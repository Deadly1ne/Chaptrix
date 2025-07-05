# Configuration Management System for Chaptrix

This guide outlines how to implement a robust configuration management system for Chaptrix to improve flexibility, maintainability, and user experience.

## Current Configuration Approach

Currently, Chaptrix uses two main JSON configuration files:

1. **comics.json**: Stores information about tracked comics, including site adapters, comic URLs, and last chapter information.
2. **settings.json**: Stores application settings such as download paths, Google Drive integration, Discord notifications, and image processing options.

While this approach works, it can be enhanced to provide more flexibility, validation, and user-friendly configuration management.

## Benefits of an Enhanced Configuration System

- **Improved Validation**: Catch configuration errors early
- **Environment-Specific Settings**: Support different configurations for development, testing, and production
- **Dynamic Configuration**: Allow runtime configuration changes
- **User-Friendly Interface**: Provide a better interface for configuration management
- **Secure Credential Management**: Better handling of sensitive information

## Proposed Configuration Architecture

### 1. Configuration Hierarchy

Implement a hierarchical configuration system with the following layers (in order of precedence):

1. **Command-Line Arguments**: Highest priority, override all other settings
2. **Environment Variables**: Override default and file-based settings
3. **User Configuration Files**: User-specific settings (comics.json, settings.json)
4. **Default Configuration**: Built-in default values

### 2. Configuration Schema

Define a formal schema for each configuration file to enable validation and documentation:

- **JSON Schema**: Define the structure and constraints for configuration files
- **Validation Logic**: Implement validation to catch configuration errors
- **Documentation**: Generate documentation from the schema

### 3. Configuration Manager

Implement a central configuration manager to handle loading, validation, and access to configuration:

- **Singleton Pattern**: Ensure a single configuration instance
- **Lazy Loading**: Load configurations only when needed
- **Caching**: Cache configuration values for performance
- **Change Notification**: Notify components of configuration changes

## Implementation Steps

### 1. Define Configuration Schema

Create JSON Schema definitions for configuration files:

```python
# config/schemas.py

COMICS_SCHEMA = {
    "type": "object",
    "required": ["sites"],
    "properties": {
        "sites": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "required": ["enabled", "comics"],
                "properties": {
                    "enabled": {"type": "boolean"},
                    "comics": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "required": ["title", "url", "last_chapter", "enabled"],
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string", "format": "uri"},
                                "last_chapter": {"type": "string"},
                                "enabled": {"type": "boolean"},
                                "custom_settings": {"type": "object"}
                            }
                        }
                    }
                }
            }
        }
    }
}

SETTINGS_SCHEMA = {
    "type": "object",
    "required": ["download_path", "google_drive", "discord", "template_processing", "banner_cropper"],
    "properties": {
        "download_path": {"type": "string"},
        "google_drive": {
            "type": "object",
            "required": ["enabled", "folder_id"],
            "properties": {
                "enabled": {"type": "boolean"},
                "folder_id": {"type": "string"},
                "service_account": {"type": "boolean", "default": False},
                "credentials_path": {"type": "string", "default": "credentials.json"}
            }
        },
        "discord": {
            "type": "object",
            "required": ["enabled"],
            "properties": {
                "enabled": {"type": "boolean"},
                "webhook_url": {"type": "string"},
                "bot_token": {"type": "string"},
                "channel_id": {"type": "string"},
                "mention_role_id": {"type": "string", "default": ""}
            }
        },
        "template_processing": {
            "type": "object",
            "required": ["enabled"],
            "properties": {
                "enabled": {"type": "boolean"},
                "templates_path": {"type": "string", "default": "templates"}
            }
        },
        "banner_cropper": {
            "type": "object",
            "required": ["enabled"],
            "properties": {
                "enabled": {"type": "boolean"},
                "threshold": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.8}
            }
        },
        "stitcher": {
            "type": "object",
            "properties": {
                "max_height": {"type": "integer", "default": 65000},
                "quality": {"type": "integer", "minimum": 1, "maximum": 100, "default": 90},
                "format": {"type": "string", "enum": ["JPEG", "PNG", "WEBP"], "default": "JPEG"}
            }
        },
        "logging": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "default": "INFO"},
                "file": {"type": "string", "default": "chaptrix.log"},
                "max_size": {"type": "integer", "default": 10485760},  # 10MB
                "backup_count": {"type": "integer", "default": 5}
            }
        },
        "performance": {
            "type": "object",
            "properties": {
                "concurrent_downloads": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3},
                "download_timeout": {"type": "integer", "minimum": 5, "maximum": 300, "default": 30},
                "retry_count": {"type": "integer", "minimum": 0, "maximum": 10, "default": 3},
                "retry_delay": {"type": "integer", "minimum": 1, "maximum": 60, "default": 5}
            }
        }
    }
}
```

### 2. Implement Configuration Validator

Enhance the existing config_validator.py to use the schema definitions:

```python
# config_validator.py
import os
import json
import logging
from jsonschema import validate, ValidationError
from config.schemas import COMICS_SCHEMA, SETTINGS_SCHEMA

logger = logging.getLogger(__name__)

def validate_comics_json(file_path="comics.json"):
    """Validate the comics.json file against the schema
    
    Args:
        file_path: Path to the comics.json file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Comics configuration file not found: {file_path}")
            return False
            
        with open(file_path, 'r', encoding='utf-8') as f:
            comics_data = json.load(f)
            
        validate(instance=comics_data, schema=COMICS_SCHEMA)
        logger.info(f"Comics configuration validated successfully: {file_path}")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in comics configuration: {str(e)}")
        return False
    except ValidationError as e:
        logger.error(f"Comics configuration validation failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error validating comics configuration: {str(e)}")
        return False

def validate_settings_json(file_path="settings.json"):
    """Validate the settings.json file against the schema
    
    Args:
        file_path: Path to the settings.json file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Settings configuration file not found: {file_path}")
            return False
            
        with open(file_path, 'r', encoding='utf-8') as f:
            settings_data = json.load(f)
            
        validate(instance=settings_data, schema=SETTINGS_SCHEMA)
        logger.info(f"Settings configuration validated successfully: {file_path}")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in settings configuration: {str(e)}")
        return False
    except ValidationError as e:
        logger.error(f"Settings configuration validation failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error validating settings configuration: {str(e)}")
        return False

def create_default_comics_json(file_path="comics.json"):
    """Create a default comics.json file
    
    Args:
        file_path: Path to create the file
        
    Returns:
        bool: True if created successfully, False otherwise
    """
    try:
        default_comics = {
            "sites": {}
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_comics, f, indent=4)
            
        logger.info(f"Created default comics configuration: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating default comics configuration: {str(e)}")
        return False

def create_default_settings_json(file_path="settings.json"):
    """Create a default settings.json file
    
    Args:
        file_path: Path to create the file
        
    Returns:
        bool: True if created successfully, False otherwise
    """
    try:
        default_settings = {
            "download_path": "./downloads",
            "google_drive": {
                "enabled": False,
                "folder_id": "",
                "service_account": False,
                "credentials_path": "credentials.json"
            },
            "discord": {
                "enabled": False,
                "webhook_url": "",
                "bot_token": "",
                "channel_id": "",
                "mention_role_id": ""
            },
            "template_processing": {
                "enabled": True,
                "templates_path": "templates"
            },
            "banner_cropper": {
                "enabled": True,
                "threshold": 0.8
            },
            "stitcher": {
                "max_height": 65000,
                "quality": 90,
                "format": "JPEG"
            },
            "logging": {
                "level": "INFO",
                "file": "chaptrix.log",
                "max_size": 10485760,
                "backup_count": 5
            },
            "performance": {
                "concurrent_downloads": 3,
                "download_timeout": 30,
                "retry_count": 3,
                "retry_delay": 5
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, indent=4)
            
        logger.info(f"Created default settings configuration: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating default settings configuration: {str(e)}")
        return False

def ensure_valid_configuration():
    """Ensure that valid configuration files exist
    
    Returns:
        bool: True if valid configuration exists, False otherwise
    """
    comics_valid = validate_comics_json()
    settings_valid = validate_settings_json()
    
    if not comics_valid:
        logger.warning("Creating default comics configuration")
        comics_valid = create_default_comics_json()
        
    if not settings_valid:
        logger.warning("Creating default settings configuration")
        settings_valid = create_default_settings_json()
        
    return comics_valid and settings_valid
```

### 3. Implement Configuration Manager

Create a central configuration manager to handle loading, validation, and access to configuration:

```python
# config/manager.py
import os
import json
import logging
from typing import Any, Dict, Optional
from jsonschema import validate
from config.schemas import COMICS_SCHEMA, SETTINGS_SCHEMA
from config_validator import ensure_valid_configuration

logger = logging.getLogger(__name__)

class ConfigurationManager:
    """Central manager for Chaptrix configuration"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure a single configuration instance"""
        if cls._instance is None:
            cls._instance = super(ConfigurationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration manager"""
        if self._initialized:
            return
            
        self._initialized = True
        self._comics_config = None
        self._settings_config = None
        self._env_config = {}
        self._cli_config = {}
        self._comics_file = "comics.json"
        self._settings_file = "settings.json"
        
        # Load environment variables
        self._load_environment_variables()
        
        # Ensure valid configuration files exist
        ensure_valid_configuration()
    
    def _load_environment_variables(self):
        """Load configuration from environment variables"""
        # Discord configuration
        if os.environ.get("DISCORD_WEBHOOK_URL"):
            self._env_config["discord.webhook_url"] = os.environ.get("DISCORD_WEBHOOK_URL")
            self._env_config["discord.enabled"] = True
            
        if os.environ.get("DISCORD_BOT_TOKEN") and os.environ.get("DISCORD_CHANNEL_ID"):
            self._env_config["discord.bot_token"] = os.environ.get("DISCORD_BOT_TOKEN")
            self._env_config["discord.channel_id"] = os.environ.get("DISCORD_CHANNEL_ID")
            self._env_config["discord.enabled"] = True
            
        if os.environ.get("DISCORD_MENTION_ROLE_ID"):
            self._env_config["discord.mention_role_id"] = os.environ.get("DISCORD_MENTION_ROLE_ID")
        
        # Google Drive configuration
        if os.environ.get("GOOGLE_DRIVE_FOLDER_ID"):
            self._env_config["google_drive.folder_id"] = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
            self._env_config["google_drive.enabled"] = True
            
        if os.environ.get("GOOGLE_CREDENTIALS_PATH"):
            self._env_config["google_drive.credentials_path"] = os.environ.get("GOOGLE_CREDENTIALS_PATH")
            
        if os.environ.get("GOOGLE_SERVICE_ACCOUNT"):
            self._env_config["google_drive.service_account"] = os.environ.get("GOOGLE_SERVICE_ACCOUNT").lower() in ["true", "1", "yes"]
        
        # Download path
        if os.environ.get("DOWNLOAD_PATH"):
            self._env_config["download_path"] = os.environ.get("DOWNLOAD_PATH")
        
        # Logging configuration
        if os.environ.get("LOG_LEVEL"):
            self._env_config["logging.level"] = os.environ.get("LOG_LEVEL")
    
    def set_cli_arguments(self, args):
        """Set configuration from command-line arguments
        
        Args:
            args: Parsed command-line arguments
        """
        # Convert namespace to dictionary
        if args:
            args_dict = vars(args)
            
            # Map command-line arguments to configuration keys
            if "download_path" in args_dict and args_dict["download_path"]:
                self._cli_config["download_path"] = args_dict["download_path"]
                
            if "log_level" in args_dict and args_dict["log_level"]:
                self._cli_config["logging.level"] = args_dict["log_level"]
                
            # Add more mappings as needed
    
    def load_comics_config(self, reload=False):
        """Load comics configuration from file
        
        Args:
            reload: Force reload from file
            
        Returns:
            dict: Comics configuration
        """
        if self._comics_config is None or reload:
            try:
                with open(self._comics_file, 'r', encoding='utf-8') as f:
                    self._comics_config = json.load(f)
                validate(instance=self._comics_config, schema=COMICS_SCHEMA)
            except Exception as e:
                logger.error(f"Error loading comics configuration: {str(e)}")
                self._comics_config = {"sites": {}}
                
        return self._comics_config
    
    def load_settings_config(self, reload=False):
        """Load settings configuration from file
        
        Args:
            reload: Force reload from file
            
        Returns:
            dict: Settings configuration
        """
        if self._settings_config is None or reload:
            try:
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    self._settings_config = json.load(f)
                validate(instance=self._settings_config, schema=SETTINGS_SCHEMA)
            except Exception as e:
                logger.error(f"Error loading settings configuration: {str(e)}")
                # Create default settings
                self._settings_config = {
                    "download_path": "./downloads",
                    "google_drive": {"enabled": False, "folder_id": ""},
                    "discord": {"enabled": False, "webhook_url": "", "bot_token": "", "channel_id": ""},
                    "template_processing": {"enabled": True},
                    "banner_cropper": {"enabled": True}
                }
                
        return self._settings_config
    
    def get_comics_config(self):
        """Get the comics configuration
        
        Returns:
            dict: Comics configuration
        """
        return self.load_comics_config()
    
    def get_settings_config(self):
        """Get the settings configuration
        
        Returns:
            dict: Settings configuration
        """
        return self.load_settings_config()
    
    def get_setting(self, key, default=None):
        """Get a setting value with fallback to environment, CLI, and default
        
        Args:
            key: Setting key (dot notation for nested settings)
            default: Default value if not found
            
        Returns:
            Any: Setting value
        """
        # Check CLI arguments first (highest priority)
        if key in self._cli_config:
            return self._cli_config[key]
            
        # Check environment variables
        if key in self._env_config:
            return self._env_config[key]
            
        # Check settings configuration
        settings = self.get_settings_config()
        keys = key.split('.')
        
        # Navigate nested dictionary
        value = settings
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def save_comics_config(self):
        """Save comics configuration to file
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if self._comics_config is None:
            logger.error("Cannot save comics configuration: Configuration not loaded")
            return False
            
        try:
            with open(self._comics_file, 'w', encoding='utf-8') as f:
                json.dump(self._comics_config, f, indent=4)
            logger.info(f"Comics configuration saved: {self._comics_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving comics configuration: {str(e)}")
            return False
    
    def save_settings_config(self):
        """Save settings configuration to file
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if self._settings_config is None:
            logger.error("Cannot save settings configuration: Configuration not loaded")
            return False
            
        try:
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings_config, f, indent=4)
            logger.info(f"Settings configuration saved: {self._settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving settings configuration: {str(e)}")
            return False
    
    def update_comic(self, site_name, comic_id, data):
        """Update a comic in the configuration
        
        Args:
            site_name: Name of the site
            comic_id: ID of the comic
            data: Updated comic data
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        comics_config = self.get_comics_config()
        
        # Ensure site exists
        if site_name not in comics_config["sites"]:
            comics_config["sites"][site_name] = {"enabled": True, "comics": {}}
            
        # Update comic
        comics_config["sites"][site_name]["comics"][comic_id] = data
        
        # Save configuration
        return self.save_comics_config()
    
    def update_setting(self, key, value):
        """Update a setting in the configuration
        
        Args:
            key: Setting key (dot notation for nested settings)
            value: New value
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        settings_config = self.get_settings_config()
        keys = key.split('.')
        
        # Navigate nested dictionary
        target = settings_config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
            
        # Update value
        target[keys[-1]] = value
        
        # Save configuration
        return self.save_settings_config()
    
    def get_enabled_sites(self):
        """Get a list of enabled sites
        
        Returns:
            list: List of enabled site names
        """
        comics_config = self.get_comics_config()
        return [site for site, data in comics_config["sites"].items() if data.get("enabled", True)]
    
    def get_enabled_comics(self, site_name):
        """Get a list of enabled comics for a site
        
        Args:
            site_name: Name of the site
            
        Returns:
            dict: Dictionary of enabled comics
        """
        comics_config = self.get_comics_config()
        
        if site_name not in comics_config["sites"]:
            return {}
            
        site_data = comics_config["sites"][site_name]
        if not site_data.get("enabled", True):
            return {}
            
        return {comic_id: data for comic_id, data in site_data["comics"].items() if data.get("enabled", True)}
```

### 4. Update Main Functions to Use Configuration Manager

Update the main functions to use the new configuration manager:

```python
# main.py (partial update)
from config.manager import ConfigurationManager

def load_settings(settings_file="settings.json"):
    """Load settings from file
    
    Args:
        settings_file: Path to settings file
        
    Returns:
        dict: Settings dictionary
    """
    config_manager = ConfigurationManager()
    return config_manager.get_settings_config()

def load_comics(comics_file="comics.json"):
    """Load comics from file
    
    Args:
        comics_file: Path to comics file
        
    Returns:
        dict: Comics dictionary
    """
    config_manager = ConfigurationManager()
    return config_manager.get_comics_config()

def save_comics(comics_data, comics_file="comics.json"):
    """Save comics to file
    
    Args:
        comics_data: Comics dictionary
        comics_file: Path to comics file
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    config_manager = ConfigurationManager()
    config_manager._comics_config = comics_data
    return config_manager.save_comics_config()
```

### 5. Implement Command-Line Argument Parsing

Enhance the command-line argument parsing to support configuration overrides:

```python
# unified_workflow.py (partial update)
import argparse
from config.manager import ConfigurationManager

def parse_arguments():
    """Parse command-line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Chaptrix Unified Workflow")
    
    # General options
    parser.add_argument("--download-path", help="Path to download comics")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level")
    
    # Comic selection
    parser.add_argument("--site", help="Process only the specified site")
    parser.add_argument("--comic", help="Process only the specified comic")
    parser.add_argument("--full-scan", action="store_true", help="Perform a full scan for all comics")
    
    # Feature toggles
    parser.add_argument("--disable-drive", action="store_true", help="Disable Google Drive upload")
    parser.add_argument("--disable-discord", action="store_true", help="Disable Discord notifications")
    parser.add_argument("--disable-template", action="store_true", help="Disable template processing")
    parser.add_argument("--disable-banner", action="store_true", help="Disable banner cropping")
    
    return parser.parse_args()

def main():
    """Main function"""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Initialize configuration manager
    config_manager = ConfigurationManager()
    config_manager.set_cli_arguments(args)
    
    # Set up logging
    log_level = config_manager.get_setting("logging.level", "INFO")
    # ... (setup logging)
    
    # Load settings and comics
    settings = config_manager.get_settings_config()
    comics = config_manager.get_comics_config()
    
    # Apply command-line overrides
    if args.disable_drive:
        settings["google_drive"]["enabled"] = False
    if args.disable_discord:
        settings["discord"]["enabled"] = False
    if args.disable_template:
        settings["template_processing"]["enabled"] = False
    if args.disable_banner:
        settings["banner_cropper"]["enabled"] = False
    
    # ... (rest of the main function)
```

### 6. Implement Environment-Specific Configuration

Add support for environment-specific configuration:

```python
# config/manager.py (additional method)
def load_environment_config(self, environment="production"):
    """Load environment-specific configuration
    
    Args:
        environment: Environment name (development, testing, production)
        
    Returns:
        bool: True if loaded successfully, False otherwise
    """
    env_file = f"settings.{environment}.json"
    
    if not os.path.exists(env_file):
        logger.debug(f"Environment-specific configuration not found: {env_file}")
        return False
        
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            env_config = json.load(f)
            
        # Merge with settings configuration
        self._settings_config = self._merge_configs(self._settings_config, env_config)
        logger.info(f"Loaded environment-specific configuration: {env_file}")
        return True
    except Exception as e:
        logger.error(f"Error loading environment-specific configuration: {str(e)}")
        return False

def _merge_configs(self, base_config, override_config):
    """Recursively merge two configuration dictionaries
    
    Args:
        base_config: Base configuration
        override_config: Override configuration
        
    Returns:
        dict: Merged configuration
    """
    if not isinstance(base_config, dict) or not isinstance(override_config, dict):
        return override_config
        
    result = base_config.copy()
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = self._merge_configs(result[key], value)
        else:
            result[key] = value
            
    return result
```

### 7. Implement Configuration UI

Create a simple configuration UI using Streamlit:

```python
# config_ui.py
import streamlit as st
import json
import os
from config.manager import ConfigurationManager

def main():
    """Main function for the configuration UI"""
    st.set_page_config(page_title="Chaptrix Configuration", page_icon="📚", layout="wide")
    st.title("Chaptrix Configuration")
    
    # Initialize configuration manager
    config_manager = ConfigurationManager()
    
    # Create tabs for different configuration sections
    tab1, tab2, tab3 = st.tabs(["General Settings", "Comics", "Advanced Settings"])
    
    with tab1:
        edit_general_settings(config_manager)
        
    with tab2:
        edit_comics(config_manager)
        
    with tab3:
        edit_advanced_settings(config_manager)

def edit_general_settings(config_manager):
    """Edit general settings
    
    Args:
        config_manager: Configuration manager instance
    """
    st.header("General Settings")
    
    settings = config_manager.get_settings_config()
    
    # Download path
    download_path = st.text_input("Download Path", settings["download_path"])
    
    # Google Drive integration
    st.subheader("Google Drive Integration")
    drive_enabled = st.checkbox("Enable Google Drive Upload", settings["google_drive"]["enabled"])
    drive_folder_id = st.text_input("Google Drive Folder ID", settings["google_drive"]["folder_id"])
    drive_service_account = st.checkbox("Use Service Account", settings["google_drive"].get("service_account", False))
    drive_credentials_path = st.text_input("Credentials Path", settings["google_drive"].get("credentials_path", "credentials.json"))
    
    # Discord integration
    st.subheader("Discord Integration")
    discord_enabled = st.checkbox("Enable Discord Notifications", settings["discord"]["enabled"])
    discord_webhook_url = st.text_input("Discord Webhook URL", settings["discord"].get("webhook_url", ""))
    discord_bot_token = st.text_input("Discord Bot Token", settings["discord"].get("bot_token", ""))
    discord_channel_id = st.text_input("Discord Channel ID", settings["discord"].get("channel_id", ""))
    discord_mention_role_id = st.text_input("Discord Mention Role ID", settings["discord"].get("mention_role_id", ""))
    
    # Image processing
    st.subheader("Image Processing")
    template_enabled = st.checkbox("Enable Template Processing", settings["template_processing"]["enabled"])
    banner_enabled = st.checkbox("Enable Banner Cropping", settings["banner_cropper"]["enabled"])
    banner_threshold = st.slider("Banner Cropping Threshold", 0.0, 1.0, settings["banner_cropper"].get("threshold", 0.8), 0.01)
    
    # Save button
    if st.button("Save General Settings"):
        # Update settings
        settings["download_path"] = download_path
        settings["google_drive"]["enabled"] = drive_enabled
        settings["google_drive"]["folder_id"] = drive_folder_id
        settings["google_drive"]["service_account"] = drive_service_account
        settings["google_drive"]["credentials_path"] = drive_credentials_path
        settings["discord"]["enabled"] = discord_enabled
        settings["discord"]["webhook_url"] = discord_webhook_url
        settings["discord"]["bot_token"] = discord_bot_token
        settings["discord"]["channel_id"] = discord_channel_id
        settings["discord"]["mention_role_id"] = discord_mention_role_id
        settings["template_processing"]["enabled"] = template_enabled
        settings["banner_cropper"]["enabled"] = banner_enabled
        settings["banner_cropper"]["threshold"] = banner_threshold
        
        # Save settings
        if config_manager.save_settings_config():
            st.success("Settings saved successfully!")
        else:
            st.error("Failed to save settings!")

def edit_comics(config_manager):
    """Edit comics configuration
    
    Args:
        config_manager: Configuration manager instance
    """
    st.header("Comics Configuration")
    
    comics = config_manager.get_comics_config()
    
    # Site selection
    sites = list(comics["sites"].keys())
    if not sites:
        st.info("No sites configured. Add a site below.")
        site_name = None
    else:
        site_name = st.selectbox("Select Site", sites)
    
    # Add new site
    with st.expander("Add New Site"):
        new_site_name = st.text_input("Site Name")
        if st.button("Add Site") and new_site_name:
            if new_site_name in comics["sites"]:
                st.error(f"Site '{new_site_name}' already exists!")
            else:
                comics["sites"][new_site_name] = {"enabled": True, "comics": {}}
                if config_manager.save_comics_config():
                    st.success(f"Site '{new_site_name}' added successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to save comics configuration!")
    
    if site_name:
        # Site settings
        site_enabled = st.checkbox(f"Enable {site_name}", comics["sites"][site_name].get("enabled", True))
        
        # Update site settings
        if st.button("Update Site Settings"):
            comics["sites"][site_name]["enabled"] = site_enabled
            if config_manager.save_comics_config():
                st.success(f"Site '{site_name}' updated successfully!")
            else:
                st.error("Failed to save comics configuration!")
        
        # Comics for the selected site
        st.subheader(f"Comics for {site_name}")
        
        site_comics = comics["sites"][site_name]["comics"]
        comic_ids = list(site_comics.keys())
        
        if not comic_ids:
            st.info(f"No comics configured for {site_name}. Add a comic below.")
            comic_id = None
        else:
            comic_id = st.selectbox("Select Comic", comic_ids)
        
        # Add new comic
        with st.expander("Add New Comic"):
            new_comic_id = st.text_input("Comic ID")
            new_comic_title = st.text_input("Comic Title")
            new_comic_url = st.text_input("Comic URL")
            
            if st.button("Add Comic") and new_comic_id and new_comic_title and new_comic_url:
                if new_comic_id in site_comics:
                    st.error(f"Comic '{new_comic_id}' already exists!")
                else:
                    site_comics[new_comic_id] = {
                        "title": new_comic_title,
                        "url": new_comic_url,
                        "last_chapter": "0",
                        "enabled": True
                    }
                    if config_manager.save_comics_config():
                        st.success(f"Comic '{new_comic_title}' added successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to save comics configuration!")
        
        if comic_id:
            # Comic settings
            comic_data = site_comics[comic_id]
            comic_title = st.text_input("Comic Title", comic_data["title"])
            comic_url = st.text_input("Comic URL", comic_data["url"])
            comic_last_chapter = st.text_input("Last Chapter", comic_data["last_chapter"])
            comic_enabled = st.checkbox("Enable Comic", comic_data.get("enabled", True))
            
            # Update comic settings
            if st.button("Update Comic Settings"):
                comic_data["title"] = comic_title
                comic_data["url"] = comic_url
                comic_data["last_chapter"] = comic_last_chapter
                comic_data["enabled"] = comic_enabled
                
                if config_manager.save_comics_config():
                    st.success(f"Comic '{comic_title}' updated successfully!")
                else:
                    st.error("Failed to save comics configuration!")
            
            # Delete comic
            if st.button("Delete Comic", type="primary", help="Delete this comic from the configuration"):
                if st.checkbox("Confirm deletion"):
                    del site_comics[comic_id]
                    if config_manager.save_comics_config():
                        st.success(f"Comic '{comic_title}' deleted successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to save comics configuration!")

def edit_advanced_settings(config_manager):
    """Edit advanced settings
    
    Args:
        config_manager: Configuration manager instance
    """
    st.header("Advanced Settings")
    
    settings = config_manager.get_settings_config()
    
    # Stitcher settings
    st.subheader("Stitcher Settings")
    stitcher_settings = settings.get("stitcher", {})
    stitcher_max_height = st.number_input("Maximum Image Height", 1000, 100000, stitcher_settings.get("max_height", 65000))
    stitcher_quality = st.slider("Image Quality", 1, 100, stitcher_settings.get("quality", 90))
    stitcher_format = st.selectbox("Image Format", ["JPEG", "PNG", "WEBP"], ["JPEG", "PNG", "WEBP"].index(stitcher_settings.get("format", "JPEG")))
    
    # Logging settings
    st.subheader("Logging Settings")
    logging_settings = settings.get("logging", {})
    logging_level = st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(logging_settings.get("level", "INFO")))
    logging_file = st.text_input("Log File", logging_settings.get("file", "chaptrix.log"))
    logging_max_size = st.number_input("Max Log Size (bytes)", 1024, 1073741824, logging_settings.get("max_size", 10485760))
    logging_backup_count = st.number_input("Log Backup Count", 0, 100, logging_settings.get("backup_count", 5))
    
    # Performance settings
    st.subheader("Performance Settings")
    performance_settings = settings.get("performance", {})
    concurrent_downloads = st.slider("Concurrent Downloads", 1, 10, performance_settings.get("concurrent_downloads", 3))
    download_timeout = st.slider("Download Timeout (seconds)", 5, 300, performance_settings.get("download_timeout", 30))
    retry_count = st.slider("Retry Count", 0, 10, performance_settings.get("retry_count", 3))
    retry_delay = st.slider("Retry Delay (seconds)", 1, 60, performance_settings.get("retry_delay", 5))
    
    # Save button
    if st.button("Save Advanced Settings"):
        # Update stitcher settings
        if "stitcher" not in settings:
            settings["stitcher"] = {}
        settings["stitcher"]["max_height"] = stitcher_max_height
        settings["stitcher"]["quality"] = stitcher_quality
        settings["stitcher"]["format"] = stitcher_format
        
        # Update logging settings
        if "logging" not in settings:
            settings["logging"] = {}
        settings["logging"]["level"] = logging_level
        settings["logging"]["file"] = logging_file
        settings["logging"]["max_size"] = logging_max_size
        settings["logging"]["backup_count"] = logging_backup_count
        
        # Update performance settings
        if "performance" not in settings:
            settings["performance"] = {}
        settings["performance"]["concurrent_downloads"] = concurrent_downloads
        settings["performance"]["download_timeout"] = download_timeout
        settings["performance"]["retry_count"] = retry_count
        settings["performance"]["retry_delay"] = retry_delay
        
        # Save settings
        if config_manager.save_settings_config():
            st.success("Advanced settings saved successfully!")
        else:
            st.error("Failed to save advanced settings!")
    
    # Export/Import configuration
    st.subheader("Export/Import Configuration")
    
    # Export
    if st.button("Export Configuration"):
        export_data = {
            "comics": config_manager.get_comics_config(),
            "settings": config_manager.get_settings_config()
        }
        export_json = json.dumps(export_data, indent=4)
        st.download_button(
            label="Download Configuration",
            data=export_json,
            file_name="chaptrix_config.json",
            mime="application/json"
        )
    
    # Import
    uploaded_file = st.file_uploader("Import Configuration", type="json")
    if uploaded_file is not None:
        try:
            import_data = json.load(uploaded_file)
            if "comics" in import_data and "settings" in import_data:
                if st.button("Apply Imported Configuration"):
                    config_manager._comics_config = import_data["comics"]
                    config_manager._settings_config = import_data["settings"]
                    
                    comics_saved = config_manager.save_comics_config()
                    settings_saved = config_manager.save_settings_config()
                    
                    if comics_saved and settings_saved:
                        st.success("Configuration imported successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to import configuration!")
            else:
                st.error("Invalid configuration file!")
        except Exception as e:
            st.error(f"Error importing configuration: {str(e)}")

if __name__ == "__main__":
    main()
```

### 8. Create a Configuration Launcher Script

Create a script to launch the configuration UI:

```python
# config_launcher.py
import subprocess
import sys
import os

def main():
    """Launch the configuration UI"""
    try:
        # Check if streamlit is installed
        try:
            import streamlit
        except ImportError:
            print("Streamlit is not installed. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
        
        # Launch the configuration UI
        print("Launching Chaptrix Configuration UI...")
        subprocess.check_call([sys.executable, "-m", "streamlit", "run", "config_ui.py"])
    except Exception as e:
        print(f"Error launching configuration UI: {str(e)}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
```

### 9. Create a Batch File for Windows Users

Create a batch file to launch the configuration UI on Windows:

```batch
@echo off
echo Launching Chaptrix Configuration UI...
python config_launcher.py
```

## Conclusion

Implementing a robust configuration management system for Chaptrix will significantly improve flexibility, maintainability, and user experience. The proposed architecture provides a solid foundation that can be extended as needed.

Key benefits of the proposed configuration system include:

1. **Hierarchical Configuration**: Support for multiple configuration sources with clear precedence
2. **Schema Validation**: Formal schema definition and validation to catch configuration errors
3. **Centralized Management**: Single point of access for all configuration settings
4. **Environment Support**: Support for different environments (development, testing, production)
5. **User-Friendly Interface**: Streamlit-based UI for easy configuration management
6. **Secure Credential Handling**: Better handling of sensitive information

By following this guide, you'll establish a robust configuration management system that will help maintain high flexibility and provide a better user experience for Chaptrix.