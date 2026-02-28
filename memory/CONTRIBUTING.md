# Security Guidelines

## Secrets Management

**Never commit secrets to this repository.**

### What counts as secrets
- API keys
- Auth tokens
- Passwords
- Client secrets
- Private keys

### How to handle secrets

1. **Use environment variables**
   ```bash
   # In ~/.bashrc or ~/.zshrc
   export MY_API_TOKEN="actual-token-here"
   ```

2. **Reference in docs as placeholders**
   ```markdown
   # Wrong
   API_TOKEN="sk-abc123..."
   
   # Correct
   API_TOKEN="<YOUR_TOKEN>"
   # or
   API_TOKEN="$MY_API_TOKEN"
   ```

3. **Local config files (gitignored)**
   ```
   tokens.json      → ignored
   .env             → ignored
   *-secrets.json   → ignored
   ```

### Pre-commit Hook

This repo has a pre-commit hook that:
- Shows staged diff before commit
- Detects potential secrets
- Asks for confirmation if secrets detected

If you see a warning, either:
1. Remove the secret and use environment variable
2. Confirm it's a false positive (e.g., placeholder text)
