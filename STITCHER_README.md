# Enhanced Stitcher for Chaptrix

The Enhanced Stitcher module provides improved image stitching functionality for the Chaptrix manga downloader. It offers better memory management, error handling, and configurability compared to the original stitching implementation.

## Features

- 🧠 **Improved memory management** - Optimized for large manga chapters with many images
- 🛡️ **Enhanced error handling** - Graceful recovery from image processing errors
- 📊 **Progress tracking** - Detailed logging of stitching progress
- 🎛️ **Configurable parameters** - Adjust width, height, and quality settings
- 🔄 **Standalone operation** - Can be used independently or integrated with Chaptrix

## Usage Options

### 1. Standalone Mode

Use the stitcher directly to process a specific comic and chapter:

```bash
python stitcher.py "Comic Name" "Chapter Name" [--width WIDTH] [--height HEIGHT] [--quality QUALITY]
```

#### Parameters

- `Comic Name`: Name of the comic (must match the folder name in downloads/)
- `Chapter Name`: Name of the chapter to stitch
- `--width`: Target width in pixels (optional, default: auto-detected)
- `--height`: Target height in pixels (optional, default: calculated from aspect ratio)
- `--quality`: JPEG quality (0-100, optional, default: 90)

### 2. Integrated Mode

Run the stitcher as part of the Chaptrix unified workflow:

```bash
python unified_workflow.py
```

Or use the provided batch file:

```bash
run_unified_workflow.bat
```

This will check for new chapters of all tracked comics and use the stitcher for processing.

### 3. Programmatic Usage

Import and use the stitcher functions in your own Python code:

```python
from stitcher import stitch_images, save_stitched_image, stitch_folder

# Stitch a list of PIL Image objects
stitched_img = stitch_images(images, target_width=800, target_height=None, quality=90)

# Save the stitched image
save_stitched_image(stitched_img, "output.jpg", quality=90)

# Stitch all images in a folder
stitch_folder("input_folder", "output.jpg", target_width=800)
```

## Testing

To verify that the stitcher is working correctly, run the test script:

```bash
python test_stitcher.py
```

Or use the provided batch file:

```bash
test_stitcher.bat
```

The test script will create sample images, stitch them together, and verify the results.

## Configuration

The stitcher uses the following settings from `settings.json`:

- `image_width`: Target width for the stitched image (0 = auto-detect)
- `image_height`: Target height for the stitched image (0 = calculate from aspect ratio)
- `image_quality`: JPEG quality setting (0-100, default: 90)

You can override these settings when using the standalone mode.

## Troubleshooting

### Common Issues

- **Memory errors**: If you encounter memory errors when stitching very large chapters:
  - Try reducing the target width/height
  - Process fewer images at once
  - Close other memory-intensive applications

- **Image quality issues**: If the stitched image quality is poor:
  - Increase the quality parameter (e.g., `--quality 95`)
  - Increase the target width for higher resolution

- **Missing images**: If some images are missing from the stitched output:
  - Check the stitcher log file for errors
  - Verify that all images in the input folder are valid

### Logging

The stitcher creates a detailed log file at `stitcher.log` that can help diagnose issues.

## Technical Details

### Memory Optimization

The enhanced stitcher implements several memory optimization techniques:

1. **Progressive processing**: Images are processed one at a time rather than loading all into memory
2. **Explicit cleanup**: Temporary objects are explicitly removed to help garbage collection
3. **Resize before paste**: Images are resized just before being pasted into the final image

### Error Handling

The stitcher includes robust error handling to prevent failures:

1. **Per-image error catching**: Errors in individual images don't stop the entire process
2. **Input validation**: Checks for valid input parameters before processing
3. **Graceful degradation**: Falls back to reasonable defaults when parameters are invalid

## Integration with Other Modules

The enhanced stitcher works seamlessly with other Chaptrix modules:

- **Banner Cropper**: Images can be processed with the banner cropper before stitching
- **Template Removal**: Template-based image processing is supported
- **Google Drive Upload**: Stitched images can be uploaded to Google Drive
- **Discord Notifications**: Notifications include links to the stitched images

## Future Improvements

Planned enhancements for future versions:

- Multi-threaded processing for faster stitching
- Additional output formats (PNG, WebP)
- Smart image compression to reduce file size while maintaining quality
- Automatic detection and correction of page orientation