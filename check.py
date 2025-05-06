import os
import re
import sys
import json
import yaml
import requests
import glob
import subprocess
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
    Note: Most GitHub tokens don't have permissions to list secrets.
    This function will likely fail but we try anyway in case the token has elevated permissions.
    """
    available_secrets = set(['GITHUB_TOKEN'])  # Built-in token always available
    
    if not token:
        print("No GitHub token provided for API access.")
        return available_secrets
    
    owner, repo = get_repo_info_from_github_context()
    if not owner or not repo:
        print("Could not determine repository owner/name.")
        return available_secrets
    
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}'
    }
    
    # Try to get repository secrets (likely to fail due to permissions)
    try:
        repo_secrets_url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets"
        response = requests.get(repo_secrets_url, headers=headers)
        if response.status_code == 200:
            secrets_data = response.json()
            for secret in secrets_data.get('secrets', []):
                available_secrets.add(secret['name'])
            print(f"✓ Successfully retrieved repository secrets")
        elif response.status_code == 403:
            # This is expected - most tokens don't have permission to list secrets
            print(f"ℹ️ Standard GitHub token doesn't have permission to list secrets (HTTP 403)")
        else:
            print(f"❌ Failed to get repository secrets: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error fetching repository secrets: {e}")
    
    # The API calls for org and environment secrets will likely fail too
    # Skipping those attempts to reduce noise in the logs
    
    return available_secrets

def get_available_secrets_via_github_cli():
    """
    Use GitHub CLI to get available secrets (just names, not values).
    GitHub CLI may have different permissions than the API when using default tokens.
    """
    available_secrets = set(['GITHUB_TOKEN'])  # Built-in token always available
    
    # Check if GitHub CLI is installed
    try:
        subprocess.run(['gh', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("GitHub CLI (gh) not found. Cannot use CLI to list secrets.")
        return available_secrets
    
    owner, repo = get_repo_info_from_github_context()
    if not owner or not repo:
        print("Could not determine repository owner/name.")
        return available_secrets
        
    repo_full_name = f"{owner}/{repo}"
    
    # Try to get repository secrets
    try:
        result = subprocess.run(
            ['gh', 'secret', 'list', '-R', repo_full_name], 
            check=False,  # Don't raise exception on non-zero exit
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check if command succeeded
        if result.returncode == 0:
            # Parse output - format is: NAME UPDATED_AT
            for line in result.stdout.strip().split('\n'):
                if line and not line.startswith('NAME'):  # Skip header
                    secret_name = line.split()[0].strip()
                    available_secrets.add(secret_name)
            print(f"✓ Successfully retrieved repository secrets via GitHub CLI")
        else:
            print(f"ℹ️ GitHub CLI couldn't list repository secrets: {result.stderr.strip()}")
    except Exception as e:
        print(f"Error using GitHub CLI to fetch repository secrets: {e}")
    
    # Try to get organization secrets
    try:
        result = subprocess.run(
            ['gh', 'secret', 'list', '-o', owner], 
            check=False,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line and not line.startswith('NAME'):
                    secret_name = line.split()[0].strip()
                    available_secrets.add(secret_name)
            print(f"✓ Successfully retrieved organization secrets via GitHub CLI")
        else:
            # This might fail if not an org or no permission - that's expected
            pass
    except Exception as e:
        # Ignore errors for org secrets - might not be applicable
        pass
            
    # Try to get environment secrets if environments were found
    for env_name in extract_environment_names():
        try:
            result = subprocess.run(
                ['gh', 'secret', 'list', '-R', repo_full_name, '-e', env_name], 
                check=False,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line and not line.startswith('NAME'):
                        secret_name = line.split()[0].strip()
                        available_secrets.add(secret_name)
                print(f"✓ Successfully retrieved secrets for environment '{env_name}' via GitHub CLI")
        except Exception:
            # Ignore errors for specific environments
            pass
    
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

def extract_environment_names():
    """Extract all environment names from workflows."""
    environments = set()
    
    # Get current workflow path
    current_workflow = get_current_workflow_path()
    if current_workflow and os.path.exists(current_workflow):
        environments.update(extract_environment_from_workflow(current_workflow))
    
    # Also check all workflows to be thorough
    workspace = os.environ.get('GITHUB_WORKSPACE', os.getcwd())
    workflow_dir = os.path.join(workspace, '.github', 'workflows')
    if os.path.isdir(workflow_dir):
        workflow_files = glob.glob(os.path.join(workflow_dir, '*.yml')) + \
                         glob.glob(os.path.join(workflow_dir, '*.yaml'))
        for wf in workflow_files:
            environments.update(extract_environment_from_workflow(wf))
    
    return environments

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
    
    # First try GitHub CLI which might have different permissions
    print("Attempting to verify secrets using GitHub CLI...")
    available_secrets = get_available_secrets_via_github_cli()
    
    # If GitHub CLI failed or found limited results, try the API approach
    if len(available_secrets) <= 1:  # Only built-in token detected
        print("Attempting to verify secrets via API (note: standard GitHub token can't list secrets)")
        available_secrets.update(get_available_secrets_via_api(github_token))
    
    # Since both approaches may fail, always use environment-based detection
    print("Using environment-based secret detection...")
    available_secrets.update(fallback_secret_detection())
    
    # For standard workflows, assume common GitHub secrets are available
    available_secrets.update([
        'GITHUB_TOKEN',
        'ACTIONS_RUNTIME_TOKEN',
        'ACTIONS_ID_TOKEN_REQUEST_TOKEN'
    ])
    
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
        
        print("\nPlease verify these secrets exist in your repository, organization, or environment settings.")
        print("\nNOTE: GitHub Actions doesn't allow listing secrets via API with standard tokens.")
        print("This check uses heuristics and may produce false positives.")
        sys.exit(1)
    else:
        print("\n✅ All referenced secrets appear to be available!")
        print("NOTE: GitHub Actions doesn't allow listing secrets via API with standard tokens.")
        print("This check uses heuristics and may not catch all missing secrets.")

if __name__ == "__main__":
    main()