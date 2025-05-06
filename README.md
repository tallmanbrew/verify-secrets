# GitHub Action: Verify Secrets

This action will verify all secrets referenced in your workflow files, checking if they appear to be available in your GitHub environment.

## Features

- Automatically detects secrets referenced with `${{ secrets.SECRET_NAME }}` syntax
- Provides best-effort verification that secrets exist in your environment
- No configuration required - just add the action to your workflow
- Supports GitHub's built-in secrets like `GITHUB_TOKEN`
- Works with repository, organization, and environment secrets

## Usage

Add this step to your workflow file:

```yaml
- uses: christallman/verify-secrets@v1
```

## How It Works

The action:
1. Analyzes the current workflow file to find all secret references
2. Uses heuristics to determine which secrets might be available in your GitHub environment
3. Reports any secrets that are referenced but might be missing
4. Provides clear guidance on how to add missing secrets

## Limitations

Due to GitHub's security model:

- Standard GitHub tokens cannot list secrets via the API (by design)
- The action uses environment-based heuristics to guess which secrets are available
- False positives may occur (warning about secrets that actually exist)
- False negatives are possible (not warning about truly missing secrets)

These limitations are fundamental to GitHub's security architecture, which intentionally restricts access to information about available secrets.

## Example

```yaml
name: Example Workflow

on:
  push:
    branches: [ main ]

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
- Only reports on the potential existence (or lack thereof) of secrets
- Uses best-effort methods to check if secrets might be available
- Requires minimal permissions to function

## License

MIT