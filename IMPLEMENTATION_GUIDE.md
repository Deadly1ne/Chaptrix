# Chaptrix Implementation Guide

## System Architecture

The Chaptrix system is designed with a modular architecture to handle manga chapter processing. The system consists of the following components:

### Core Components

1. **Site Adapters**: Handle site-specific logic for different manga sources
2. **Downloader**: Downloads chapter images from manga sites
3. **Image Processor**: Processes images (cropping, watermark removal)
4. **Stitcher**: Combines multiple images into a single long image
5. **Uploader**: Uploads processed chapters to Discord/Google Drive
6. **Notifier**: Sends notifications about new chapters

### Workflow Implementation

The system now has three different workflow implementations:

1. **Original Workflow**: Separate scripts for checking/stitching and cropping
2. **Combined Workflow**: Batch script that runs both processes sequentially
3. **Unified Workflow**: Integrated Python implementation that handles all steps

## Code Organization

### Key Files

- `main.py`: Core functionality and utilities
- `stitcher.py`: Image stitching implementation with multi-page support
- `banner_cropper.py`: Watermark removal using template matching
- `unified_workflow.py`: Integrated implementation that handles all steps

### Configuration Files

- `settings.json`: System-wide configuration
- `comics.json`: List of tracked comics

## Maintenance Guidelines

### Adding New Features

When adding new features to Chaptrix:

1. **Identify the appropriate component**: Determine which component should handle the new functionality
2. **Implement in the unified workflow**: Add the feature to `unified_workflow.py` to ensure it's part of the integrated process
3. **Update configuration**: Add any necessary configuration options to `settings.json`
4. **Document the changes**: Update the README files to reflect the new functionality

### Adding Support for New Manga Sites

To add support for a new manga site:

1. **Create a new site adapter**: Implement the required methods for the new site
2. **Register the adapter**: Add the new adapter to the site adapters in `settings.json`
3. **Test thoroughly**: Ensure the adapter works correctly with the unified workflow

### Error Handling Best Practices

1. **Use try-except blocks**: Wrap site-specific code in try-except to prevent one site's failure from affecting others
2. **Detailed logging**: Log detailed error information to help with debugging
3. **Graceful degradation**: Allow the system to continue processing other comics if one fails

## Performance Optimization

### Image Processing

1. **Batch processing**: Process images in batches to reduce memory usage
2. **Resize before stitching**: Resize images to the target dimensions before stitching
3. **Use appropriate image quality**: Balance file size and quality with the `image_quality` setting

### Network Operations

1. **Implement retries**: Add retry logic for network operations to handle temporary failures
2. **Use async/await**: Consider using asynchronous programming for network-bound operations
3. **Implement rate limiting**: Respect site rate limits to avoid being blocked

## Testing Strategy

1. **Unit tests**: Test individual components in isolation
2. **Integration tests**: Test the complete workflow with mock data
3. **Manual testing**: Periodically test with real manga sites to ensure compatibility

## Future Enhancements

### Short-term Improvements

1. **Better error reporting**: Enhance error messages and logging
2. **Progress indicators**: Add progress bars or status updates for long-running operations
3. **Configuration UI**: Create a simple web UI for configuration

### Long-term Vision

1. **Plugin system**: Implement a plugin architecture for easier extension
2. **Scheduled checks**: Add support for scheduled checks without manual intervention
3. **Mobile notifications**: Extend notifications to mobile devices
4. **User preferences**: Allow per-user preferences for notifications and uploads

## Troubleshooting Common Issues

### Image Processing Issues

1. **Banner not detected**: Ensure the banner template is clear and matches the actual watermarks
2. **Stitching problems**: Check image dimensions and format compatibility
3. **Memory errors**: Reduce batch size or image quality for large chapters

### Network Issues

1. **Site changes**: Update site adapters when manga sites change their structure
2. **Rate limiting**: Implement delays between requests to avoid being blocked
3. **Authentication**: Handle sites that require login or cookies

### System Integration

1. **Discord API changes**: Keep Discord notification code updated with API changes
2. **Google Drive API**: Maintain proper authentication for Google Drive uploads
3. **Dependency conflicts**: Manage Python dependencies carefully to avoid conflicts

## Conclusion

This implementation guide provides a foundation for maintaining and extending the Chaptrix system. By following these guidelines, you can ensure that the system remains robust, efficient, and adaptable to changing requirements.