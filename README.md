# GitHub Action: Verify Secrets

This action will verify all secrets used in your workflow files are defined as GitHub secrets.

## Features

- Automatically detects secrets referenced with `${{ secrets.SECRET_NAME }}` syntax
- Verifies secrets exist at repository, organization, and environment level
- No configuration required - just add the action to your workflow
- Supports GitHub's built-in secrets like `GITHUB_TOKEN`
- Detects environment-specific secrets

## Usage

Add this step to your workflow file:

```yaml
- uses: christallman/verify-secrets@v1
```

For best results, add the following permissions to your workflow:

```yaml
permissions:
  contents: read
  id-token: write  # Needed for accessing repository, organization and environment secrets
```

## How It Works

The action:
1. Analyzes the current workflow file to find all secret references
2. Checks which secrets are available in your GitHub environment 
3. Reports any secrets that are referenced but not defined
4. Provides clear instructions on how to fix missing secrets

## Example

```yaml
name: Example Workflow

on:
  push:
    branches: [ main ]

permissions:
  contents: read
  id-token: write  # Needed for secret verification

jobs:
  verify-secrets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      # Add this step to verify all secrets are available
      - uses: christallman/verify-secrets@v1
      
      # Your other steps that use secrets
      - name: Use secrets
        run: echo "Using secrets in workflow"
        env:
          API_KEY: ${{ secrets.API_KEY }}
```

## Security

This action:
- Never exposes secret values
- Only reports on the existence (or lack thereof) of secrets
- Uses GitHub's API to check if secrets exist, not their values
- Requires minimal permissions to function

## License

MIT