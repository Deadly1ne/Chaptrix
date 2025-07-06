# Error Handling Best Practices

## Overview

This document provides recommendations for improving error handling throughout the Chaptrix application. Proper error handling is crucial for creating a robust, user-friendly application that can recover gracefully from unexpected situations.

## Current State

The application has recently been improved with a centralized `handle_error()` function in `main.py`, which is a good start. However, there are still opportunities to enhance error handling throughout the codebase.

## Recommendations

### 1. Expand the Centralized Error Handler

Enhance the existing `handle_error()` function to provide more functionality:

```python
def handle_error(error, context="operation", critical=False, notify=False, recovery_action=None):
    """Centralized error handling function
    
    Args:
        error: The exception object
        context: String describing where the error occurred
        critical: Boolean indicating if this is a critical error
        notify: Boolean indicating if user notification is needed
        recovery_action: Optional function to attempt recovery
        
    Returns:
        Boolean indicating if recovery was successful
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if critical:
        logger.critical(f"CRITICAL ERROR in {context}: {error_type} - {error_msg}")
    else:
        logger.error(f"Error in {context}: {error_type} - {error_msg}")
    
    # Attempt recovery if a recovery action is provided
    if recovery_action and callable(recovery_action):
        try:
            logger.info(f"Attempting recovery for {context}...")
            recovery_action()
            logger.info(f"Recovery successful for {context}")
            return True
        except Exception as recovery_error:
            logger.error(f"Recovery failed for {context}: {str(recovery_error)}")
    
    # User notification for important errors
    if notify and settings.get("error_notifications", False):
        try:
            send_error_notification(context, error_type, error_msg)
        except Exception as notify_error:
            logger.error(f"Failed to send error notification: {str(notify_error)}")
    
    return False
```

### 2. Create Error Types for Different Scenarios

Define custom exception classes for different error scenarios:

```python
class ChaptrixError(Exception):
    """Base exception class for Chaptrix errors"""
    pass

class ConfigurationError(ChaptrixError):
    """Error related to configuration issues"""
    pass

class NetworkError(ChaptrixError):
    """Error related to network connectivity issues"""
    pass

class ScrapingError(ChaptrixError):
    """Error related to web scraping issues"""
    pass

class ProcessingError(ChaptrixError):
    """Error related to image processing issues"""
    pass

class IntegrationError(ChaptrixError):
    """Error related to external integrations"""
    pass
```

### 3. Implement Context Managers for Common Operations

Create context managers for operations that need consistent error handling:

```python
class NetworkOperation:
    """Context manager for network operations with retry logic"""
    def __init__(self, operation_name, max_retries=3, retry_delay=1):
        self.operation_name = operation_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.attempt = 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False  # No exception occurred
        
        if issubclass(exc_type, requests.RequestException):
            self.attempt += 1
            if self.attempt <= self.max_retries:
                logger.warning(f"{self.operation_name} failed (attempt {self.attempt}/{self.max_retries}): {exc_val}")
                logger.warning(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                return True  # Suppress exception and retry
        
        # Log the error using the centralized handler
        handle_error(exc_val, self.operation_name)
        return False  # Don't suppress the exception
```

Usage example:

```python
def download_image(url, save_path):
    with NetworkOperation("Image download", max_retries=3):
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return save_path
```

### 4. Add Graceful Degradation

Implement graceful degradation for optional features:

```python
def send_discord_notification(message, embed=None, file_path=None):
    """Send a Discord notification with graceful degradation"""
    settings = load_settings()
    webhook_url = settings.get("discord_webhook_url", "")
    
    if not webhook_url:
        logger.info("Discord webhook URL not configured. Skipping notification.")
        return False
    
    try:
        # Attempt to send with file attachment if provided
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(webhook_url, json={"content": message, "embeds": [embed] if embed else []}, files=files)
        else:
            response = requests.post(webhook_url, json={"content": message, "embeds": [embed] if embed else []})
        
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        handle_error(e, "Discord notification")
        
        # Graceful degradation: try without file attachment
        if file_path:
            logger.info("Retrying Discord notification without file attachment...")
            try:
                response = requests.post(webhook_url, json={"content": message, "embeds": [embed] if embed else []})
                response.raise_for_status()
                logger.info("Discord notification sent without file attachment")
                return True
            except requests.RequestException as retry_e:
                handle_error(retry_e, "Discord notification retry")
        
        return False
```

### 5. Implement a Retry Decorator

Create a retry decorator for functions that may fail due to transient issues:

```python
def retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """Retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_attempts, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    msg = f"{func.__name__} failed. Retrying in {mdelay} seconds... ({mtries-1} attempts remaining)"
                    logger.warning(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)  # Last attempt
        return wrapper
    return decorator
```

Usage example:

```python
@retry(max_attempts=3, exceptions=(requests.RequestException,))
def fetch_page(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text
```

### 6. Add Comprehensive Error Logging

Enhance error logging to include more context:

```python
def enhanced_exception_hook(exc_type, exc_value, exc_traceback):
    """Enhanced exception hook for uncaught exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Call the default handler for KeyboardInterrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log the full exception with traceback
    logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Add additional context if available
    try:
        import platform
        import psutil
        
        # System information
        logger.critical(f"System: {platform.system()} {platform.release()}")
        
        # Memory usage
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        logger.critical(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
    except ImportError:
        pass

# Set the enhanced exception hook
sys.excepthook = enhanced_exception_hook
```

### 7. Implement Feature Flags for Risky Operations

Use feature flags to control risky operations:

```python
def is_feature_enabled(feature_name, default=True):
    """Check if a feature is enabled in settings"""
    settings = load_settings()
    features = settings.get("features", {})
    return features.get(feature_name, default)

# Usage example
if is_feature_enabled("experimental_stitching"):
    try:
        result = experimental_stitch_function(images)
        logger.info("Experimental stitching successful")
        return result
    except Exception as e:
        handle_error(e, "Experimental stitching")
        logger.info("Falling back to standard stitching")

# Standard stitching as fallback
return standard_stitch_function(images)
```

## Implementation Priority

1. **High Priority**:
   - Expand the centralized error handler
   - Implement graceful degradation for external services
   - Add comprehensive error logging

2. **Medium Priority**:
   - Create custom exception types
   - Implement the retry decorator
   - Add feature flags for risky operations

3. **Low Priority**:
   - Implement context managers for common operations
   - Add telemetry for error tracking

## Conclusion

Implementing these error handling best practices will significantly improve the robustness and reliability of the Chaptrix application. By properly handling errors, providing clear error messages, and implementing recovery mechanisms, the application will be more resilient to unexpected situations and provide a better user experience.