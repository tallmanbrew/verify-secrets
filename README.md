# firenza/verify-secrets

If you use github secrets in your workflows use this action to verify all secrets are accessible to this repository via environment, organization, or repository defined secrets.

## Usage
```yml
# Need to get repo files to parse workflows for secrets
- uses: actions/checkout@v2

- name: Verify Github Secrets
  uses: firenza/verify-secrets@v2
  with:
    secrets: ${{ toJSON(secrets) }}
```

## Inputs
- `secrets`: (Required) JSON of built in `secrets` variable
