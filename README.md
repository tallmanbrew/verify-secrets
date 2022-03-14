# firenza/verify-secrets

If you use github secrets in your workflows use this action to verify all secrets are accessible to this repository via environment, organization, or repository defined secrets.

## Usage

Sending in all the secret information

```yml
# Need to get repo files to parse workflows for secrets
- uses: actions/checkout@v2

- name: Verify Github Secrets
  uses: firenza/verify-secrets@v2
  with:
    secrets: ${{ toJSON(secrets) }}
    exclusions: IGNORE_ME, IGNORE_ME_TOO
```

Sending in just the secret names

```yml
# Need to get repo files to parse workflows for secrets
- uses: actions/checkout@v2

- name: Get secret JSON keys
  id: secret_json_keys
  run: echo ::set-output name=json_keys::$(echo '${{ toJSON(secrets) }}' | jq -c 'keys')

- name: Verify Github Secrets
  uses: firenza/verify-secrets@v2
  with:
    secret_names: ${{ steps.secret_json_keys.outputs.json_keys }}
```

## Inputs
  Either `secrets` or `secret_names` is required

- `secrets`: JSON of built in `secrets` variable
- `secret_names`: JSON of secret names from built in `secrets` variable
- `exclusions`: A comma separated string of secret names to exclude from verification
