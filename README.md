# firenza/verify-secrets

If you use github secrets in your workflows use this action to verify all secrets are accessible to this repository via environment, organization, or repository defined secrets.

## Usage
```yml
- name: Verify Github Secrets
  uses: firenza/verify-github-secrets@v2
  with:
    secrets: ${{ toJSON(secrets) }}
```

## Inputs
- `secrets`: (Required) JSON of built in `secrets` variable
