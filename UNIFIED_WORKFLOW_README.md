# Chaptrix Unified Workflow

This document explains the unified workflow implementation for Chaptrix, which combines multiple steps into a streamlined process.

## Overview

The unified workflow handles the following steps in sequence:

1. **Check for new chapters** - Scans tracked comics for new releases
2. **Download new chapters** - Downloads images for any new chapters found
3. **Remove watermarks** - Applies banner cropping to remove watermarks from images
4. **Stitch images** - Combines all chapter images into a single long image
5. **Upload and notify** - Uploads to Discord/Google Drive and sends notifications

## Available Scripts

### 1. Batch Script

#### `run_unified_workflow.bat`

This batch file runs the new unified implementation:
- Executes `unified_workflow.py`, which combines all functionality into a single script
- Provides a more integrated experience with better logging and error handling

This is the recommended approach for most users.

### 2. Python Implementation

#### `unified_workflow.py`

A comprehensive Python script that combines all functionality:
- Integrates both the enhanced stitcher and banner cropper
- Processes each comic in a single pass
- Handles downloading, cropping, stitching, and uploading in sequence
- Provides detailed logging in `chaptrix_unified.log`

## Configuration

The unified workflow uses the same configuration files as the existing implementation:

- `settings.json` - General settings including paths and options
- `comics.json` - List of tracked comics

Make sure `enable_banner_cropping` is set to `true` in `settings.json` to enable watermark removal.

## Troubleshooting

If you encounter issues with the unified workflow:

1. Check the log file at `chaptrix_unified.log` for detailed error messages
2. Ensure all dependencies are installed (OpenCV, PIL, etc.)
3. Verify that `banner.png` exists in the `assets` directory
4. Make sure your `settings.json` and `comics.json` files are properly configured

## Extending the Workflow

To add new functionality to the unified workflow:

1. Modify `unified_workflow.py` to include the new processing steps
2. Update the configuration in `settings.json` as needed
3. Add any new dependencies to your environment

## Other Scripts

The following scripts are also available:

- `run_check.bat` - Runs the basic check for new chapters
- `validate_config.bat` - Validates your configuration

However, it's recommended to use the unified workflow for a more streamlined experience.