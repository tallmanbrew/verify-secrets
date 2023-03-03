# tallmanbrew/verify-secrets

If you use github secrets in your workflows use this action to verify all secrets are defined at either org or repo level.

## Usage
```yml
- name: Verify Secrets
  uses: tallmanbrew/verify-secrets@v1
    with:
      secrets: ${{ toJSON(secrets) }}
```

## Inputs
- `secrets`: (Required) JSON of built in secrets variable