# Chaptrix Automation Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Chaptrix automated workflow.

## GitHub Actions Workflow Issues

### Workflow Not Running

**Symptoms:**
- No workflow runs visible in the Actions tab
- Scheduled workflows not triggering

**Possible Solutions:**
1. **Check workflow file syntax**: Ensure the `.github/workflows/unified-workflow.yml` file has valid YAML syntax
2. **Verify schedule**: GitHub Actions schedules use UTC time; adjust your cron expression accordingly
3. **Repository activity**: GitHub may disable scheduled workflows in repositories with no recent activity; perform a manual push or run the workflow manually
4. **Workflow permissions**: Ensure the workflow has appropriate permissions in repository settings

### Workflow Failing

**Symptoms:**
- Red X in the Actions tab
- Error messages in workflow logs

**Common Errors and Solutions:**

1. **Python dependency errors**
   - Error: `ModuleNotFoundError: No module named 'X'`
   - Solution: Add the missing package to `requirements.txt`

2. **File not found errors**
   - Error: `FileNotFoundError: [Errno 2] No such file or directory: 'X'`
   - Solution: Check file paths in your code; use relative paths and ensure all necessary files are committed to the repository

3. **Permission denied errors**
   - Error: `PermissionError: [Errno 13] Permission denied: 'X'`
   - Solution: Ensure the workflow has appropriate permissions to access files and directories

4. **Timeout errors**
   - Error: `The job running on runner-X has exceeded the maximum execution time of 360 minutes.`
   - Solution: Optimize your code or split the workflow into smaller jobs

## Google Drive Integration Issues

### Authentication Failures

**Symptoms:**
- Errors mentioning "credentials", "authentication", or "unauthorized"
- Files not uploading to Google Drive

**Possible Solutions:**
1. **Check service account key**: Verify the `GOOGLE_CREDENTIALS` secret contains the complete, valid JSON key
2. **API enabled**: Ensure the Google Drive API is enabled for your Google Cloud project
3. **Scope configuration**: Verify the code is using the correct API scopes

### Permission Issues

**Symptoms:**
- Error messages containing "permission denied" or "insufficient permissions"
- Files not appearing in the expected Drive folder

**Possible Solutions:**
1. **Folder sharing**: Ensure your Google Drive folder is shared with the service account email
2. **Permission level**: The service account needs "Editor" permission on the folder
3. **Folder ID**: If using a folder ID in your code, verify it's correct

## Discord Notification Issues

**Note: Discord integration is completely optional.** Chaptrix will work without Discord credentials, but you won't receive notifications about new chapters.

### Missing Notifications

**Symptoms:**
- No messages appearing in Discord
- No errors in the workflow logs

**Possible Solutions:**
1. **Integration disabled**: Check if `upload_to_discord` is set to `false` in `settings.json`
2. **Webhook URL**: Verify the `DISCORD_WEBHOOK_URL` secret is correct
3. **Bot token**: If using a bot, check the `DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID` secrets
4. **Rate limiting**: Discord may rate-limit frequent messages; add delays between notifications
5. **Message content**: Ensure the message content complies with Discord's requirements

### File Attachment Issues

**Symptoms:**
- Messages sent without file attachments
- Errors about file size or format

**Possible Solutions:**
1. **File size**: Discord has an 8MB limit for webhook attachments (25MB for premium servers)
2. **File format**: Ensure the file format is supported by Discord
3. **File path**: Verify the file exists at the specified path

## Image Processing Issues

### Image Stitching Failures

**Symptoms:**
- Errors in image processing steps
- Missing or corrupted output images

**Possible Solutions:**
1. **Dependencies**: Ensure all image processing dependencies are installed correctly
2. **Input validation**: Add more robust error handling for invalid input images
3. **Memory issues**: Large images may cause memory problems; consider processing in smaller batches

## Debugging Techniques

### Enhanced Logging

To add more detailed logging to your workflow:

1. Modify your Python code to include more logging statements
2. Set the log level to DEBUG in your code
3. Add this to your workflow file to see more detailed output:

```yaml
- name: Run unified workflow with debug logging
  run: python unified_workflow.py --debug
  env:
    PYTHONUNBUFFERED: 1
```

### Testing Locally

Before relying on the automated workflow:

1. Test your code locally with the same environment variables
2. Use a service account key file for local testing
3. Verify all components work correctly before pushing changes

### Workflow Artifacts

To save output files for inspection:

```yaml
- name: Upload debug artifacts
  uses: actions/upload-artifact@v2
  if: always()
  with:
    name: debug-logs
    path: |  
      logs/
      *.log
```

## Getting Help

If you're still experiencing issues:

1. Check the GitHub Actions documentation: https://docs.github.com/en/actions
2. Review the Google Drive API documentation: https://developers.google.com/drive/api/v3/about-sdk
3. Search for similar issues in the Discord.py or Google API Python client repositories
4. Include detailed logs and error messages when seeking help