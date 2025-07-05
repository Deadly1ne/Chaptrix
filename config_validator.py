import os
import json
import sys
from colorama import init, Fore, Style

# Initialize colorama for colored console output
init()

def print_success(message):
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_warning(message):
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")

def print_error(message):
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

def print_info(message):
    print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")

def print_header(message):
    print(f"\n{Fore.WHITE}{Style.BRIGHT}{message}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'-' * len(message)}{Style.RESET_ALL}")

def validate_settings():
    print_header("Validating settings.json")
    
    # Check if settings.json exists
    if not os.path.exists("settings.json"):
        print_error("settings.json not found")
        return False
    
    try:
        with open("settings.json", "r", encoding="utf-8") as f:
            settings = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in settings.json: {e}")
        return False
    
    # Check required settings
    required_settings = [
        "download_path",
        "processed_path"
    ]
    
    for setting in required_settings:
        if setting not in settings:
            print_error(f"Missing required setting: {setting}")
            return False
        else:
            print_success(f"Found required setting: {setting}")
    
    # Check paths
    for path_setting in ["download_path", "processed_path"]:
        path = settings[path_setting]
        if not os.path.exists(path):
            print_warning(f"Path does not exist: {path} ({path_setting})")
            try:
                os.makedirs(path, exist_ok=True)
                print_success(f"Created directory: {path}")
            except Exception as e:
                print_error(f"Failed to create directory {path}: {e}")
        else:
            print_success(f"Path exists: {path} ({path_setting})")
    
    # Check banner cropping settings
    if "enable_banner_cropping" not in settings:
        print_warning("enable_banner_cropping setting not found, banner cropping will not be applied")
    elif settings["enable_banner_cropping"]:
        print_success("Banner cropping is enabled")
        
        # Check if banner.png exists
        banner_path = "assets/banner.png"
        if not os.path.exists(banner_path):
            print_error(f"Banner template not found: {banner_path}")
        else:
            print_success(f"Banner template found: {banner_path}")
    else:
        print_info("Banner cropping is disabled")
    
    # Check image quality setting
    if "image_quality" not in settings:
        print_warning("image_quality setting not found, using default value")
    else:
        quality = settings["image_quality"]
        if not isinstance(quality, int) or quality < 1 or quality > 100:
            print_error(f"Invalid image_quality value: {quality} (should be 1-100)")
        else:
            print_success(f"Image quality set to: {quality}")
    
    # Check upload settings
    if "upload_to_discord" in settings and settings["upload_to_discord"]:
        print_success("Discord upload is enabled")
        if "discord_webhook_url" not in settings or not settings["discord_webhook_url"]:
            print_error("Discord webhook URL is missing")
        else:
            print_success("Discord webhook URL is configured")
    else:
        print_info("Discord upload is disabled")
    
    if "upload_to_drive" in settings and settings["upload_to_drive"]:
        print_success("Google Drive upload is enabled")
        if not os.path.exists("credentials.json"):
            print_error("credentials.json not found (required for Google Drive upload)")
        else:
            print_success("credentials.json found")
    else:
        print_info("Google Drive upload is disabled")
    
    return True

def validate_comics():
    print_header("Validating comics.json")
    
    # Check if comics.json exists
    if not os.path.exists("comics.json"):
        print_error("comics.json not found")
        return False
    
    try:
        with open("comics.json", "r", encoding="utf-8") as f:
            comics = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in comics.json: {e}")
        return False
    
    if not isinstance(comics, list):
        print_error("comics.json should contain a list of comics")
        return False
    
    if len(comics) == 0:
        print_warning("No comics found in comics.json")
        return True
    
    print_success(f"Found {len(comics)} comics in comics.json")
    
    # Validate each comic
    for i, comic in enumerate(comics):
        if "name" not in comic or not comic["name"]:
            print_error(f"Comic #{i+1} is missing a name")
            continue
            
        comic_name = comic["name"]
        print_info(f"Validating comic: {comic_name}")
        
        # Check required fields
        required_fields = ["url", "last_known_chapter"]
        for field in required_fields:
            if field not in comic or not comic[field]:
                print_error(f"  Missing required field: {field}")
            else:
                print_success(f"  Found required field: {field}")
        
        # Check URL format
        if "url" in comic and comic["url"]:
            url = comic["url"]
            if not url.startswith("http"):
                print_warning(f"  URL may be invalid: {url}")
            else:
                print_success(f"  URL format looks valid")
        
        # Check template image if specified
        if "template_image" in comic and comic["template_image"]:
            template_path = comic["template_image"]
            if not os.path.exists(template_path):
                print_error(f"  Template image not found: {template_path}")
            else:
                print_success(f"  Template image found: {template_path}")
    
    return True

def validate_dependencies():
    print_header("Validating Python dependencies")
    
    required_packages = [
        "Pillow",  # PIL for image processing
        "requests",  # For HTTP requests
        "beautifulsoup4",  # For HTML parsing
        "opencv-python",  # For banner cropping
        "colorama",  # For colored console output
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace("-", "_"))
            print_success(f"Found package: {package}")
        except ImportError:
            print_error(f"Missing package: {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print_warning("\nSome required packages are missing. Install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def validate_files():
    print_header("Validating required files")
    
    required_files = [
        "main.py",
        "stitcher.py",
        "banner_cropper.py",
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print_error(f"Required file not found: {file}")
        else:
            print_success(f"Found required file: {file}")
    
    # Check for workflow scripts
    workflow_scripts = [
        "run_unified_workflow.bat",
        "unified_workflow.py",
    ]
    
    for script in workflow_scripts:
        if not os.path.exists(script):
            print_warning(f"Workflow script not found: {script}")
        else:
            print_success(f"Found workflow script: {script}")
    
    return True

def main():
    print(f"{Fore.CYAN}{Style.BRIGHT}Chaptrix Configuration Validator{Style.RESET_ALL}")
    print(f"{Fore.CYAN}==============================={Style.RESET_ALL}\n")
    
    settings_valid = validate_settings()
    comics_valid = validate_comics()
    dependencies_valid = validate_dependencies()
    files_valid = validate_files()
    
    print_header("Validation Summary")
    
    if settings_valid:
        print_success("Settings configuration is valid")
    else:
        print_error("Settings configuration has issues")
    
    if comics_valid:
        print_success("Comics configuration is valid")
    else:
        print_error("Comics configuration has issues")
    
    if dependencies_valid:
        print_success("All required dependencies are installed")
    else:
        print_error("Some dependencies are missing")
    
    if files_valid:
        print_success("All required files are present")
    else:
        print_error("Some required files are missing")
    
    if settings_valid and comics_valid and dependencies_valid and files_valid:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}✓ Configuration is valid! Chaptrix should work correctly.{Style.RESET_ALL}")
        return 0
    else:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠ Configuration has some issues that need to be addressed.{Style.RESET_ALL}")
        return 1

if __name__ == "__main__":
    sys.exit(main())