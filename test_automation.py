#!/usr/bin/env python3

"""
Test script for Chaptrix automation

This script verifies that all components required for automation are working correctly.
It tests:
1. Environment variable access
2. Google Drive API connectivity
3. Discord webhook/bot connectivity
4. Basic image processing functionality

Run this script before setting up GitHub Actions to ensure everything will work.
"""

import os
import sys
import json
import logging
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import time
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('chaptrix_test')

# Load environment variables
load_dotenv()

def check_environment():
    """Check if required environment variables are set"""
    logger.info("Checking environment variables...")
    
    # Check Discord configuration
    discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
    discord_bot_token = os.getenv('DISCORD_BOT_TOKEN')
    discord_channel_id = os.getenv('DISCORD_CHANNEL_ID')
    
    if not discord_webhook and not (discord_bot_token and discord_channel_id):
        logger.warning("No Discord configuration found. Discord notifications will be disabled.")
        # Continue execution even without Discord credentials
        # return False
    
    # Check if we're running in GitHub Actions
    if os.getenv('GITHUB_ACTIONS') == 'true':
        logger.info("Running in GitHub Actions environment")
    else:
        logger.info("Running in local environment")
    
    return True

def check_google_drive():
    """Check Google Drive API connectivity"""
    logger.info("Checking Google Drive connectivity...")
    
    try:
        # Try to import Google API libraries
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        
        # Check for credentials file
        if os.path.exists('credentials.json'):
            logger.info("Found credentials.json file")
            
            # Try to authenticate
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            creds = None
            
            # Check if we're using service account (for automation)
            if os.path.getsize('credentials.json') > 0:
                try:
                    # First try as service account
                    creds = service_account.Credentials.from_service_account_file(
                        'credentials.json', scopes=SCOPES)
                    logger.info("Successfully loaded service account credentials")
                except Exception:
                    # If that fails, try as OAuth credentials
                    if os.path.exists('token.json'):
                        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                        logger.info("Successfully loaded OAuth token")
                    else:
                        logger.warning("No token.json found for OAuth authentication")
                        return False
            
            # Build the Drive API client
            if creds:
                try:
                    service = build('drive', 'v3', credentials=creds)
                    # Test API with a simple request
                    results = service.files().list(pageSize=1).execute()
                    logger.info("Successfully connected to Google Drive API")
                    return True
                except Exception as e:
                    logger.error(f"Error connecting to Google Drive API: {e}")
                    return False
        else:
            logger.warning("No credentials.json file found")
            return False
            
    except ImportError:
        logger.error("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False

def check_discord():
    """Check Discord connectivity"""
    logger.info("Checking Discord connectivity...")
    
    # Check if Discord credentials are available
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    channel_id = os.getenv('DISCORD_CHANNEL_ID')
    
    if not webhook_url and not (bot_token and channel_id):
        logger.warning("No Discord credentials found. Skipping Discord connectivity test.")
        # Return True to allow the automation to continue without Discord
        return True
    
    # Create a test image
    img = Image.new('RGB', (400, 200), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    
    # Try to add text (with fallback if font not available)
    try:
        font = ImageFont.truetype("arial.ttf", 15)
        d.text((10, 10), "Chaptrix Automation Test\nIf you can see this, Discord integration is working!", fill=(255, 255, 0), font=font)
    except IOError:
        d.text((10, 10), "Chaptrix Automation Test\nIf you can see this, Discord integration is working!", fill=(255, 255, 0))
    
    # Save image to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # Try webhook method first
    if webhook_url:
        try:
            files = {'file': ('test.png', img_byte_arr, 'image/png')}
            payload = {"content": "Chaptrix automation test - webhook method"}
            response = requests.post(webhook_url, files=files, data=payload)
            
            if response.status_code == 200:
                logger.info("Successfully sent test message via Discord webhook")
                return True
            else:
                logger.error(f"Failed to send Discord webhook: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error sending Discord webhook: {e}")
    
    # Try bot method if webhook failed or not configured
    if bot_token and channel_id:
        try:
            import discord
            import asyncio
            
            async def send_test_message():
                intents = discord.Intents.default()
                intents.message_content = True
                client = discord.Client(intents=intents)
                
                @client.event
                async def on_ready():
                    try:
                        channel = client.get_channel(int(channel_id))
                        if not channel:
                            logger.error(f"Could not find channel with ID {channel_id}")
                            await client.close()
                            return False
                        
                        img_byte_arr.seek(0)  # Reset position
                        discord_file = discord.File(fp=img_byte_arr, filename="test.png")
                        await channel.send(content="Chaptrix automation test - bot method", file=discord_file)
                        logger.info("Successfully sent test message via Discord bot")
                        await client.close()
                        return True
                    except Exception as e:
                        logger.error(f"Error in Discord bot: {e}")
                        await client.close()
                        return False
                
                try:
                    await client.start(bot_token)
                except Exception as e:
                    logger.error(f"Failed to start Discord bot: {e}")
                    return False
            
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(send_test_message())
            return result
            
        except ImportError:
            logger.error("Discord.py not installed. Run: pip install discord.py")
            return False
    
    logger.warning("Discord credentials found but all connection attempts failed")
    # Return False only if credentials were provided but connection failed
    return False

def check_image_processing():
    """Test basic image processing functionality"""
    logger.info("Testing image processing...")
    
    try:
        # Create test images
        test_dir = os.path.join(os.getcwd(), "test_automation")
        os.makedirs(test_dir, exist_ok=True)
        
        # Create 3 test images
        for i in range(1, 4):
            img = Image.new('RGB', (800, 1200), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            
            # Add some text and shapes to make each image unique
            try:
                font = ImageFont.truetype("arial.ttf", 30)
                d.text((100, 100), f"Test Image {i}", fill=(0, 0, 0), font=font)
            except IOError:
                d.text((100, 100), f"Test Image {i}", fill=(0, 0, 0))
                
            # Draw different shapes on each image
            if i == 1:
                d.rectangle([(200, 300), (600, 700)], outline=(255, 0, 0), width=5)
            elif i == 2:
                d.ellipse([(200, 300), (600, 700)], outline=(0, 255, 0), width=5)
            else:
                d.polygon([(400, 300), (200, 700), (600, 700)], outline=(0, 0, 255), width=5)
            
            # Save the image
            img_path = os.path.join(test_dir, f"{i}.jpg")
            img.save(img_path, "JPEG")
            logger.info(f"Created test image: {img_path}")
        
        # Import stitcher and test stitching
        try:
            from stitcher import stitch_images_multi_page, save_stitched_images
            
            # Get list of image paths
            image_paths = [os.path.join(test_dir, f"{i}.jpg") for i in range(1, 4)]
            
            # Stitch images
            stitched_images = stitch_images_multi_page(image_paths, 800, 0)
            
            # Save stitched images
            output_dir = os.path.join(test_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            save_stitched_images(stitched_images, output_dir)
            
            # Check if output files exist
            output_files = os.listdir(output_dir)
            if output_files:
                logger.info(f"Successfully stitched and saved images: {output_files}")
                return True
            else:
                logger.error("No output files generated from stitcher")
                return False
                
        except ImportError:
            logger.error("Could not import stitcher module")
            return False
        except Exception as e:
            logger.error(f"Error in image stitching: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error in image processing test: {e}")
        return False

def main():
    """Run all tests and report results"""
    logger.info("Starting Chaptrix automation test")
    
    results = {
        "environment": check_environment(),
        "google_drive": check_google_drive(),
        "discord": check_discord(),
        "image_processing": check_image_processing()
    }
    
    # Print summary
    logger.info("\n===== TEST RESULTS =====")
    all_passed = True
    for test, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{test.upper()}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("\nAll tests PASSED! Your Chaptrix automation setup is ready.")
        return 0
    else:
        logger.error("\nSome tests FAILED. Please fix the issues before setting up automation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())