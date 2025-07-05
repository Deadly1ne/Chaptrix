# Google Drive Service Account Setup Guide

This guide provides detailed instructions for setting up a Google Drive service account for Chaptrix automation.

## What is a Service Account?

A service account is a special type of Google account intended for non-human users that need to authenticate and be authorized to access data in Google APIs. For Chaptrix automation, we use a service account to upload files to Google Drive without requiring user interaction.

## Step-by-Step Setup Instructions

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "Chaptrix Automation")
5. Click "Create"

### 2. Enable the Google Drive API

1. Select your new project from the project dropdown
2. Go to "APIs & Services" > "Library"
3. Search for "Google Drive API"
4. Click on "Google Drive API"
5. Click "Enable"

### 3. Create a Service Account

1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Enter a service account name (e.g., "Chaptrix Service")
4. (Optional) Enter a description
5. Click "Create and Continue"
6. For the "Grant this service account access to project" step:
   - Select "Editor" role
   - Click "Continue"
7. For the "Grant users access to this service account" step:
   - You can skip this step
   - Click "Done"

### 4. Create a Service Account Key

1. From the Service Accounts list, click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" as the key type
5. Click "Create"
6. The key file will be automatically downloaded to your computer
7. Keep this file secure - it grants access to your Google Drive!

### 5. Share Your Google Drive Folder

1. Note the service account email address (it looks like `something@project-id.iam.gserviceaccount.com`)
2. Go to your Google Drive
3. Create a folder for Chaptrix uploads (if you haven't already)
4. Right-click on the folder and select "Share"
5. Enter the service account email address
6. Set permission to "Editor"
7. Uncheck "Notify people"
8. Click "Share"

### 6. Configure Chaptrix to Use the Service Account

For GitHub Actions automation:

1. Open the downloaded JSON key file
2. Copy the entire contents
3. Go to your GitHub repository
4. Go to "Settings" > "Secrets and variables" > "Actions"
5. Create a new repository secret named `GOOGLE_CREDENTIALS`
6. Paste the entire JSON content as the value
7. Click "Add secret"

## Verifying the Setup

To verify that your service account is working correctly:

1. Run the GitHub Actions workflow manually
2. Check the workflow logs for any authentication errors
3. Verify that files are being uploaded to your Google Drive folder

## Troubleshooting

### Common Issues

1. **Authentication Error**: Make sure the JSON key is correctly added as a GitHub secret
2. **Permission Denied**: Ensure you've shared your Drive folder with the service account email
3. **API Not Enabled**: Verify that the Google Drive API is enabled for your project

### Service Account Limitations

- Service accounts cannot access files in "My Drive" unless those files are explicitly shared with the service account
- Service accounts have their own Drive storage, separate from your personal Drive
- The free tier of Google Cloud provides sufficient resources for Chaptrix automation

## Security Considerations

- The service account key grants access to your Google Drive. Keep it secure.
- Only share the minimum necessary permissions with the service account.
- Consider setting up a dedicated Google Cloud project for this purpose.
- Regularly review the service account's activity in the Google Cloud Console.