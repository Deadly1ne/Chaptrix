import argparse
import asyncio
import io
import json
import logging
import os
import re
import requests
import zipfile

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chaptrix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Chaptrix")

import discord
from discord.ext import commands
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.auth.transport.requests import Request
from google.auth.transport.requests import AuthorizedSession
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.protobuf.json_format import MessageToJson, Parse, ParseDict
# Note: ParseMessage is not available in protobuf 6.31.1

from PIL import Image
from bs4 import BeautifulSoup

from stitcher import stitch_images_multi_page
from stitcher import save_stitched_images

# Import streamlit only if it's available
try:
    import streamlit as st
except ImportError:
    st = None

SETTINGS_FILE = "settings.json"
CONFIG_FILE = "comics.json"
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
SUPPORTED_SITES = {
    "baozimh": {
        "name": "Baozimh",
        "url": "https://www.baozimh.com",
        "template": 'baozimh_logo_template.svg'
    },
    "twmanga": {
        "name": "Twmanga",
        "url": "https://www.twmanga.com",
        "template": 'twmanga_logo_template.svg'
    }
}

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Default settings
DEFAULT_SETTINGS = {
    "check_interval": 14400,  # 4 hours in seconds
    "image_width": 800,      # Default width for stitched images
    "image_height": 0,       # 0 means auto-calculate height
    "upload_to_drive": True,
    "upload_to_discord": True,
    "download_path": "downloads",
    "processed_path": "processed",
    "discord_webhook_url": "",
    "discord_bot_token": "",
    "discord_channel_id": "",
    "site_adapters": {
        "baozimh": {
            "enabled": True,
            "template": "baozimh_logo_template.svg"
        },
        "twmanga": {
            "enabled": True,
            "template": "twmanga_logo_template.svg"
        }
    }
}

# Regular expression for baozimh CDN URLs
BAOZI_CDN_REGEX = r'^https?://(?:[\w-]+)\.baozicdn\.com/(.+)$'
BAOZI_CDN_REPLACEMENT = r'https://static-tw.baozimh.com/\1'

# ===== Utility Functions =====

def load_settings():
    """Load user settings from settings.json"""
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # Merge with default settings to ensure all keys exist
            return {**DEFAULT_SETTINGS, **settings}
    except FileNotFoundError:
        logger.info(f"'{SETTINGS_FILE}' not found. Creating with default settings.")
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    except json.JSONDecodeError:
        logger.error(f"Error reading '{SETTINGS_FILE}'. File might be malformed. Using defaults.")
        return DEFAULT_SETTINGS

def save_settings(settings):
    """Save user settings to settings.json"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved settings to '{SETTINGS_FILE}'.")
    except IOError as e:
        logger.error(f"Error saving '{SETTINGS_FILE}': {e}")

def load_tracked_comics():
    """Loads the list of tracked comics from comics.json"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info(f"'{CONFIG_FILE}' not found. Creating an empty list for tracked comics.")
        return []
    except json.JSONDecodeError:
        logger.error(f"Error reading '{CONFIG_FILE}'. File might be empty or malformed. Starting with empty list.")
        return []

def save_tracked_comics(comics):
    """Saves the current list of tracked comics to comics.json"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(comics, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved updated comic data to '{CONFIG_FILE}'.")
    except IOError as e:
        logger.error(f"Error saving '{CONFIG_FILE}': {e}")

def get_drive_service():
    """Get authenticated Google Drive service"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_info(json.load(open(TOKEN_FILE)))
        except Exception as e:
            logger.error(f"Error loading token file: {e}")
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing credentials: {e}")
                return None
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(f"'{CREDENTIALS_FILE}' not found. Please download it from Google Cloud Console.")
                return None
                
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=8080)
            except Exception as e:
                logger.error(f"Error in authentication flow: {e}")
                return None
                
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    try:
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Error building Drive service: {e}")
        return None

def send_discord_notification(message_content, embed=None, file_path=None):
    """Sends a notification to Discord via webhook or bot"""
    settings = load_settings()
    
    # Check if Discord notifications are enabled
    if not settings.get("upload_to_discord", True):
        logger.info("Discord notifications are disabled in settings")
        return False
    
    # Try webhook first if available
    if settings.get("discord_webhook_url"):
        payload = {"content": message_content}
        if embed:
            payload["embeds"] = [embed]
        
        files = None
        if file_path and os.path.exists(file_path):
            files = {"file": open(file_path, "rb")}
        
        try:
            # First try with file attachment if provided
            if files:
                try:
                    response = requests.post(settings["discord_webhook_url"], data={"payload_json": json.dumps(payload)}, files=files)
                    response.raise_for_status()
                    logger.info(f"Discord webhook notification sent successfully with file: {file_path}")
                    return True
                except requests.exceptions.HTTPError as e:
                    # If we get a 413 Payload Too Large error, try again without the file
                    if e.response.status_code == 413:
                        logger.warning(f"File too large for Discord webhook (413 error). Sending message without attachment.")
                        files["file"].close()  # Close the file before retrying
                        response = requests.post(settings["discord_webhook_url"], json=payload)
                        response.raise_for_status()
                        logger.info("Discord webhook notification sent successfully without file attachment")
                        return True
                    else:
                        # Re-raise if it's not a 413 error
                        raise
                finally:
                    # Make sure file is closed
                    if "file" in files and hasattr(files["file"], "close"):
                        files["file"].close()
            else:
                # No file to attach, just send the message
                response = requests.post(settings["discord_webhook_url"], json=payload)
                response.raise_for_status()
                logger.info("Discord webhook notification sent successfully without file attachment")
                return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Discord webhook notification: {e}")
            return False
    
    # Fall back to bot if webhook fails or isn't configured
    elif settings.get("discord_bot_token") and settings.get("discord_channel_id"):
        async def send_bot_message():
            try:
                intents = discord.Intents.default()
                intents.message_content = True
                bot = commands.Bot(command_prefix="!", intents=intents)
                
                @bot.event
                async def on_ready():
                    try:
                        channel = bot.get_channel(int(settings["discord_channel_id"]))
                        if not channel:
                            logger.error(f"Could not find channel with ID {settings['discord_channel_id']}")
                            await bot.close()
                            return
                        
                        if file_path and os.path.exists(file_path):
                            discord_file = discord.File(file_path)
                            if embed:
                                await channel.send(content=message_content, embed=discord.Embed.from_dict(embed), file=discord_file)
                            else:
                                await channel.send(content=message_content, file=discord_file)
                        else:
                            if embed:
                                await channel.send(content=message_content, embed=discord.Embed.from_dict(embed))
                            else:
                                await channel.send(content=message_content)
                        
                        logger.info(f"Discord bot message sent successfully! File: {file_path if file_path else 'None'}")
                    except Exception as e:
                        logger.error(f"Error in on_ready: {e}")
                    finally:
                        await bot.close()
                
                await bot.start(settings["discord_bot_token"])
                return True
            except Exception as e:
                logger.error(f"Error with Discord bot: {e}")
                return False
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(send_bot_message())
        loop.close()
        return success
    
    else:
        logger.warning("No Discord webhook URL or bot token configured. Skipping notification.")
        return False

def upload_to_drive(file_path, folder_name="Chaptrix"):
    """Upload a file to Google Drive and return the shareable link"""
    service = get_drive_service()
    if not service:
        logger.error("Failed to get Google Drive service")
        return None
    
    try:
        # Check if the folder exists, create if not
        folder_id = None
        results = service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id)'
        ).execute()
        
        if not results['files']:
            # Create folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
        else:
            folder_id = results['files'][0]['id']
        
        # Upload file to the folder
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,webViewLink'
        ).execute()
        
        # Make the file publicly accessible via link
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(fileId=file['id'], body=permission).execute()
        
        # Get the updated file with webViewLink
        file = service.files().get(fileId=file['id'], fields='webViewLink').execute()
        
        logger.info(f"File uploaded to Drive: {file['webViewLink']}")
        return file['webViewLink']
    
    except Exception as e:
        logger.error(f"Error uploading to Google Drive: {e}")
        return None

# ===== Web Scraping Functions =====

class MangaSiteAdapter:
    """Base class for manga site adapters"""
    
    def __init__(self, url):
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_latest_chapter(self):
        """Get the latest chapter information (chapter name and URL)"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def download_chapter_images(self, chapter_url):
        """Download all images from a chapter page"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def extract_chapter_number(self, chapter_text):
        """Extract chapter number from chapter text"""
        match = re.search(r'(\d+(?:\.\d+)?)', chapter_text)
        if match:
            chapter_number = match.group(1)
            return f"Chapter {chapter_number}"
        else:
            logger.warning(f"Could not extract clear chapter number from '{chapter_text}'. Using full text for comparison.")
            return chapter_text


class BaozimhAdapter(MangaSiteAdapter):
    """Adapter for baozimh.com"""
    
    def get_latest_chapter(self):
        """Fetches the given comic URL and extracts the latest chapter information"""
        logger.info(f"Fetching URL: {self.url}")
        try:
            response = requests.get(self.url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            section_title_div = soup.find('div', class_='section-title', string=lambda text: text and '最新章節' in text)

            chapter_list_container = None
            if section_title_div:
                chapter_list_container = section_title_div.find_next_sibling('div', class_='pure-g')

            if not chapter_list_container:
                logger.warning("Could not find the '最新章節' section or its direct 'pure-g' container. Attempting fallback searches.")
                chapter_list_container = soup.find('div', class_='comic-chapters-list')
                if not chapter_list_container:
                    chapter_list_container = soup.find('div', class_='pure-g')
                    if chapter_list_container and not chapter_list_container.find('a', class_='comics-chapters__item'):
                        chapter_list_container = None

            if not chapter_list_container:
                logger.error("No suitable chapter list container found on the page after all attempts.")
                return None, None

            chapter_links = chapter_list_container.find_all('a', class_='comics-chapters__item')

            if not chapter_links:
                logger.error("No chapter links with class 'comics-chapters__item' found within the container.")
                return None, None

            # Collect all chapters with their parsed numbers
            chapters_data = []
            for link_element in chapter_links:
                raw_text = link_element.get_text(strip=True)
                chapter_url = link_element['href']
                if not chapter_url.startswith('http'):
                    chapter_url = f"https://www.baozimh.com{chapter_url}"
                
                # Attempt to extract a numerical part for sorting
                match = re.search(r'\d+', raw_text)
                if match:
                    try:
                        chapter_num = float(match.group(0)) # Use float to handle potential decimals
                        chapters_data.append((chapter_num, raw_text, chapter_url))
                    except ValueError:
                        logger.warning(f"Could not convert '{match.group(0)}' to a number for sorting. Skipping chapter: {raw_text}")
                else:
                    logger.warning(f"Could not find a numerical chapter in '{raw_text}'. Skipping for sorting.")

            if not chapters_data:
                logger.error("No valid chapters found for sorting.")
                return None, None

            # Sort chapters by their numerical part in descending order
            chapters_data.sort(key=lambda x: x[0], reverse=True)

            # The first element after sorting is the latest chapter
            latest_chapter_num, latest_chapter_text, latest_chapter_url = chapters_data[0]
                
            logger.info(f"Found raw latest chapter text: '{latest_chapter_text}', URL: {latest_chapter_url} (Numerically latest: {latest_chapter_num})")

            chapter_name = self.extract_chapter_number(latest_chapter_text)
            return chapter_name, latest_chapter_url

        except requests.exceptions.Timeout:
            logger.error(f"Timeout error fetching {self.url}. The server might be slow or unresponsive.")
            return None, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {self.url}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"An unexpected error occurred during scraping {self.url}: {e}")
            return None, None
    
    def download_chapter_images(self, chapter_url):
        """Download all images from a chapter page, including pagination support"""
        logger.info(f"Downloading images from: {chapter_url}")
        try:
            response = requests.get(chapter_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            final_url = response.url
            logger.info(f"Final URL after potential redirect: {final_url}")

            # Check if redirected to twmanga.com
            if "twmanga.com" in final_url:
                logger.info(f"Redirected to twmanga.com. Delegating to TwmangaAdapter for {final_url}")
                twmanga_adapter = TwmangaAdapter(final_url) # Initialize with the final URL
                return twmanga_adapter.download_chapter_images(final_url)

            # Initialize variables for pagination
            all_images = []
            current_url = final_url
            page_count = 1
            max_pages = 20  # Safety limit to prevent infinite loops
            previous_page_images = []  # For duplicate detection
            duplicate_threshold = 4  # Number of last images to check for duplicates
            
            while page_count <= max_pages:
                logger.info(f"Processing page {page_count} of chapter: {current_url}")
                
                try:
                    page_response = requests.get(current_url, headers=self.headers, timeout=15)
                    page_response.raise_for_status()
                    soup = BeautifulSoup(page_response.text, 'html.parser')
                    
                    # Find the container with chapter images
                    image_container = soup.find('div', class_='comic-contain')
                    if not image_container:
                        logger.error(f"Could not find image container on page {page_count}")
                        break
                    
                    # Find all image elements
                    image_elements = image_container.find_all('img')
                    if not image_elements:
                        logger.error(f"No images found on page {page_count}")
                        break
                    
                    # Process images on current page
                    page_images = []
                    for i, img in enumerate(image_elements):
                        img_url = img.get('src')
                        if not img_url:
                            img_url = img.get('data-src')  # Some sites use lazy loading
                        
                        if not img_url:
                            logger.warning(f"Could not find URL for image {i+1} on page {page_count}")
                            continue
                        
                        # Skip duplicate images
                        if img_url in previous_page_images[-duplicate_threshold:]:
                            logger.info(f"Skipping duplicate image: {img_url}")
                            continue
                            
                        # Apply CDN regex replacement if needed
                        img_url = re.sub(BAOZI_CDN_REGEX, BAOZI_CDN_REPLACEMENT, img_url)
                        
                        # Download the image
                        try:
                            img_response = requests.get(img_url, headers=self.headers, timeout=15)
                            img_response.raise_for_status()
                            
                            # Create image from binary data
                            img_data = Image.open(io.BytesIO(img_response.content))
                            page_images.append(img_data)
                            previous_page_images.append(img_url)  # Add to previous images for duplicate detection
                            logger.info(f"Downloaded image {i+1}/{len(image_elements)} from page {page_count}")
                        except Exception as e:
                            logger.error(f"Error downloading image {i+1} from page {page_count}: {e}")
                    
                    # Add page images to all images
                    all_images.extend(page_images)
                    
                    # Look for next page button/link
                    next_page_url = None
                    
                    # Method 1: Look for pagination elements with "next" or "下一页" text
                    pagination_elements = soup.find_all(['a', 'button', 'div'], class_=lambda c: c and any(x in c.lower() for x in ['pag', 'next', 'nav']))
                    for element in pagination_elements:
                        element_text = element.get_text(strip=True).lower()
                        if any(x in element_text for x in ['next', '下一页', '下一張', '下一章', '下一節']):
                            if element.name == 'a' and element.get('href'):
                                next_page_url = element['href']
                                if not next_page_url.startswith('http'):
                                    next_page_url = f"{'/'.join(current_url.split('/')[:3])}{next_page_url}"
                                break
                    
                    # Method 2: Look for JavaScript pagination functions
                    if not next_page_url:
                        onclick_elements = soup.find_all(attrs={"onclick": True})
                        for element in onclick_elements:
                            onclick = element.get('onclick', '')
                            if any(x in onclick.lower() for x in ['next', 'page', 'load']):
                                # Extract page number from onclick attribute if possible
                                page_match = re.search(r'page=([0-9]+)', onclick)
                                if page_match:
                                    page_num = page_match.group(1)
                                    # Construct next page URL
                                    if '?' in current_url:
                                        next_page_url = re.sub(r'page=[0-9]+', f'page={page_num}', current_url)
                                        if next_page_url == current_url:  # If no substitution happened
                                            next_page_url = f"{current_url}&page={page_num}"
                                    else:
                                        next_page_url = f"{current_url}?page={page_num}"
                                    break
                    
                    # Method 3: Check for URL patterns with page numbers
                    if not next_page_url and page_count == 1:
                        # Try common pagination URL patterns for the second page
                        potential_patterns = [
                            f"{current_url}?page=2",
                            f"{current_url}&page=2",
                            re.sub(r'(\d+)$', lambda m: str(int(m.group(1)) + 1), current_url)
                        ]
                        
                        for pattern in potential_patterns:
                            try:
                                test_response = requests.head(pattern, headers=self.headers, timeout=5)
                                if test_response.status_code == 200:
                                    next_page_url = pattern
                                    break
                            except:
                                continue
                    
                    # If no next page found or no new images on this page, stop pagination
                    if not next_page_url or not page_images:
                        logger.info(f"No next page found or no new images on page {page_count}. Stopping pagination.")
                        break
                    
                    # Move to next page
                    current_url = next_page_url
                    page_count += 1
                    
                    # Add a small delay between page requests to avoid overloading the server
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing page {page_count}: {e}")
                    break
            
            logger.info(f"Finished downloading chapter. Total pages processed: {page_count}, total images: {len(all_images)}")
            return all_images
        
        except Exception as e:
            logger.error(f"Error downloading chapter images: {e}")
            return []


class TwmangaAdapter(MangaSiteAdapter):
    """Adapter for twmanga.com"""
    
    def get_latest_chapter(self):
        """Fetches the given comic URL and extracts the latest chapter information"""
        logger.info(f"Fetching URL: {self.url}")
        try:
            response = requests.get(self.url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the chapter list container
            chapter_list = soup.find('ul', class_='chapter-list')
            if not chapter_list:
                logger.error("Could not find chapter list on the page")
                return None, None

            # Find all chapter links
            chapter_links = chapter_list.find_all('a')
            if not chapter_links:
                logger.error("No chapter links found within the chapter list")
                return None, None

            # Get the latest chapter (usually the first one)
            latest_chapter_element = chapter_links[0]
            latest_chapter_text = latest_chapter_element.get_text(strip=True)
            latest_chapter_url = latest_chapter_element['href']
            if not latest_chapter_url.startswith('http'):
                latest_chapter_url = f"https://www.twmanga.com{latest_chapter_url}"
                
            logger.info(f"Found raw latest chapter text: '{latest_chapter_text}', URL: {latest_chapter_url}")

            chapter_name = self.extract_chapter_number(latest_chapter_text)
            return chapter_name, latest_chapter_url

        except requests.exceptions.Timeout:
            logger.error(f"Timeout error fetching {self.url}. The server might be slow or unresponsive.")
            return None, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {self.url}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"An unexpected error occurred during scraping {self.url}: {e}")
            return None, None
    
    def download_chapter_images(self, chapter_url):
        """Download all images from a chapter page, including pagination support"""
        logger.info(f"Downloading images from: {chapter_url}")
        try:
            # Initialize variables for pagination
            all_images = []
            current_url = chapter_url
            page_count = 1
            max_pages = 20  # Safety limit to prevent infinite loops
            previous_page_images = []  # For duplicate detection
            duplicate_threshold = 4  # Number of last images to check for duplicates
            
            while page_count <= max_pages:
                logger.info(f"Processing page {page_count} of chapter: {current_url}")
                
                try:
                    page_response = requests.get(current_url, headers=self.headers, timeout=15)
                    page_response.raise_for_status()
                    soup = BeautifulSoup(page_response.text, 'html.parser')
                    
                    # Find all image elements (twmanga uses amp-img tags with comic-contain__item class)
                    image_elements = soup.find_all('amp-img', class_='comic-contain__item')
                    if not image_elements:
                        logger.error(f"No images found on page {page_count}")
                        break
                    
                    # Process images on current page
                    page_images = []
                    for i, img in enumerate(image_elements):
                        img_url = img.get('src')
                        if not img_url:
                            logger.warning(f"Could not find URL for image {i+1} on page {page_count}")
                            continue
                        
                        # Skip duplicate images
                        if img_url in previous_page_images[-duplicate_threshold:]:
                            logger.info(f"Skipping duplicate image: {img_url}")
                            continue
                        
                        # Download the image
                        try:
                            img_response = requests.get(img_url, headers=self.headers, timeout=15)
                            img_response.raise_for_status()
                            
                            # Create image from binary data
                            img_data = Image.open(io.BytesIO(img_response.content))
                            page_images.append(img_data)
                            previous_page_images.append(img_url)  # Add to previous images for duplicate detection
                            logger.info(f"Downloaded image {i+1}/{len(image_elements)} from page {page_count}")
                        except Exception as e:
                            logger.error(f"Error downloading image {i+1} from page {page_count}: {e}")
                    
                    # Add page images to all images
                    all_images.extend(page_images)
                    
                    # Look for next page button/link
                    next_page_url = None
                    
                    # Method 1: Look for pagination elements with "next" or "下一页" text
                    pagination_elements = soup.find_all(['a', 'button', 'div'], class_=lambda c: c and any(x in c.lower() for x in ['pag', 'next', 'nav']))
                    for element in pagination_elements:
                        element_text = element.get_text(strip=True).lower()
                        if any(x in element_text for x in ['next', '下一页', '下一张', '下一章', '下一节']):
                            if element.name == 'a' and element.get('href'):
                                next_page_url = element['href']
                                if not next_page_url.startswith('http'):
                                    next_page_url = f"{'/'.join(current_url.split('/')[:3])}{next_page_url}"
                                break
                    
                    # Method 2: Look for AMP pagination elements (specific to twmanga)
                    if not next_page_url:
                        amp_pagination = soup.find('amp-pagination')
                        if amp_pagination:
                            next_button = amp_pagination.find('button', {'pagination-item-next': True})
                            if next_button and not next_button.get('disabled'):
                                # Extract page number if possible
                                current_page_num = int(page_count)
                                next_page_num = current_page_num + 1
                                
                                # Construct next page URL
                                if '?' in current_url:
                                    next_page_url = re.sub(r'page=[0-9]+', f'page={next_page_num}', current_url)
                                    if next_page_url == current_url:  # If no substitution happened
                                        next_page_url = f"{current_url}&page={next_page_num}"
                                else:
                                    next_page_url = f"{current_url}?page={next_page_num}"
                    
                    # Method 3: Look for JavaScript pagination functions
                    if not next_page_url:
                        onclick_elements = soup.find_all(attrs={"onclick": True})
                        for element in onclick_elements:
                            onclick = element.get('onclick', '')
                            if any(x in onclick.lower() for x in ['next', 'page', 'load']):
                                # Extract page number from onclick attribute if possible
                                page_match = re.search(r'page=([0-9]+)', onclick)
                                if page_match:
                                    page_num = page_match.group(1)
                                    # Construct next page URL
                                    if '?' in current_url:
                                        next_page_url = re.sub(r'page=[0-9]+', f'page={page_num}', current_url)
                                        if next_page_url == current_url:  # If no substitution happened
                                            next_page_url = f"{current_url}&page={page_num}"
                                    else:
                                        next_page_url = f"{current_url}?page={page_num}"
                                    break
                    
                    # Method 4: Check for URL patterns with page numbers
                    if not next_page_url and page_count == 1:
                        # Try common pagination URL patterns for the second page
                        potential_patterns = [
                            f"{current_url}?page=2",
                            f"{current_url}&page=2",
                            re.sub(r'(\d+)$', lambda m: str(int(m.group(1)) + 1), current_url)
                        ]
                        
                        for pattern in potential_patterns:
                            try:
                                test_response = requests.head(pattern, headers=self.headers, timeout=5)
                                if test_response.status_code == 200:
                                    next_page_url = pattern
                                    break
                            except:
                                continue
                    
                    # If no next page found or no new images on this page, stop pagination
                    if not next_page_url or not page_images:
                        logger.info(f"No next page found or no new images on page {page_count}. Stopping pagination.")
                        break
                    
                    # Move to next page
                    current_url = next_page_url
                    page_count += 1
                    
                    # Add a small delay between page requests to avoid overloading the server
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing page {page_count}: {e}")
                    break
            
            logger.info(f"Finished downloading chapter. Total pages processed: {page_count}, total images: {len(all_images)}")
            return all_images
        
        except Exception as e:
            logger.error(f"Error downloading chapter images: {e}")
            return []


def get_site_adapter(comic):
    """Get the appropriate site adapter based on the comic's URL or site field"""
    if 'site' in comic and comic['site'] in SUPPORTED_SITES:
        site = comic['site']
    else:
        # Auto-detect site from URL
        if 'baozimh.com' in comic['url']:
            site = 'baozimh'
        elif 'twmanga.com' in comic['url']:
            site = 'twmanga'
        else:
            logger.error(f"Unsupported site for URL: {comic['url']}")
            return None
    
    # Create and return the appropriate adapter
    if site == 'baozimh':
        return BaozimhAdapter(comic['url'])
    elif site == 'twmanga':
        return TwmangaAdapter(comic['url'])
    else:
        logger.error(f"No adapter available for site: {site}")
        return None


def get_latest_chapter(comic_url):
    """Legacy function for backward compatibility"""
    adapter = BaozimhAdapter(comic_url)
    return adapter.get_latest_chapter()


def download_chapter_images(chapter_url):
    """Legacy function for backward compatibility"""
    # Determine which adapter to use based on the URL
    if 'baozimh.com' in chapter_url:
        adapter = BaozimhAdapter(chapter_url)
    elif 'twmanga.com' in chapter_url:
        adapter = TwmangaAdapter(chapter_url)
    else:
        logger.error(f"Unsupported site for URL: {chapter_url}")
        return []
    
    return adapter.download_chapter_images(chapter_url)

# ===== Image Processing Functions

def stitch_images(images, target_width=None, target_height=None):
    """Stitch multiple images vertically into a single image or multiple images if needed"""
    if not images:
        logger.error("No images to stitch")
        return None
    
    settings = load_settings()
    if not target_width:
        target_width = settings["image_width"]
    if not target_height:
        target_height = settings["image_height"]
    
    try:
        # Import the multi-page stitcher functions
        from stitcher import stitch_images_multi_page
        
        # Use the multi-page stitcher with the max_height from settings
        max_height = target_height if target_height > 0 else 12000
        stitched_images = stitch_images_multi_page(images, target_width, max_height)
        
        # Return the first image for backward compatibility
        if stitched_images and len(stitched_images) > 0:
            return stitched_images[0]
        else:
            return None
    
    except ImportError:
        logger.warning("Could not import multi-page stitcher, falling back to single-page stitching")
        try:
            # Calculate dimensions
            if target_width <= 0:
                target_width = max(img.width for img in images)
            
            # Calculate height based on aspect ratio if target_height is 0
            heights = []
            for img in images:
                aspect_ratio = img.height / img.width
                new_height = int(target_width * aspect_ratio)
                heights.append(new_height)
            
            total_height = sum(heights)
            
            # If target_height is specified and not 0, use it to scale the total height
            if target_height > 0:
                scale_factor = target_height / total_height
                total_height = target_height
                heights = [int(h * scale_factor) for h in heights]
            
            # Create a new blank image
            stitched_img = Image.new('RGB', (target_width, total_height), (255, 255, 255))
            
            # Paste each image
            y_offset = 0
            for i, img in enumerate(images):
                # Resize the image to fit the target width while maintaining aspect ratio
                resized_img = img.resize((target_width, heights[i]), Image.LANCZOS)
                stitched_img.paste(resized_img, (0, y_offset))
                y_offset += heights[i]
            
            return stitched_img
        
        except Exception as e:
            logger.error(f"Error stitching images: {e}")
            return None
    
    except Exception as e:
        logger.error(f"Error stitching images: {e}")
        return None

def remove_image_parts(image, template_image, threshold=0.8):
    """Remove parts of an image that match a template image"""
    try:
        # Convert PIL images to numpy arrays for processing
        img_array = np.array(image)
        template_array = np.array(template_image)
        
        # Convert to grayscale for template matching
        img_gray = np.mean(img_array, axis=2).astype(np.uint8)
        template_gray = np.mean(template_array, axis=2).astype(np.uint8)
        
        # Get template dimensions
        h, w = template_gray.shape
        
        # Perform template matching
        result = np.zeros_like(img_gray)
        for y in range(img_gray.shape[0] - h + 1):
            for x in range(img_gray.shape[1] - w + 1):
                # Extract region of interest
                roi = img_gray[y:y+h, x:x+w]
                
                # Calculate normalized cross-correlation
                correlation = np.sum((roi - np.mean(roi)) * (template_gray - np.mean(template_gray))) / \
                              (np.std(roi) * np.std(template_gray) * roi.size)
                
                if correlation > threshold:
                    # Create a white rectangle to cover the matched area
                    img_array[y:y+h, x:x+w] = [255, 255, 255]
        
        # Convert back to PIL image
        processed_image = Image.fromarray(img_array)
        return processed_image
    
    except Exception as e:
        logger.error(f"Error removing image parts: {e}")
        return image  # Return original image if processing fails

# ===== Main Bot Logic =====

def process_comic(comic, tracked_comics, comic_index):
    """Process a single comic: check for new chapters, download, process, and upload"""
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
            template = Image.open(comic['template_image'])
            processed_images = []
            
            for img in images:
                processed_img = remove_image_parts(img, template)
                processed_images.append(processed_img)
            
            images = processed_images
        except Exception as e:
            logger.error(f"Error processing images with template: {e}")
    
    # Import multi-page stitcher functions
    try:
        from stitcher import stitch_images_multi_page, save_stitched_images
        
        # Get image dimensions from settings
        target_width = settings.get("image_width", 0)
        max_height = settings.get("image_height", 12000)  # Use image_height as max_height
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
        
        # Create a zip file containing all stitched images
        zip_filename = os.path.join(processed_dir, f"{safe_chapter}.zip")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for file_path in saved_files:
                # Add file to zip with just the filename (not the full path)
                zipf.write(file_path, os.path.basename(file_path))
        
        logger.info(f"Created zip archive of all stitched images: {zip_filename}")
        
        # Upload to Google Drive if enabled
        drive_links = []
        if settings["upload_to_drive"]:
            # Create a folder for the chapter in Google Drive
            chapter_folder_name = f"{comic['name']}/{safe_chapter}"
            # Upload the zip file to the chapter folder
            drive_link = upload_to_drive(zip_filename, f"Chaptrix/{chapter_folder_name}")
            if drive_link:
                drive_links.append(drive_link)
    
    except ImportError:
        # Fall back to original method if stitcher module is not available
        logger.warning("Could not import multi-page stitcher, falling back to single-page stitching")
        
        # Stitch images
        stitched_image = stitch_images(images)
        if not stitched_image:
            logger.error(f"Failed to stitch images for {comic['name']} chapter {current_chapter}")
            return False
        
        # Save processed image
        safe_chapter = current_chapter.replace('/', '_').replace('\\', '_')
        processed_file = os.path.join(processed_dir, f"{safe_chapter}.jpg")
        stitched_image.save(processed_file, "JPEG", quality=settings.get("image_quality", 90))
        logger.info(f"Saved processed image to {processed_file}")
        
        # Create a zip file containing the stitched image
        zip_filename = os.path.join(processed_dir, f"{safe_chapter}.zip")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            zipf.write(processed_file, os.path.basename(processed_file))
        
        logger.info(f"Created zip archive of stitched image: {zip_filename}")
        
        # For compatibility with the rest of the function
        saved_files = [processed_file]
        
        # Upload to Google Drive if enabled
        drive_links = []
        if settings["upload_to_drive"]:
            # Create a folder for the chapter in Google Drive
            chapter_folder_name = f"{comic['name']}/{safe_chapter}"
            # Upload the zip file to the chapter folder
            drive_link = upload_to_drive(zip_filename, f"Chaptrix/{chapter_folder_name}")
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
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    # Add Drive links if available
    if drive_links:
        embed["fields"].append({
            "name": "Download Complete Chapter",
            "value": f"[Google Drive Link]({drive_links[0]})",
            "inline": False
        })
    
    # Send Discord notification if enabled
    if settings["upload_to_discord"]:
        message_content = f"Hey everyone! A new chapter for **{comic['name']}** is out!"
        
        # Send the zip file with the embed
        if 'zip_filename' in locals() and os.path.exists(zip_filename):
            send_discord_notification(message_content, embed, zip_filename)
        else:
            # Fallback to sending the first image if zip file doesn't exist
            if 'saved_files' in locals() and len(saved_files) > 0:
                send_discord_notification(message_content, embed, saved_files[0])
            else:
                # Just send the message without any attachment
                send_discord_notification(message_content, embed)
    
    # Update comic's last known chapter
    tracked_comics[comic_index]['last_known_chapter'] = current_chapter
    return True

def main_check_loop():
    """Main function to check all comics for updates"""
    logger.info("Bot started. Loading tracked comics...")
    tracked_comics = load_tracked_comics()
    settings = load_settings()
    
    if not tracked_comics:
        logger.warning("No comics tracked. Please add some to comics.json.")
        logger.info("Example format for comics.json (replace with your comic details):")
        logger.info("""
[
    {
        "name": "My Favorite Manga",
        "url": "https://www.baozimh.com/comic/your-comic-slug-here",
        "site": "baozimh",  # Optional, will auto-detect if not provided
        "last_known_chapter": "Chapter 0",
        "template_image": "templates/baozimh_logo_template.svg"  # Optional
    }
]
        """)
        return {"total": 0, "new": 0}
    
    logger.info(f"Checking {len(tracked_comics)} comics for new chapters...")
    total_checked = 0
    new_chapters = 0
    
    for comic in tracked_comics:
        try:
            # Skip comics from disabled site adapters
            site = None
            if 'site' in comic and comic['site'] in settings['site_adapters']:
                site = comic['site']
                if not settings['site_adapters'][site]['enabled']:
                    logger.info(f"Skipping {comic['name']} - site adapter {site} is disabled")
                    continue
            else:
                # Auto-detect site from URL
                if 'baozimh.com' in comic['url']:
                    site = 'baozimh'
                elif 'twmanga.com' in comic['url']:
                    site = 'twmanga'
                
                if site and not settings['site_adapters'][site]['enabled']:
                    logger.info(f"Skipping {comic['name']} - auto-detected site adapter {site} is disabled")
                    continue
            
            total_checked += 1
            if process_comic(comic, tracked_comics, tracked_comics.index(comic)): # Pass tracked_comics and index
                new_chapters += 1
        except Exception as e:
            logger.error(f"Error processing comic {comic['name']}: {e}")
    
    # Save the updated comics data
    save_tracked_comics(tracked_comics)
    
    logger.info("Finished checking all tracked comics.")
    return {"total": total_checked, "new": new_chapters}

# ===== Streamlit Dashboard =====

def run_dashboard():
    """Run the Streamlit dashboard for managing comics and settings"""
    st.set_page_config(page_title="Chaptrix Dashboard", page_icon="assets/logo.ico")
    
    # Load data
    settings = load_settings()
    comics = load_tracked_comics()
    
    # Display header
    st.image("assets/banner.png", use_column_width=True)
    st.title("Chaptrix - Manga Chapter Manager")
    
    # Sidebar navigation
    page = st.sidebar.radio("Navigation", ["Comics", "Settings", "Run Bot", "About"])
    
    if page == "Comics":
        st.header("Manage Comics")
        
        # Add new comic form
        with st.expander("Add New Comic", expanded=False):
            with st.form("add_comic_form"):
                new_name = st.text_input("Comic Name (English)", "")
                new_url = st.text_input("Comic URL", "https://www.baozimh.com/comic/")
                
                # Site selection
                site_options = ["Auto-detect"] + list(SUPPORTED_SITES.keys())
                site_index = st.selectbox("Manga Site", options=site_options, index=0)
                
                # Get site key from selection
                site_key = site_options[site_index] if site_index > 0 else "auto"
                
                new_template = st.file_uploader("Upload template image for parts to remove (optional)", type=["png", "jpg", "jpeg"])
                
                submitted = st.form_submit_button("Add Comic")
                if submitted and new_name and new_url:
                    # Save template image if provided
                    template_path = None
                    if new_template:
                        os.makedirs("templates", exist_ok=True)
                        template_path = f"templates/{new_name.replace('/', '_')}_template.png"
                        with open(template_path, "wb") as f:
                            f.write(new_template.getvalue())
                    
                    # Add new comic
                    new_comic = {
                        "name": new_name,
                        "url": new_url,
                        "last_known_chapter": "Chapter 0",
                    }
                    
                    # Add site if not auto-detect
                    if site_key != "auto":
                        new_comic["site"] = site_key
                        
                    if template_path:
                        new_comic["template_image"] = template_path
                        
                    comics.append(new_comic)
                    save_tracked_comics(comics)
                    st.success(f"Added {new_name} to tracked comics!")
                    st.experimental_rerun()
        
        # List and manage existing comics
        if not comics:
            st.info("No comics tracked yet. Add your first comic above.")
        else:
            for i, comic in enumerate(comics):
                with st.expander(f"{i+1}. {comic['name']} - {comic['last_known_chapter']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**URL:** {comic['url']}")
                        
                        # Display site information
                        site = comic.get('site', 'auto')
                        if site == 'auto':
                            # Auto-detect site from URL
                            if 'baozimh.com' in comic['url']:
                                site_name = "baozimh"
                            elif 'twmanga.com' in comic['url']:
                                site_name = "twmanga"
                            else:
                                site_name = "Unknown"
                            st.write(f"**Site:** {site_name} (auto-detected)")
                        else:
                            st.write(f"**Site:** {site}")
                        
                        if 'template_image' in comic and comic['template_image']:
                            st.write(f"**Template:** {comic['template_image']}")
                            if os.path.exists(comic['template_image']):
                                st.image(comic['template_image'], width=200)
                    
                    with col2:
                        # Edit comic
                        new_name = st.text_input(f"Rename {comic['name']}", comic['name'], key=f"rename_{i}")
                        new_url = st.text_input(f"Update URL", comic['url'], key=f"url_{i}")
                        
                        # Site selection for editing
                        current_site = comic.get('site', 'auto')
                        site_options = ["Auto-detect"] + list(SUPPORTED_SITES.keys())
                        current_site_index = site_options.index(current_site) if current_site in site_options else 0
                        site_index = st.selectbox(f"Manga Site", options=site_options, index=current_site_index, key=f"site_{i}")
                        site_key = site_options[site_index] if site_index > 0 else "auto"
                        
                        new_template = st.file_uploader(f"Update template", type=["png", "jpg", "jpeg"], key=f"template_{i}")
                        
                        if st.button(f"Update", key=f"update_{i}"):
                            if new_template:
                                os.makedirs("templates", exist_ok=True)
                                template_path = f"templates/{new_name.replace('/', '_')}_template.png"
                                with open(template_path, "wb") as f:
                                    f.write(new_template.getvalue())
                                comic['template_image'] = template_path
                            
                            comic['name'] = new_name
                            comic['url'] = new_url
                            
                            # Update site if not auto-detect
                            if site_key != "auto":
                                comic["site"] = site_key
                            elif "site" in comic:
                                del comic["site"]  # Remove site if auto-detect is selected
                                
                            save_tracked_comics(comics)
                            st.success("Comic updated!")
                            st.experimental_rerun()
                        
                        if st.button(f"Delete", key=f"delete_{i}"):
                            comics.pop(i)
                            save_tracked_comics(comics)
                            st.success("Comic deleted!")
                            st.experimental_rerun()
                        
                        if st.button(f"Check Now", key=f"check_{i}"):
                            with st.spinner(f"Checking {comic['name']}..."):
                                if process_comic(comic):
                                    save_tracked_comics(comics)
                                    st.success(f"Found and processed new chapter: {comic['last_known_chapter']}")
                                else:
                                    st.info(f"No new chapter found. Still at {comic['last_known_chapter']}")
    
    elif page == "Settings":
        st.header("Settings")
        
        with st.form("settings_form"):
            # General settings
            st.subheader("General Settings")
            check_interval = st.number_input("Check Interval (seconds)", min_value=300, value=settings["check_interval"])
            download_path = st.text_input("Download Path", settings["download_path"])
            processed_path = st.text_input("Processed Path", settings["processed_path"])
            
            # Image processing settings
            st.subheader("Image Processing")
            image_width = st.number_input("Image Width (px, 0 for auto)", min_value=0, value=settings["image_width"])
            image_height = st.number_input("Image Height (px, 0 for auto)", min_value=0, value=settings["image_height"])
            
            # Upload settings
            st.subheader("Upload Settings")
            upload_to_drive = st.checkbox("Upload to Google Drive", settings["upload_to_drive"])
            upload_to_discord = st.checkbox("Upload to Discord", settings["upload_to_discord"])
            
            # Discord settings
            st.subheader("Discord Settings")
            discord_webhook_url = st.text_input("Discord Webhook URL", settings["discord_webhook_url"])
            discord_bot_token = st.text_input("Discord Bot Token (optional)", settings["discord_bot_token"])
            discord_channel_id = st.text_input("Discord Channel ID (optional)", settings["discord_channel_id"])
            
            # Save settings
            submitted = st.form_submit_button("Save Settings")
            if submitted:
                new_settings = {
                    "check_interval": check_interval,
                    "image_width": image_width,
                    "image_height": image_height,
                    "upload_to_drive": upload_to_drive,
                    "upload_to_discord": upload_to_discord,
                    "download_path": download_path,
                    "processed_path": processed_path,
                    "discord_webhook_url": discord_webhook_url,
                    "discord_bot_token": discord_bot_token,
                    "discord_channel_id": discord_channel_id
                }
                save_settings(new_settings)
                st.success("Settings saved!")
        
        # Google Drive setup
        st.subheader("Google Drive Setup")
        if not os.path.exists(CREDENTIALS_FILE):
            st.warning("Google Drive credentials file not found. Please upload your credentials.json file.")
            credentials_file = st.file_uploader("Upload credentials.json", type=["json"])
            if credentials_file:
                with open(CREDENTIALS_FILE, "wb") as f:
                    f.write(credentials_file.getvalue())
                st.success("Credentials file uploaded!")
        else:
            st.info("Google Drive credentials file found.")
            if st.button("Authenticate Google Drive"):
                with st.spinner("Authenticating with Google Drive..."):
                    service = get_drive_service()
                    if service:
                        st.success("Google Drive authentication successful!")
                    else:
                        st.error("Google Drive authentication failed. Please check your credentials.")
    
    elif page == "Run Bot":
        st.header("Run Bot")
        
        if st.button("Check All Comics Now"):
            with st.spinner("Checking all comics for updates..."):
                main_check_loop()
                st.success("Check completed!")
        
        st.subheader("Schedule Bot")
        st.info("For automated scheduling, you can use GitHub Actions or set up a cron job on your server.")
        
        # Display GitHub Actions workflow example
        st.code("""
# Example GitHub Actions workflow (save as .github/workflows/check-comics.yml)

name: Check Comics

on:
  schedule:
    - cron: '0 */4 * * *'  # Run every 4 hours
  workflow_dispatch:  # Allow manual triggering

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run bot
        env:
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
        run: python main.py
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add comics.json
          git commit -m "Update comics data" || echo "No changes to commit"
          git push
        """, language="yaml")
    
    elif page == "About":
        st.header("About Chaptrix")
        st.write("""
        Chaptrix is a manga chapter notification and download bot that helps you keep track of your favorite manga series.
        
        ### Features
        - Track multiple manga series from different sites
        - Automatically check for new chapters
        - Download and stitch chapter images
        - Remove watermarks and ads with template matching
        - Upload processed chapters to Google Drive
        - Send notifications via Discord
        """)
        
        # Display supported sites
        st.subheader("Supported Manga Sites")
        for site_key, site_info in SUPPORTED_SITES.items():
            st.write(f"**{site_info['name']}**")
            st.write(f"- Base URL: {site_info['url']}")
            st.write(f"- Template: {site_info['template']}")
            st.write("")
        
        st.write("""
        ### How to Use
        1. Add manga series to track in the 'Manage Comics' tab
        2. Configure your settings in the 'Settings' tab
        3. Set up Google Drive integration in the 'Google Drive Setup' tab (optional)
        4. Run the bot regularly to check for updates
        
        ### Scheduling
        For automatic checking, you can:
        - Use the Windows Task Scheduler to run `python main.py --check` at regular intervals
        - Set up a cron job on Linux/macOS
        - Use GitHub Actions for cloud-based checking
        
        Example GitHub Actions workflow:
        ```yaml
        name: Check Comics
        on:
          schedule:
            - cron: '0 */4 * * *'  # Run every 4 hours
          workflow_dispatch:  # Allow manual triggering
        
        jobs:
          check:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v2
              - name: Set up Python
                uses: actions/setup-python@v2
                with:
                  python-version: '3.9'
              - name: Install dependencies
                run: pip install -r requirements.txt
              - name: Run check
                run: python main.py --check
        ```
        
        ### Credits
        Created by AI Assistant
        
        Version 1.0.0
        """)
        
        # Display a sample image
        st.image("https://i.imgur.com/XqLQ5oC.png", caption="Sample manga page processing", use_column_width=True)

# ===== Main Execution =====

def main():
    """Main entry point for the application"""
    # Create necessary directories
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("processed", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Manga Chapter Notification Bot")
    parser.add_argument("--check", action="store_true", help="Check for new chapters")
    parser.add_argument("--dashboard", action="store_true", help="Run the Streamlit dashboard")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--disable-site", type=str, help="Disable a specific site adapter (e.g., baozimh, twmanga)")
    parser.add_argument("--enable-site", type=str, help="Enable a specific site adapter (e.g., baozimh, twmanga)")
    parser.add_argument("--list-sites", action="store_true", help="List all available site adapters and their status")
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    settings = load_settings()
    
    if args.disable_site:
        site = args.disable_site.lower()
        if site in settings['site_adapters']:
            settings['site_adapters'][site]['enabled'] = False
            save_settings(settings)