import os
import sys
import json
import logging
from datetime import datetime

# Add the current directory to the path so we can import from main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the stitcher module
from stitcher import stitch_images_multi_page, save_stitched_images

# Import the banner cropper
from banner_cropper import crop_banner_if_found

# Import necessary functions from main.py
try:
    from main import load_tracked_comics, load_settings, get_site_adapter
    from main import upload_to_drive, send_discord_notification
    from main import CONFIG_FILE
except ImportError as e:
    print(f"Error importing from main.py: {e}")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chaptrix_unified.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ChaptrixUnified")

def unified_process_comic(comic, tracked_comics, comic_index):
    """
    Unified process that combines enhanced stitching and banner cropping
    
    Args:
        comic: Comic dictionary containing name, url, etc.
        tracked_comics: List of all tracked comics
        comic_index: Index of the current comic in tracked_comics
        
    Returns:
        bool: True if a new chapter was found and processed, False otherwise
    """
    settings = load_settings()
    logger.info(f"Processing comic: {comic['name']} (URL: {comic['url']})")
    
    # Get the appropriate site adapter
    adapter = get_site_adapter(comic)
    if not adapter:
        logger.error(f"No suitable adapter found for {comic['name']}")
        return False
    
    # Get latest chapter info
    current_chapter, chapter_url = adapter.get_latest_chapter()
    
    if not current_chapter or not chapter_url:
        logger.error(f"Failed to retrieve current chapter for {comic['name']}. Skipping.")
        return False
    
    # Check if this is a new chapter
    if current_chapter == comic['last_known_chapter']:
        logger.info(f"No new chapter for {comic['name']}. Still at {comic['last_known_chapter']}")
        return False
    
    logger.info(f"New chapter found for {comic['name']}: {current_chapter} (was {comic['last_known_chapter']})")
    
    # Create directories if they don't exist
    download_dir = os.path.join(settings["download_path"], comic['name'].replace('/', '_'))
    processed_dir = os.path.join(settings["processed_path"], comic['name'].replace('/', '_'))
    
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    # Download chapter images
    images = adapter.download_chapter_images(chapter_url)
    
    if not images:
        logger.error(f"Failed to download images for {comic['name']} chapter {current_chapter}")
        return False
    
    # Process images if template is provided
    if 'template_image' in comic and comic['template_image'] and os.path.exists(comic['template_image']):
        try:
            from main import remove_image_parts
            import PIL.Image as Image
            
            template = Image.open(comic['template_image'])
            processed_images = []
            
            for img in images:
                processed_img = remove_image_parts(img, template)
                processed_images.append(processed_img)
            
            images = processed_images
            logger.info(f"Applied template processing to {len(images)} images")
        except Exception as e:
            logger.error(f"Error processing images with template: {e}")
    
    # Apply banner cropping
    banner_path = "assets/banner.png"
    if os.path.exists(banner_path):
        try:
            import cv2
            import PIL.Image as Image
            from io import BytesIO
            
            banner = cv2.imread(banner_path)
            if banner is not None:
                logger.info(f"Applying banner cropping to {len(images)} images")
                
                # Save images temporarily to apply cropping
                temp_dir = os.path.join(download_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                
                for i, img in enumerate(images):
                    temp_path = os.path.join(temp_dir, f"temp_{i}.jpg")
                    img.save(temp_path)
                    crop_banner_if_found(temp_path, banner)
                    # Reload the cropped image
                    images[i] = Image.open(temp_path)
                
                logger.info(f"Banner cropping completed successfully")
        except Exception as e:
            logger.error(f"Error applying banner cropping: {e}")
    
    # Use the multi-page stitcher module
    logger.info(f"Stitching {len(images)} images for {comic['name']} chapter {current_chapter}")
    
    # Get image dimensions from settings
    target_width = settings.get("image_width", 0)
    max_height = settings.get("max_image_height", 12000)  # Default to 12000px if not specified
    image_quality = settings.get("image_quality", 90)
    
    # Stitch images with multi-page support
    stitched_images = stitch_images_multi_page(images, target_width, max_height, image_quality)
    if not stitched_images:
        logger.error(f"Failed to stitch images for {comic['name']} chapter {current_chapter}")
        return False
    
    # Save processed images
    safe_chapter = current_chapter.replace('/', '_').replace('\\', '_')
    processed_file_template = os.path.join(processed_dir, f"{safe_chapter}.jpg")
    
    saved_files = save_stitched_images(stitched_images, processed_file_template, image_quality)
    if not saved_files:
        logger.error(f"Failed to save stitched images for {comic['name']} chapter {current_chapter}")
        return False
    
    logger.info(f"Saved {len(saved_files)} stitched image(s) for {comic['name']} chapter {current_chapter}")
    
    # Upload to Google Drive if enabled
    drive_links = []
    if settings.get("upload_to_drive", False):
        for file_path in saved_files:
            drive_link = upload_to_drive(file_path, f"Chaptrix/{comic['name']}")
            if drive_link:
                drive_links.append(drive_link)
    
    # Create Discord notification
    embed = {
        "title": f"🎉 New Chapter Alert! 🎉",
        "description": f"Manga: **{comic['name']}**\nNew Chapter: **{current_chapter}**",
        "url": chapter_url,
        "color": 65280,
        "fields": [
            {
                "name": "Read it here",
                "value": f"[Click to Read]({chapter_url})",
                "inline": False
            }
        ],
        "footer": {
            "text": "Chaptrix Manga Notifier"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Add Drive links if available
    if drive_links:
        if len(drive_links) == 1:
            embed["fields"].append({
                "name": "Download Stitched Chapter",
                "value": f"[Google Drive Link]({drive_links[0]})",
                "inline": False
            })
        else:
            links_text = "\n".join([f"[Part {i+1}]({link})" for i, link in enumerate(drive_links)])
            embed["fields"].append({
                "name": "Download Stitched Chapter (Multiple Parts)",
                "value": links_text,
                "inline": False
            })
    
    # Send Discord notification if enabled
    if settings.get("upload_to_discord", False):
        message_content = f"Hey everyone! A new chapter for **{comic['name']}** is out!"
        
        # Send the first file with the embed
        send_discord_notification(message_content, embed, saved_files[0])
        
        # Send additional files if there are multiple parts
        if len(saved_files) > 1:
            for i, file_path in enumerate(saved_files[1:], 1):
                part_message = f"**{comic['name']}** - {current_chapter} (Part {i+1}/{len(saved_files)})"
                send_discord_notification(part_message, None, file_path)
    
    # Update comic's last known chapter
    tracked_comics[comic_index]['last_known_chapter'] = current_chapter
    return True

def main():
    """
    Main function to check all comics for updates with unified processing
    """
    logger.info("Unified Chaptrix workflow started. Loading tracked comics...")
    tracked_comics = load_tracked_comics()
    settings = load_settings()
    
    if not tracked_comics:
        logger.warning("No comics tracked. Please add some to comics.json.")
        return
    
    logger.info(f"Checking {len(tracked_comics)} comics for updates...")
    
    updates_found = 0
    for i, comic in enumerate(tracked_comics):
        try:
            # Skip comics from disabled site adapters
            site = None
            if 'site' in comic and comic['site'] in settings.get('site_adapters', {}):
                site = comic['site']
                if not settings['site_adapters'][site].get('enabled', True):
                    logger.info(f"Skipping {comic['name']} - site adapter {site} is disabled")
                    continue
            else:
                # Auto-detect site from URL
                if 'baozimh.com' in comic['url']:
                    site = 'baozimh'
                elif 'twmanga.com' in comic['url']:
                    site = 'twmanga'
                
                if site and site in settings.get('site_adapters', {}) and not settings['site_adapters'][site].get('enabled', True):
                    logger.info(f"Skipping {comic['name']} - auto-detected site adapter {site} is disabled")
                    continue
            
            if unified_process_comic(comic, tracked_comics, i):
                updates_found += 1
        except Exception as e:
            logger.error(f"Error processing comic {comic['name']}: {e}")
    
    # Save the updated tracked_comics data
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracked_comics, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Check complete. Found {updates_found} new chapters.")
    logger.info(f"Updated comic data saved to {CONFIG_FILE}")

if __name__ == "__main__":
    main()