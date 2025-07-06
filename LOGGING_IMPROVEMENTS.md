# Logging System Improvements

## Overview

This document provides recommendations for enhancing the logging system in the Chaptrix application. A well-designed logging system is crucial for debugging, monitoring, and understanding application behavior.

## Current Logging Implementation

The application currently uses Python's built-in `logging` module with a basic configuration:

```python
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
```

This provides essential logging functionality but has several limitations:

1. No log rotation (log files can grow indefinitely)
2. Limited log levels (primarily using INFO and ERROR)
3. No structured logging for easier parsing
4. No differentiation between different types of events

## Recommended Improvements

### 1. Implement Log Rotation

Use `RotatingFileHandler` or `TimedRotatingFileHandler` to manage log file size:

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_file="chaptrix.log", max_size_mb=10, backup_count=5):
    """Set up logging with rotation"""
    # Convert MB to bytes
    max_bytes = max_size_mb * 1024 * 1024
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_bytes, 
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger("Chaptrix")

# Usage
logger = setup_logging()
```

### 2. Create Component-Specific Loggers

Use hierarchical loggers for different components:

```python
# In main.py
logger = logging.getLogger("Chaptrix.main")

# In stitcher.py
logger = logging.getLogger("Chaptrix.stitcher")

# In banner_cropper.py
logger = logging.getLogger("Chaptrix.banner_cropper")

# In unified_workflow.py
logger = logging.getLogger("Chaptrix.workflow")
```

This allows for component-specific log filtering and levels.

### 3. Add Contextual Information

Enhance log messages with contextual information:

```python
def download_chapter_images(self, chapter_url):
    """Download all images for a chapter"""
    comic_name = self.comic["name"]
    logger.info(f"[Comic: {comic_name}] Downloading images from {chapter_url}")
    
    try:
        # Download logic...
    except Exception as e:
        logger.error(f"[Comic: {comic_name}] Failed to download images: {str(e)}")
```

### 4. Implement Log Levels Consistently

Use appropriate log levels for different types of events:

- **DEBUG**: Detailed information, typically useful only for diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: An indication that something unexpected happened, but the application is still working
- **ERROR**: Due to a more serious problem, the application has not been able to perform a function
- **CRITICAL**: A serious error indicating that the application itself may be unable to continue running

Example implementation:

```python
def process_comic(comic):
    """Process a comic with consistent log levels"""
    logger.debug(f"Starting to process comic: {comic['name']}")
    
    # Check if comic URL is valid
    if not comic.get("url"):
        logger.warning(f"Comic {comic['name']} has no URL defined, skipping")
        return False
    
    try:
        # Processing logic...
        logger.info(f"Successfully processed comic: {comic['name']}")
        return True
    except ConnectionError as e:
        logger.warning(f"Network issue while processing {comic['name']}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to process comic {comic['name']}: {str(e)}")
        return False
```

### 5. Add Structured Logging

Implement structured logging for easier parsing and analysis:

```python
import json

class StructuredLogFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage()
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if available
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

def setup_structured_logging(log_file="chaptrix_structured.log"):
    """Set up structured logging"""
    # Create logger
    logger = logging.getLogger("ChaptrixStructured")
    logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(StructuredLogFormatter())
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger

# Usage
structured_logger = setup_structured_logging()

# Log with extra context
structured_logger.info("Downloaded chapter", extra={
    "comic": "Test Comic",
    "chapter": "Chapter 10",
    "images_count": 15,
    "duration_ms": 1250
})
```

### 6. Add Performance Logging

Track performance metrics in logs:

```python
import time

def log_execution_time(func):
    """Decorator to log function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Get function name and arguments for context
        func_name = func.__name__
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        logger.debug(f"Function {func_name} executed in {execution_time:.2f}ms")
        return result
    return wrapper

# Usage
@log_execution_time
def stitch_images(images, target_width):
    # Stitching logic...
    return stitched_image
```

### 7. Create a Logging Configuration File

Move logging configuration to a separate file for easier management:

```python
# logging_config.py
import logging
import logging.config
import os

def configure_logging(log_dir="logs", debug_mode=False):
    """Configure logging based on settings"""
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Define log files
    main_log = os.path.join(log_dir, "chaptrix.log")
    error_log = os.path.join(log_dir, "error.log")
    debug_log = os.path.join(log_dir, "debug.log")
    
    # Define logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "error": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": main_log,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "error",
                "filename": error_log,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "debug_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": debug_log,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3
            }
        },
        "loggers": {
            "Chaptrix": {
                "level": "DEBUG" if debug_mode else "INFO",
                "handlers": ["console", "file", "error_file", "debug_file"],
                "propagate": False
            },
            "Chaptrix.stitcher": {
                "level": "DEBUG" if debug_mode else "INFO",
                "handlers": ["console", "file", "error_file", "debug_file"],
                "propagate": False
            },
            "Chaptrix.banner_cropper": {
                "level": "DEBUG" if debug_mode else "INFO",
                "handlers": ["console", "file", "error_file", "debug_file"],
                "propagate": False
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    return logging.getLogger("Chaptrix")

# Usage
logger = configure_logging(debug_mode=True)
```

### 8. Add User-Friendly Logging

Implement user-friendly logging for important events:

```python
def log_user_event(event_type, message, details=None):
    """Log user-friendly events"""
    user_logger = logging.getLogger("Chaptrix.user")
    
    # Log the event
    if details:
        user_logger.info(f"[{event_type}] {message} | {details}")
    else:
        user_logger.info(f"[{event_type}] {message}")

# Usage
log_user_event("NEW_CHAPTER", "New chapter found", "Comic: Test Comic, Chapter: 10")
log_user_event("UPLOAD_SUCCESS", "Chapter uploaded to Google Drive", "Link: https://drive.google.com/...")
```

## Implementation Plan

### Phase 1: Basic Improvements

1. Implement log rotation
2. Create component-specific loggers
3. Add contextual information to log messages

### Phase 2: Advanced Features

1. Implement structured logging
2. Add performance logging
3. Create a logging configuration file

### Phase 3: Integration

1. Update all modules to use the new logging system
2. Add user-friendly logging for important events
3. Create log analysis tools or dashboards

## Best Practices

1. **Be Consistent**: Use the same logging pattern throughout the codebase
2. **Log at the Right Level**: Use appropriate log levels for different types of events
3. **Include Context**: Add relevant context to log messages
4. **Avoid Sensitive Information**: Never log sensitive information like passwords or tokens
5. **Performance Considerations**: Be mindful of logging overhead in performance-critical sections

## Conclusion

Implementing these logging improvements will significantly enhance the debuggability and maintainability of the Chaptrix application. A well-designed logging system provides valuable insights into application behavior, helps identify issues quickly, and improves the overall development experience.