import os
import re
import sys
import json
import yaml
import requests
import glob
from pathlib import Path

def extract_secrets_from_workflow(file_path):
    """Extract all secrets referenced in a workflow file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find all references to secrets using regex
        secret_pattern = r'\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}'
        referenced_secrets = re.findall(secret_pattern, content)
        return set(referenced_secrets)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return set()

def check_secret_availability(secret_name):
    """
    Check if a secret with the given name is available in the GitHub Actions environment.
    
    In GitHub Actions, we can detect built-in secrets directly.
    For user-defined secrets, GitHub doesn't provide a direct way to list them all,
    but we can make intelligent guesses based on environment variable patterns.
    """
    # Known GitHub built-in secrets
    if secret_name in ['GITHUB_TOKEN']:
        return True
    
    # For user-defined secrets, GitHub creates masked environment variables
    # We can only detect their presence indirectly
    
    # Method 1: Check against all environment variables
    # Secret usage often exposes environment variables that might indicate availability
    for env_var in os.environ:
        if env_var == secret_name or env_var == f"INPUT_{secret_name}":
            return True

    # We can't definitively know if a secret exists if it hasn't been used
    # So we'll return False but note this is a best-effort check
    return False

def get_current_workflow_path():
    """Extract the current workflow file path from GitHub context and environment variables."""
    try:
        # Method 1: Try getting from GITHUB_WORKFLOW and GITHUB_WORKSPACE
        github_workflow = os.environ.get('GITHUB_WORKFLOW')
        github_workspace = os.environ.get('GITHUB_WORKSPACE', os.getcwd())
        
        if github_workflow:
            # Try common extensions
            for ext in ['yml', 'yaml']:
                workflow_path = os.path.join(github_workspace, '.github', 'workflows', f"{github_workflow}.{ext}")
                if os.path.exists(workflow_path):
                    return workflow_path
                    
            # Try looking for files containing the workflow name
            workflow_files = glob.glob(os.path.join(github_workspace, '.github', 'workflows', '*.y*ml'))
            for wf in workflow_files:
                try:
                    with open(wf, 'r') as f:
                        content = yaml.safe_load(f)
                        if content and 'name' in content and content['name'] == github_workflow:
                            return wf
                except:
                    continue
        
        # Method 2: Try from github context
        github_context = json.loads(os.environ.get('GITHUB_CONTEXT', '{}'))
        workflow_ref = github_context.get('workflow_ref', '')
        if workflow_ref:
            parts = workflow_ref.split('/')
            if len(parts) >= 3:
                workflow_file = parts[-1].split('@')[0]  # Remove ref part
                return os.path.join(github_workspace, '.github', 'workflows', workflow_file)
        
        # Method 3: Use GITHUB_EVENT_PATH to extract workflow information
        event_path = os.environ.get('GITHUB_EVENT_PATH')
        if event_path and os.path.exists(event_path):
            try:
                with open(event_path, 'r') as f:
                    event_data = json.load(f)
                    workflow_path = event_data.get('workflow', '')
                    if workflow_path:
                        return os.path.join(github_workspace, '.github', 'workflows', os.path.basename(workflow_path))
            except:
                pass
        
        return None
    except Exception as e:
        print(f"Error extracting workflow path: {e}")
        return None

def get_repo_info_from_github_context():
    """Extract repository owner and name from GitHub context or environment variables."""
    try:
        # First try from environment variables
        github_repository = os.environ.get('GITHUB_REPOSITORY')
        if github_repository and '/' in github_repository:
            return github_repository.split('/')
        
        # Then try from GitHub context
        github_context = json.loads(os.environ.get('GITHUB_CONTEXT', '{}'))
        repository = github_context.get('repository', '')
        if repository and '/' in repository:
            return repository.split('/')
            
        return None, None
    except Exception as e:
        print(f"Error extracting repository info: {e}")
        return None, None

def get_available_secrets_via_api(token=None):
    """
    Use GitHub API to get available secrets (just names, not values).
    Requires a GitHub token with appropriate permissions.
    """
    available_secrets = set(['GITHUB_TOKEN'])  # Built-in token always available
    
    if not token:
        print("No GitHub token provided for API access or token lacks required permissions.")
        print("Will rely on environment variable detection for secrets.")
        return available_secrets
    
    owner, repo = get_repo_info_from_github_context()
    if not owner or not repo:
        print("Could not determine repository owner/name. Skipping API-based secret verification.")
        return available_secrets
    
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}'
    }
    
    # Check repository secrets
    try:
        repo_secrets_url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets"
        response = requests.get(repo_secrets_url, headers=headers)
        if response.status_code == 200:
            secrets_data = response.json()
            for secret in secrets_data.get('secrets', []):
                available_secrets.add(secret['name'])
            print(f"✓ Successfully retrieved repository secrets")
        elif response.status_code == 403:
            print(f"❌ Permission denied when accessing repository secrets. Check token permissions.")
        else:
            print(f"❌ Failed to get repository secrets: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error fetching repository secrets: {e}")
    
    # Check organization secrets (if applicable)
    try:
        org_secrets_url = f"https://api.github.com/orgs/{owner}/actions/secrets"
        response = requests.get(org_secrets_url, headers=headers)
        if response.status_code == 200:
            secrets_data = response.json()
            for secret in secrets_data.get('secrets', []):
                available_secrets.add(secret['name'])
        elif response.status_code != 404:  # 404 is expected if not an org
            print(f"Failed to get organization secrets: {response.status_code}")
    except Exception as e:
        print(f"Error fetching organization secrets: {e}")
        
    # Check environment secrets
    try:
        # Get current environment name from GitHub context or environment variables
        environment = os.environ.get('GITHUB_ENVIRONMENT')
        
        # If the environment variable isn't set directly, try to extract from context
        if not environment:
            github_context = json.loads(os.environ.get('GITHUB_CONTEXT', '{}'))
            environment = github_context.get('event', {}).get('deployment', {}).get('environment')
        
        # If still not found, check if GITHUB_ENV is set (this is likely NOT the environment name)
        # This appears to be an error in your current implementation
        if not environment:
            # Don't use GITHUB_ENV, it's not the environment name
            pass
            
        if environment:
            print(f"Checking secrets for environment: {environment}")
            env_secrets_url = f"https://api.github.com/repos/{owner}/{repo}/environments/{environment}/secrets"
            response = requests.get(env_secrets_url, headers=headers)
            if response.status_code == 200:
                secrets_data = response.json()
                for secret in secrets_data.get('secrets', []):
                    available_secrets.add(secret['name'])
                print(f"✓ Successfully retrieved environment secrets for '{environment}'")
            elif response.status_code == 404:
                print(f"❌ Environment '{environment}' not found")
            else:
                print(f"❌ Failed to get environment secrets: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error fetching environment secrets: {e}")
    
    return available_secrets

def extract_environment_from_workflow(file_path):
    """Extract environment name from workflow file if specified."""
    try:
        with open(file_path, 'r') as f:
            workflow = yaml.safe_load(f)
            
        # Look for environment definitions in jobs
        environments = set()
        if 'jobs' in workflow:
            for job_name, job_data in workflow['jobs'].items():
                if 'environment' in job_data:
                    # Environment can be a string or object with 'name' property
                    env = job_data['environment']
                    if isinstance(env, str):
                        environments.add(env)
                    elif isinstance(env, dict) and 'name' in env:
                        environments.add(env['name'])
        
        return environments
    except Exception as e:
        print(f"Error extracting environment from workflow: {e}")
        return set()

def extract_secrets_from_all_workflows(workflow_dir=None):
    """Find all workflow files and extract referenced secrets from them."""
    if not workflow_dir:
        workspace = os.environ.get('GITHUB_WORKSPACE', os.getcwd())
        workflow_dir = os.path.join(workspace, '.github', 'workflows')
    
    if not os.path.exists(workflow_dir):
        print(f"Workflow directory not found: {workflow_dir}")
        return set()
    
    all_secrets = set()
    workflow_files = glob.glob(os.path.join(workflow_dir, '*.yml')) + glob.glob(os.path.join(workflow_dir, '*.yaml'))
    
    for file_path in workflow_files:
        file_secrets = extract_secrets_from_workflow(file_path)
        all_secrets.update(file_secrets)
        print(f"Processed {os.path.basename(file_path)}: Found {len(file_secrets)} secret(s)")
    
    return all_secrets

def fallback_secret_detection():
    """Use environment-based heuristics to detect available secrets."""
    available_secrets = set(['GITHUB_TOKEN'])  # Built-in token always available
    
    # Check environment variables that might indicate secrets
    for env_var in os.environ:
        # Check for common patterns of secret environment variables
        if any(marker in env_var for marker in ['TOKEN', 'SECRET', 'PASSWORD', 'KEY', 'AUTH']):
            available_secrets.add(env_var)
        
        # Check for GitHub's secret mapping format
        if env_var.startswith('SECRET_'):
            available_secrets.add(env_var[7:])
    
    return available_secrets

def main():
    # Get current workflow file
    current_workflow = get_current_workflow_path()
    
    if not current_workflow or not os.path.exists(current_workflow):
        print("Could not find current workflow file.")
        print("Attempting to scan all workflow files...")
        
        # Fall back to checking all workflow files
        workspace = os.environ.get('GITHUB_WORKSPACE', os.getcwd())
        workflow_dir = os.path.join(workspace, '.github', 'workflows')
        
        if not os.path.isdir(workflow_dir):
            print(f"❌ ERROR: Workflow directory not found at {workflow_dir}")
            sys.exit(1)
            
        referenced_secrets = extract_secrets_from_all_workflows(workflow_dir)
        if not referenced_secrets:
            print("✅ No secrets referenced in any workflow files.")
            return
    else:
        print(f"Analyzing workflow: {current_workflow}")
        # Extract referenced secrets from workflow
        referenced_secrets = extract_secrets_from_workflow(current_workflow)
    
    print(f"Found {len(referenced_secrets)} secret reference(s):")
    for secret in sorted(referenced_secrets):
        print(f"  - {secret}")
    
    if not referenced_secrets:
        print("✅ No secrets referenced, nothing to verify!")
        return
    
    # Extract environment names from workflow if present
    environments = set()
    if current_workflow and os.path.exists(current_workflow):
        environments = extract_environment_from_workflow(current_workflow)
        if environments:
            print(f"Found environments in workflow: {', '.join(environments)}")
    
    # Get GitHub token for API access
    github_token = os.environ.get('GITHUB_TOKEN', None)
    
    # Try to get available secrets using GitHub API first
    available_secrets = get_available_secrets_via_api(github_token)
    
    # If API check failed or had limited results, fall back to environment-based detection
    if len(available_secrets) <= 1:  # Only built-in token detected
        print("Falling back to environment-based secret detection...")
        available_secrets.update(fallback_secret_detection())
    
    # Check each referenced secret
    missing_secrets = []
    for secret in referenced_secrets:
        if secret not in available_secrets:
            missing_secrets.append(secret)
    
    # Report results
    if missing_secrets:
        print("\n⚠️ WARNING: The following secrets may not be available:")
        for secret in sorted(missing_secrets):
            print(f"  - {secret}")
        
        print("\nConsider adding these secrets to your GitHub repository or organization.")
        print("\nNote: For more accurate results, ensure your workflow has proper permissions:")
        print("""
permissions:
  contents: read
  id-token: write  # For accessing repository and organization secrets
""")
        sys.exit(1)
    else:
        print("\n✅ All referenced secrets appear to be available!")

if __name__ == "__main__":
    main()