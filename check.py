import os
import re
import requests

TOKEN = os.getenv('TOKEN')
OWNER = os.getenv('OWNER')
REPO = os.getenv('REPO')
DIRECTORY = '.github/workflows'

headers = {'Authorization': f'token {TOKEN}'}

print(f'Reading repository')
repo_url = f'https://api.github.com/repos/{REPO}'
repo_response = requests.get(repo_url, headers=headers)
repo_response.raise_for_status()

repo_json = repo_response.json()

repo_is_private = repo_json['private']

print(f'Reading org secrets')
org_secrets_url = f'https://api.github.com/orgs/{OWNER}/actions/secrets?per_page=100'
org_secrets_response = requests.get(org_secrets_url, headers=headers)
org_secrets_response.raise_for_status()

print(f'Reading repository secrets')
repo_secrets_url = f'https://api.github.com/repos/{REPO}/actions/secrets?per_page=100'
repo_secrets_response = requests.get(repo_secrets_url, headers=headers)
repo_secrets_response.raise_for_status() 

print(f'Reading environments')
environments_url = f'https://api.github.com/repos/{REPO}/environments'
environments_response = requests.get(environments_url, headers=headers)
environments_response.raise_for_status()

secrets_tied_to_repo = []

# Read in the secrets for each environment
environments_response_json = environments_response.json()

for environment in environments_response_json['environments']:
    environment_name = environment['name']

    environment_secrets_url = f'https://api.github.com/repos/{REPO}/environments/{environment_name}/secrets'
    print(f'Reading environment secrets for environment {environment_name}')
    environment_secrets = requests.get(environment_secrets_url, headers=headers)
    environment_secrets.raise_for_status()

    environment_secrets_json = environment_secrets.json()

    for secret in environment_secrets_json['secrets']:
        secrets_tied_to_repo.append(secret['name'])

# See which org secrets are assigned to this repository
org_secrets_response_json = org_secrets_response.json()

for org_secret in org_secrets_response_json['secrets']:
    org_secret_name = org_secret['name']

    if org_secret['visibility'] == 'all' or org_secret['visibility'] == 'private' and repo_is_private:
        secrets_tied_to_repo.append(org_secret_name)
    elif org_secret['visibility'] == 'selected':
        # NOTE: This if an org secret is selectively assigned to > 100 repos this will
        # not cover that scenario
        org_secret_repositories_url = f'https://api.github.com/orgs/{OWNER}/actions/secrets/{org_secret_name}/repositories?per_page=100'
        print(f'Reading repositories that are associated with org secret {org_secret_name}')
        org_secret_repositories_response = requests.get(org_secret_repositories_url, headers=headers)
        org_secret_repositories_response.raise_for_status()

        org_secret_repositories_json = org_secret_repositories_response.json()

        for repository in org_secret_repositories_json['repositories']:
            if repository['name'] == REPO:
                secrets_tied_to_repo.append(org_secret_name)

repo_secrets_response_json = repo_secrets_response.json()

if 'secrets' in repo_secrets_response_json:
    for secret in repo_secrets_response_json['secrets']:
        secrets_tied_to_repo.append(secret['name'])

missing_secrets = []

for filename in os.listdir(DIRECTORY):
    if filename.endswith(".yaml") or filename.endswith(".yml"):
         with open(os.path.join(DIRECTORY, filename), 'r') as f:
             for line in f:
                 res = re.search(r"\{\{(.*?)\}", line)
                 if (res and res.group(1) and 'secrets.' in res.group(1) and 'GITHUB_TOKEN' not in res.group(1)):
                    if (res.group(1).split(".")[1].strip() not in secrets_tied_to_repo):
                        missing_secret_name = res.group(1).split(".")[1].strip()
                        missing_secrets.append(missing_secret_name)
    else:
        continue

# Remove duplicates and sort
missing_secrets = sorted(set(missing_secrets))

if len(missing_secrets) > 0:
    print('\n\nThe following workflow referenced secrets are not yet associated with this repository\n')
    for missing_secret in missing_secrets:
        print(missing_secret)
    exit(1)