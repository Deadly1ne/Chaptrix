# Chaptrix

An all-in-one manga chapter notification and download bot for baozimh.com

![Chaptrix Banner](assets/banner.png)

## Features

- 🔍 **Monitor manga series** from baozimh.com for new chapter releases
- 📥 **Download new chapters** automatically when available
- 🖼️ **Process images** - stitch them together and remove unwanted parts
- ✂️ **Banner cropping** - Automatically detect and remove banner images from manga pages
- 📊 **Enhanced stitcher** - Improved image stitching with better memory management and error handling
- ☁️ **Upload to cloud** - Google Drive integration for easy access
- 🤖 **Discord notifications** - Get alerts with download links
- 🎛️ **User-friendly dashboard** - Manage everything through a Streamlit web interface

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- A Discord account (optional, only if you want notifications)
- A Google account (optional, only if you want Drive integration)

### Installation

1. Clone this repository or download the files

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up Discord webhook (optional, for notifications):
   - Create a Discord server or use an existing one
   - Create a channel for notifications
   - Go to Channel Settings > Integrations > Webhooks > New Webhook
   - Copy the webhook URL
   - Add it to the settings in the dashboard
   - Note: Discord integration is completely optional. Chaptrix will work without it.

4. Set up Google Drive API (optional, for Drive uploads):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Drive API
   - Create OAuth 2.0 credentials
   - Download the credentials as JSON
   - Rename it to `credentials.json` and place it in the project directory

### Running the Application

#### Dashboard Mode

To run the Streamlit dashboard for managing comics and settings:

```
streamlit run main.py
```

Or use the provided batch file:

```
run_dashboard.bat
```

This will open a web interface where you can:
- Add/edit/remove manga series
- Configure settings
- Run manual checks
- Set up automation

#### Check Mode

To run a one-time check for new chapters (useful for scheduled tasks):

```
python main.py --check
```

Or use the provided batch file:

```
run_check.bat
```

#### Unified Workflow Mode

To run the complete workflow with banner cropping and stitching functionality:

```
python unified_workflow.py
```

Or use the provided batch file:

```
run_unified_workflow.bat
```



#### Standalone Stitcher

To stitch images for a specific comic and chapter:

```
python stitcher.py "Comic Name" "Chapter Name" [--width WIDTH] [--height HEIGHT] [--quality QUALITY]
```

### Automation

You can automate checks using:

1. **GitHub Actions** - If you host this on GitHub, use the provided workflow example
   - See our detailed [Automation Guide](AUTOMATION.md) for setup instructions
   - Configure [Google Drive Service Account](SERVICE_ACCOUNT_SETUP.md) for headless operation
   - Set up [Discord Integration](DISCORD_SETUP.md) for notifications
   - Check [Troubleshooting](TROUBLESHOOTING.md) if you encounter issues
2. **Windows Task Scheduler** - Schedule `python main.py --check` to run periodically
3. **Cron jobs** - On Linux/macOS, set up cron to run the check command

## Image Processing

### Template Images

To remove specific parts of manga images (like watermarks or ads):

1. Create a template image that contains only the part you want to remove
2. Upload it when adding a new manga series
3. The bot will automatically detect and remove matching parts

### Banner Cropper

The banner cropper automatically detects and removes banner images from manga pages:

1. Place your banner template image in the `assets` folder as `banner.png`
2. Banner cropping is integrated into the unified workflow
3. For more details, see the [Banner Cropper README](BANNER_CROPPER_README.md)

### Enhanced Stitcher

The enhanced stitcher provides improved image stitching with better memory management and error handling:

1. Use it as a standalone tool with `python stitcher.py`
2. Stitching is integrated into the unified workflow
3. Features include:
   - Better memory management for large image sets
   - Improved error handling and recovery
   - Progress tracking for large operations
   - Configurable image quality and dimensions
   - Detailed logging

For more details, see the [Enhanced Stitcher README](STITCHER_README.md)

## Configuration

### comics.json

Stores information about tracked manga series:

```json
[
    {
        "name": "My Favorite Manga",
        "url": "https://www.baozimh.com/comic/your-comic-slug-here",
        "last_known_chapter": "Chapter 0",
        "template_image": "templates/watermark.png"  // Optional
    }
]
```

### settings.json

Stores application settings:

```json
{
    "check_interval": 14400,
    "image_width": 800,
    "image_height": 0,
    "upload_to_drive": true,
    "upload_to_discord": true,
    "download_path": "downloads",
    "processed_path": "processed",
    "discord_webhook_url": "YOUR_WEBHOOK_URL",
    "discord_bot_token": "",
    "discord_channel_id": ""
}
```

## Troubleshooting

- **No chapters found**: Make sure the manga URL is correct and the series exists
- **Discord notifications not working**: Verify your webhook URL is correct
- **Google Drive upload fails**: Check your credentials.json file and authentication
- **Image processing issues**: Try adjusting the image width/height settings
- **Banner cropping not working**: Ensure your banner.png template is clear and matches the banners in your manga
- **OpenCV errors**: Make sure you've installed all requirements with `pip install -r requirements.txt`
- **Stitcher memory errors**: For very large manga chapters, the unified workflow handles memory efficiently
- **Stitcher quality issues**: Adjust the quality parameter in settings.json

## License

This project is available for personal use.

## Acknowledgements

- Built with Python, Streamlit, and various libraries
- Icon and banner assets included in the repository