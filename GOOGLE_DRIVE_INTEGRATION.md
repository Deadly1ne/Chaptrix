# Google Drive Integration Guide

## Overview

This document provides guidance on properly setting up and handling Google Drive integration in the Chaptrix application. It addresses the common error of `credentials.json` not being found and provides best practices for a more robust implementation.

## Current Issues

The application currently shows errors related to Google Drive integration:

```
Error: 'credentials.json' not found. Please download it from Google Cloud Console.
```

This occurs because:

1. The `credentials.json` file is excluded from version control (as it should be for security reasons)
2. The application doesn't gracefully handle its absence
3. The error handling doesn't clearly communicate to users how to resolve the issue

## Immediate Solutions

### Option 1: Create the Required Credentials File

Follow these steps to set up Google Drive integration:

1. Follow the instructions in `SERVICE_ACCOUNT_SETUP.md` to create a Google Cloud project and obtain credentials
2. Save the downloaded JSON key file as `credentials.json` in the root directory of the project
3. Make sure the file is listed in `.gitignore` to prevent accidental commits

### Option 2: Disable Google Drive Integration

If you don't need Google Drive integration, you can disable it in the settings:

1. Open `settings.json`
2. Set `"upload_to_drive": false`
3. Save the file

## Code Improvements

### 1. Make Google Drive Integration Truly Optional

Update the `get_drive_service()` function in `main.py` to handle missing credentials gracefully:

```python
def get_drive_service():
    """Get authenticated Google Drive service with improved error handling"""
    # Check if Google Drive integration is enabled in settings
    settings = load_settings()
    if not settings.get("upload_to_drive", True):
        logger.info("Google Drive integration is disabled in settings.")
        return None
        
    # Early check for credentials file
    if not os.path.exists(CREDENTIALS_FILE):
        logger.warning(
            f"'{CREDENTIALS_FILE}' not found. Google Drive uploads will be disabled.\n"
            f"To enable Google Drive uploads, please follow the instructions in SERVICE_ACCOUNT_SETUP.md"
        )
        return None
        
    # Rest of the authentication logic...
```

### 2. Improve Error Handling in Upload Function

Update the `upload_to_drive()` function to handle a missing service gracefully:

```python
def upload_to_drive(file_path, folder_name=None):
    """Upload a file to Google Drive with improved error handling"""
    if not os.path.exists(file_path):
        logger.error(f"Cannot upload non-existent file: {file_path}")
        return None
        
    drive_service = get_drive_service()
    if not drive_service:
        logger.warning("Google Drive service unavailable. Skipping upload.")
        return None
        
    # Rest of the upload logic...
```

### 3. Add Clear User Feedback in Unified Workflow

Update the `unified_process_comic()` function in `unified_workflow.py` to provide clear feedback about Google Drive status:

```python
# In unified_process_comic function
# Upload to Google Drive if enabled
drive_links = []
if settings.get("upload_to_drive", False):
    drive_service = get_drive_service()
    if not drive_service:
        logger.warning(f"Skipping Google Drive upload for {comic['name']} chapter {current_chapter} - service unavailable")
    else:
        for file_path in saved_files:
            drive_link = upload_to_drive(file_path, f"Chaptrix/{comic['name']}")
            if drive_link:
                drive_links.append(drive_link)
                logger.info(f"Uploaded {os.path.basename(file_path)} to Google Drive")
            else:
                logger.warning(f"Failed to upload {os.path.basename(file_path)} to Google Drive")
```

## Best Practices for Credential Management

### Environment Variables

Consider using environment variables for sensitive credentials:

```python
def get_drive_service_from_env():
    """Get Google Drive service using credentials from environment variables"""
    import os
    import json
    from google.oauth2.service_account import Credentials
    
    # Check for credentials in environment variable
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        logger.warning("GOOGLE_CREDENTIALS environment variable not set. Google Drive uploads will be disabled.")
        return None
        
    try:
        creds_info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Error creating Drive service from environment: {e}")
        return None
```

### Dotenv Support

Add support for `.env` files to simplify local development:

```python
# At the top of main.py
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file if it exists
    logger.info("Loaded environment variables from .env file")
except ImportError:
    pass  # dotenv is optional
```

## Testing Google Drive Integration

### Manual Testing

To test Google Drive integration manually:

1. Create a test script that attempts to upload a small file
2. Run it with and without credentials to verify proper error handling
3. Check that the application continues to function when Google Drive is unavailable

### Automated Testing

Add unit tests for Google Drive integration:

```python
def test_drive_service_with_missing_credentials(monkeypatch):
    """Test that get_drive_service handles missing credentials gracefully"""
    # Ensure credentials file doesn't exist for this test
    monkeypatch.setattr(os.path, "exists", lambda path: False if "credentials.json" in path else os.path.exists(path))
    
    # Should return None without raising exceptions
    assert get_drive_service() is None

def test_upload_to_drive_with_no_service():
    """Test that upload_to_drive handles missing service gracefully"""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix=".txt") as temp:
        temp.write(b"Test content")
        temp.flush()
        
        # Should return None without raising exceptions
        assert upload_to_drive(temp.name, "test_folder") is None
```

## Conclusion

By implementing these improvements, the Chaptrix application will handle Google Drive integration more gracefully, providing clear feedback to users and continuing to function even when credentials are missing or invalid. This will significantly improve the user experience and reduce confusion for new users who haven't set up Google Drive integration yet.