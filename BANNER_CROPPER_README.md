# Chaptrix Banner Cropper

This extension for Chaptrix automatically detects and removes banner images from manga pages. It's particularly useful for removing watermarks, ads, or other unwanted elements that appear consistently at the top or bottom of manga pages.

## How It Works

1. The banner cropper uses OpenCV's template matching to identify banner images at the top or bottom of manga pages.
2. When a match is found with sufficient confidence (default: 90%), the banner is cropped out of the image.
3. The cropper can be integrated with the main Chaptrix workflow or run separately on specific chapters.

## Setup

1. Make sure you have installed the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Place your banner template image in the `assets` folder as `banner.png`. This should be an image of the banner you want to remove.

## Usage

### Option 1: Integrated with Chaptrix

Run the unified workflow script which will check for new chapters and apply banner cropping automatically:

```
run_unified_workflow.bat
```

Or manually run:

```
python unified_workflow.py
```

### Option 2: Process Specific Chapters

To process a specific comic and chapter:

1. Edit the `banner_cropper.py` file and modify the last line to specify your comic and chapter:
   ```python
   if __name__ == "__main__":
       run_cropper("Your Comic Name", "Chapter_XX")
   ```

2. Run the script:
   ```
   python banner_cropper.py
   ```

## Creating a Banner Template

1. Take a screenshot of the banner you want to remove.
2. Crop it precisely to include only the banner.
3. Save it as `banner.png` in the `assets` folder.

## Adjusting Sensitivity

If the cropper is not detecting banners correctly, you can adjust the threshold value in the `crop_banner_if_found` function:

- Higher threshold (closer to 1.0): More precise matching, may miss some banners
- Lower threshold (closer to 0.8): More aggressive matching, may incorrectly crop some images

## Troubleshooting

- If banners aren't being detected, check that your template image is clear and representative of the banners in your manga.
- If you're getting errors about missing OpenCV, make sure you've installed all requirements: `pip install -r requirements.txt`
- Check the `chaptrix_cropper.log` file for detailed information about the cropping process.

## Integration with Existing Templates

The banner cropper works alongside Chaptrix's existing template-based image processing. If you're already using templates to remove watermarks, the banner cropper provides an additional way to clean up your manga pages.