# Chaptrix Automation Guide

This guide explains how to set up Chaptrix to run automatically on GitHub Actions, eliminating the need to run it on your local PC.

## Setup Instructions

### 1. GitHub Repository Setup

If you haven't already, push your Chaptrix code to a GitHub repository:

1. Create a new GitHub repository
2. Initialize Git in your Chaptrix folder (if not already done):
   ```
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/Chaptrix.git
   git push -u origin main
   ```

### 2. Set Up Google Drive Service Account

To allow GitHub Actions to upload files to Google Drive without user interaction:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Drive API
4. Create a Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Give it a name like "Chaptrix Automation"
   - Grant it the "Editor" role
   - Click "Create"
5. Create and download a JSON key:
   - Click on the service account you just created
   - Go to the "Keys" tab
   - Click "Add Key" > "Create new key"
   - Select JSON format and click "Create"
   - Save the downloaded JSON file

6. Share your Google Drive folder with the service account email (it looks like `something@project-id.iam.gserviceaccount.com`)

### 3. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to your GitHub repository
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Add the following secrets:

   - `GOOGLE_CREDENTIALS`: The entire content of the Google service account JSON key file
   - `DISCORD_WEBHOOK_URL` (optional): Your Discord webhook URL
   - `DISCORD_BOT_TOKEN` (optional): Your Discord bot token (if using bot method)
   - `DISCORD_CHANNEL_ID` (optional): Your Discord channel ID (if using bot method)
   
   Note: Discord integration is completely optional. Chaptrix will work without Discord credentials.

### 4. Modify Your Code (if needed)

Ensure your code is compatible with headless operation:

1. Use environment variables for configuration
2. Avoid GUI dependencies
3. Make sure file paths are relative
4. Handle authentication properly for headless operation

### 5. Workflow Schedule

The default workflow runs every 4 hours. To change this:

1. Edit the `.github/workflows/unified-workflow.yml` file
2. Modify the `cron` expression in the `schedule` section

Cron syntax: `minute hour day-of-month month day-of-week`

Examples:
- `0 */4 * * *`: Every 4 hours
- `0 0,12 * * *`: Twice a day (midnight and noon)
- `0 8 * * *`: Once a day at 8 AM

## Troubleshooting

### Checking Workflow Runs

1. Go to your GitHub repository
2. Click on the "Actions" tab
3. You'll see all workflow runs, including any errors

### Common Issues

1. **Authentication Errors**: Check your Google credentials and Discord tokens
2. **Permission Issues**: Ensure the service account has access to your Drive folder
3. **Dependency Problems**: Make sure all required packages are in `requirements.txt`
4. **File Path Errors**: Use relative paths in your code

### Logs

To view detailed logs:

1. Click on a specific workflow run
2. Click on the job name
3. Expand the step that failed to see the logs

## Manual Triggering

You can manually trigger the workflow:

1. Go to your GitHub repository
2. Click on the "Actions" tab
3. Select "Chaptrix Unified Workflow"
4. Click "Run workflow"

## Additional Notes

- GitHub Actions provides 2,000 free minutes per month for private repositories
- The workflow will automatically commit changes to `comics.json` after each run
- For large files, consider using GitHub LFS or alternative storage solutions