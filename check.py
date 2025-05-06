import os
import re
import sys
import json
import yaml
import requests
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
    """Extract the current workflow file path from GitHub context."""
    try:
        github_context = json.loads(os.environ.get('GITHUB_CONTEXT', '{}'))
        
        # Get repository workspace path
        workspace = os.environ.get('GITHUB_WORKSPACE', os.getcwd())
        
        # Get workflow info from context
        workflow_ref = github_context.get('workflow_ref', '')
        if not workflow_ref:
            print("Could not determine current workflow from GitHub context")
            return None
            
        # Extract workflow file path from reference
        # Format is typically: {owner}/{repo}/.github/workflows/{filename}@{ref}
        parts = workflow_ref.split('/')
        if len(parts) >= 3:
            workflow_file = parts[-1].split('@')[0]  # Remove ref part
            return os.path.join(workspace, '.github', 'workflows', workflow_file)
        
        return None
    except Exception as e:
        print(f"Error extracting workflow path: {e}")
        return None

def get_repo_info_from_github_context():
    """Extract repository owner and name from GitHub context."""
    try:
        github_context = json.loads(os.environ.get('GITHUB_CONTEXT', '{}'))
        repository = github_context.get('repository', '')
        if repository:
            owner, repo = repository.split('/')
            return owner, repo
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
        print("No GitHub token provided for API access. Skipping API-based secret verification.")
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
        else:
            print(f"Failed to get repository secrets: {response.status_code}")
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
        # Get current environment name from GitHub context
        github_context = json.loads(os.environ.get('GITHUB_CONTEXT', '{}'))
        environment = os.environ.get('GITHUB_ENV') or github_context.get('event', {}).get('deployment', {}).get('environment')
        
        if environment:
            print(f"Checking secrets for environment: {environment}")
            env_secrets_url = f"https://api.github.com/repos/{owner}/{repo}/environments/{environment}/secrets"
            response = requests.get(env_secrets_url, headers=headers)
            if response.status_code == 200:
                secrets_data = response.json()
                for secret in secrets_data.get('secrets', []):
                    available_secrets.add(secret['name'])
            else:
                print(f"Failed to get environment secrets: {response.status_code}")
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

def main():
    # Get current workflow file
    current_workflow = get_current_workflow_path()
    
    if not current_workflow or not os.path.exists(current_workflow):
        print("Could not find current workflow file.")
        print(f"Attempting to use local workflow file...")
        
        # Fall back to using any workflow file in .github/workflows
        workflow_files = list(Path('.github/workflows').glob('*.yml'))
        if not workflow_files:
            workflow_files = list(Path('.github/workflows').glob('*.yaml'))
        
        if not workflow_files:
            print("No workflow files found.")
            sys.exit(1)
            
        current_workflow = str(workflow_files[0])
    
    print(f"Analyzing workflow: {current_workflow}")
    
    # Extract referenced secrets from workflow
    referenced_secrets = extract_secrets_from_workflow(current_workflow)
    print(f"Found {len(referenced_secrets)} secret reference(s):")
    for secret in sorted(referenced_secrets):
        print(f"  - {secret}")
    
    # Extract environment names from workflow if present
    environments = extract_environment_from_workflow(current_workflow)
    if environments:
        print(f"Found environments in workflow: {', '.join(environments)}")
        # Set environment variables to check environment-specific secrets
        for env in environments:
            os.environ['GITHUB_ENV'] = env
    
    # Get GitHub token for API access
    github_token = os.environ.get('GITHUB_TOKEN', None)
    
    # Get available secrets using GitHub API (if token available)
    available_secrets = get_available_secrets_via_api(github_token)
    
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
        if not github_token:
            print("\nNote: For more accurate results, add permissions for 'secrets' to your workflow:")
            print("""
permissions:
  contents: read
  secrets: read  # Add this line
""")
            sys.exit(1)
    else:
        print("\n✅ All referenced secrets appear to be available!")

if __name__ == "__main__":
    main()