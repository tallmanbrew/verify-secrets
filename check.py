import os
import re
import json

SECRETS = os.getenv('SECRETS')
DIRECTORY = '.github/workflows'
NEEDS_EXIT = False

json_secrets = json.loads(SECRETS)

if not json_secrets:
    print('No secrets found defined in repo')
    exit(1)

for filename in os.listdir(DIRECTORY):
    if filename.endswith(".yaml") or filename.endswith(".yml"):
         with open(os.path.join(DIRECTORY, filename), 'r') as f:
             for line in f:
                 if line.startswith("#"):
                     continue
                 res = re.search(r"\{\{(.*?)\}", line)
                 if (res and res.group(1) and 'secrets.' in res.group(1) and 'GITHUB_TOKEN' not in res.group(1)):
                    if (res.group(1).split(".")[1].strip() not in json_secrets):
                        print(res.group(1).split(".")[1].strip())
                        NEEDS_EXIT = True
    else:
        continue

if NEEDS_EXIT:
    print('Secrets listed above not setup in GitHub secrets store!')
    exit(1)