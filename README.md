# tallmanbrew/verify-secrets

If you use github secrets in your workflows use this action to verify all secrets are defined at either org or repo level.

## Prerequisites
- This action requires a personal access token with admin rights to repo
- For Org level secrets personal access token must have org level admin rights

## Usage
```yml
- name: Verify Secrets
  uses: tallmanbrew/verify-secrets@v1
    with:
      access-token: ${{ secrets.PAT }}
      repo: ${{ github.repository }}
      owner: ${{ github.repository_owner }}
      shell: bash
```

## Inputs
- `access-token`: (Required) Personal Access Token with repo admin rights, if under an org PAT requires Org admin rights

- `repo`: (Required) Set to repository name 
  ```text
  ${{ github.repository }}
  ```
- `owner`: (Optional) Only used if repo under org
  ```text
  ${{ github.repository_owner }}
  ```
- `shell`: (Optional) Set to bash by default, use cmd to set for windows runners
  ```text
  bash
  ```