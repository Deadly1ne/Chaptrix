# Chaptrix - Unified Workflow

## New Unified Workflow Implementation

This document describes the new unified workflow implementation for Chaptrix, which streamlines the manga processing pipeline into a single integrated process.

## Overview

The unified workflow handles the following steps in sequence:

1. **Check for new chapters** - Monitors manga sites for new chapter releases
2. **Download new chapters** - Automatically downloads images for new chapters
3. **Remove watermarks** - Uses template matching to remove watermarks/banners
4. **Stitch images** - Combines chapter images into a single long image
5. **Upload processed chapters** - Uploads to Discord and/or Google Drive
6. **Send notifications** - Notifies users about new chapters via Discord

## New Components

The unified workflow introduces several new components:

### 1. Unified Python Script

`unified_workflow.py` - A comprehensive Python script that combines all functionality:
- Integrates both the enhanced stitcher and banner cropper
- Processes each comic in a single pass
- Handles downloading, cropping, stitching, and uploading in sequence
- Provides detailed logging in `chaptrix_unified.log`

### 2. Batch Files

#### `run_unified_workflow.bat`

Runs the new unified implementation:
- Executes `unified_workflow.py`, which combines all functionality into a single script
- Provides a more integrated experience with better logging and error handling



### 3. Configuration Validator

`config_validator.py` - A utility script that validates your Chaptrix configuration:
- Checks settings.json for required fields and valid values
- Validates comics.json structure and entries
- Verifies that required dependencies are installed
- Ensures all necessary files are present

Run it with `validate_config.bat` to check your setup before running Chaptrix.

## Usage

### Recommended Approach

For most users, the unified workflow is the recommended approach:

```
run_unified_workflow.bat
```

This will run the entire process from checking for new chapters to uploading and notifications in a single integrated workflow.



### Configuration Validation

Before running Chaptrix, it's recommended to validate your configuration:

```
validate_config.bat
```

This will check your settings, comics, dependencies, and files to ensure everything is properly configured.

## Documentation

Detailed documentation is available in the following files:

- `UNIFIED_WORKFLOW_README.md` - Information about the unified workflow
- `IMPLEMENTATION_GUIDE.md` - Technical details and maintenance guidelines
- `BANNER_CROPPER_README.md` - Instructions for the banner cropper

## Troubleshooting

### Logs

Check the following log files for detailed information:

- `chaptrix.log` - General log file
- `stitcher.log` - Logs from the stitcher process
- `chaptrix_cropper.log` - Logs from the banner cropper
- `chaptrix_unified.log` - Logs from the unified workflow

### Common Issues

1. **No new chapters found**
   - Check if the manga site structure has changed
   - Verify your internet connection
   - Check if the site is blocking automated requests

2. **Banner cropping not working**
   - Ensure `enable_banner_cropping` is set to `true` in settings.json
   - Verify `banner.png` exists in the `assets` directory
   - Check if the banner template matches the actual watermarks

3. **Upload failures**
   - For Discord: Verify your webhook URL is correct
   - For Google Drive: Check your credentials and permissions

## Conclusion

The unified workflow provides a more streamlined and integrated experience for Chaptrix users. By combining all steps into a single process, it simplifies usage and improves reliability. We recommend using this new implementation for the best experience.