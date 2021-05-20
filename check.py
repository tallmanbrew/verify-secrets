import os
import re
import requests

TOKEN = os.getenv('TOKEN')
OWNER = os.getenv('OWNER')
REPO = os.getenv('REPO')
DIRECTORY = '.github/workflows'
NEEDS_EXIT = False

repos_url = f'https://api.github.com/repos/{REPO}/actions/secrets?per_page=100'
org_url = f'https://api.github.com/orgs/{OWNER}/actions/secrets?per_page=100'

headers = {'Authorization': f'token {TOKEN}'}

orgs = requests.get(org_url, headers=headers)
repos = requests.get(repos_url, headers=headers)

json_orgs_secrets = orgs.json()
json_repos_secrets = repos.json()

stored_secrets = []
if 'secrets' in json_orgs_secrets:
    for secret in json_orgs_secrets['secrets']:
        stored_secrets.append(secret['name'])
if 'secrets' in json_repos_secrets:
    for secret in json_repos_secrets['secrets']:
        stored_secrets.append(secret['name'])

if not stored_secrets:
    print('No secrets found defined in repo')
    exit(1)

for filename in os.listdir(DIRECTORY):
    if filename.endswith(".yaml") or filename.endswith(".yml"):
         with open(os.path.join(DIRECTORY, filename), 'r') as f:
             for line in f:
                 res = re.search(r"\{\{(.*?)\}", line)
                 if (res and res.group(1) and 'secrets.' in res.group(1)):
                    if (res.group(1).split(".")[1].strip() not in stored_secrets):
                        print(res.group(1).split(".")[1].strip())
                        NEEDS_EXIT = True
    else:
        continue

if NEEDS_EXIT:
    print('Secrets listed above not setup in GitHub secrets store!')
    exit(1)