# GitHub Push Instructions

## Setting Up Authentication

To push changes to the GitHub repository, you need to set up authentication using a Personal Access Token (PAT).

### Step 1: Generate a Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Generate new token
   - You can go directly to: https://github.com/settings/tokens/new
2. Give your token a descriptive name (e.g., "Chaptrix Push Access")
3. Set an expiration date (or choose "No expiration" if appropriate)
4. Select the necessary scopes:
   - At minimum, select the `repo` scope for full control of private repositories
5. Click "Generate token"
6. **IMPORTANT**: Copy the generated token immediately. GitHub will only show it once!

### Step 2: Set Up the Token

#### Option A: Set as Environment Variable (Recommended)

Set the token as an environment variable to avoid entering it each time:

1. Open Command Prompt as Administrator
2. Run the following command (replace `your_token_here` with your actual token):

```
setx GITHUB_TOKEN "your_token_here"
```

3. Close and reopen any command prompts for the change to take effect

#### Option B: Enter Token When Prompted

Alternatively, you can enter the token each time you run the push scripts when prompted.

## Using the Push Scripts

### Basic Push Script

To push changes with a default commit message:

1. Run `push_to_github.bat`
2. If you haven't set the `GITHUB_TOKEN` environment variable, enter your token when prompted

### Custom Commit Message Script

To push changes with a custom commit message:

1. Run `push_to_github_custom.bat`
2. Enter your custom commit message when prompted
3. If you haven't set the `GITHUB_TOKEN` environment variable, enter your token when prompted

Alternatively, provide the commit message as a parameter:

```
push_to_github_custom.bat "Your commit message here"
```

## Security Notes

- **Never commit your token to the repository**
- Treat your token like a password
- If you suspect your token has been compromised, revoke it immediately on GitHub and generate a new one
- Consider setting an expiration date on your token for better security

## Troubleshooting

### Permission Denied Errors

If you see "Permission denied" errors:

1. Verify your token has the correct scopes (at minimum, the `repo` scope)
2. Check that you're using the correct token
3. Ensure your GitHub account has write access to the repository

### Invalid Username/Password Errors

If you see authentication errors:

1. Your token may have expired - generate a new one
2. The token may have been entered incorrectly
3. The token may have been revoked - check your GitHub token settings