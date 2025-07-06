import logging
import os
import json
from typing import Optional, Any

def handle_error(error, context="operation", critical=False, additional_info=None):
    """
    Unified error handling function for the entire Chaptrix application.
    
    Args:
        error: The error/exception that occurred
        context: Context where the error occurred
        critical: Whether this is a critical error that should stop execution
        additional_info: Additional information about the error
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    log_message = f"Error in {context}: {error_type} - {error_message}"
    if additional_info:
        log_message += f" | Additional info: {additional_info}"
    
    if critical:
        logging.critical(log_message)
        if hasattr(error, '__traceback__'):
            logging.critical(f"Traceback: {error.__traceback__}")
    else:
        logging.error(log_message)
    
    return error_message

def setup_logging(log_level=logging.INFO, log_file="chaptrix.log"):
    """
    Setup logging configuration for the application.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Log file name (default: chaptrix.log)
    """
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def load_json_config(file_path: str) -> Optional[dict]:
    """
    Load JSON configuration file with error handling.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary containing the configuration or None if failed
    """
    try:
        if not os.path.exists(file_path):
            logging.warning(f"Configuration file not found: {file_path}")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        handle_error(e, f"loading config file {file_path}")
        return None

def save_json_config(data: dict, file_path: str) -> bool:
    """
    Save dictionary to JSON file with error handling.
    
    Args:
        data: Dictionary to save
        file_path: Path to save the JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        handle_error(e, f"saving config file {file_path}")
        return False

def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure a directory exists, create if it doesn't.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            logging.info(f"Created directory: {directory_path}")
        return True
    except Exception as e:
        handle_error(e, f"creating directory {directory_path}")
        return False