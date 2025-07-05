# Error Handling and Recovery System for Chaptrix

## Introduction

This document outlines a comprehensive error handling and recovery system for Chaptrix. The goal is to make the application more robust, maintainable, and user-friendly by implementing a structured approach to error handling, reporting, and recovery.

## Benefits

- **Improved Reliability**: Graceful handling of errors prevents crashes and ensures the application can continue functioning even when parts of it fail.
- **Better User Experience**: Clear error messages and automatic recovery mechanisms provide a smoother experience for users.
- **Easier Debugging**: Structured error reporting makes it easier to identify and fix issues.
- **Reduced Maintenance Burden**: A consistent approach to error handling reduces the effort required to maintain and extend the codebase.

## Proposed Architecture

### 1. Error Classification

A hierarchy of custom exception classes to categorize different types of errors:

```
ChaptrixError (base class)
├── NetworkError
│   ├── ConnectionError
│   ├── TimeoutError
│   └── AuthenticationError
├── ParsingError
│   ├── HTMLParsingError
│   └── JSONParsingError
├── StorageError
│   ├── FileSystemError
│   └── GoogleDriveError
├── NotificationError
│   ├── DiscordWebhookError
│   └── DiscordBotError
└── ImageProcessingError
    ├── StitchingError
    └── CroppingError
```

### 2. Error Handling Strategies

- **Retry**: Automatically retry operations that might fail due to transient issues (e.g., network connectivity).
- **Fallback**: Provide alternative methods when primary methods fail (e.g., simplified image processing when advanced processing fails).
- **Circuit Breaker**: Prevent cascading failures by temporarily disabling operations that consistently fail.
- **Graceful Degradation**: Continue with reduced functionality when non-critical components fail.

### 3. Centralized Error Handling

A centralized error handler to provide consistent error handling across the application:

- Log errors with appropriate severity levels
- Report errors to monitoring systems
- Execute recovery actions when possible
- Provide clear error messages to users

### 4. Enhanced Logging

Structured logging with contextual information to aid debugging:

- Error type and message
- Stack trace
- Context (e.g., function name, parameters)
- Timestamp
- Severity level

## Implementation Steps

### 1. Define Custom Exception Classes

Create a hierarchy of custom exception classes in `errors.py`:

```python
class ChaptrixError(Exception):
    """Base class for all Chaptrix exceptions"""
    def __init__(self, message, error_code=None, details=None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.datetime.now().isoformat()

    def to_dict(self):
        """Convert exception to dictionary for serialization"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details,
            'timestamp': self.timestamp
        }

class NetworkError(ChaptrixError):
    """Error related to network operations"""
    pass

class ConnectionError(NetworkError):
    """Error connecting to a remote server"""
    pass

class TimeoutError(NetworkError):
    """Error when a network operation times out"""
    pass

class AuthenticationError(NetworkError):
    """Error authenticating with a remote server"""
    pass

class ParsingError(ChaptrixError):
    """Error parsing data"""
    pass

class HTMLParsingError(ParsingError):
    """Error parsing HTML data"""
    pass

class JSONParsingError(ParsingError):
    """Error parsing JSON data"""
    pass

class StorageError(ChaptrixError):
    """Error related to storage operations"""
    pass

class FileSystemError(StorageError):
    """Error accessing the file system"""
    pass

class GoogleDriveError(StorageError):
    """Error accessing Google Drive"""
    pass

class NotificationError(ChaptrixError):
    """Error sending notifications"""
    pass

class DiscordWebhookError(NotificationError):
    """Error sending Discord webhook notifications"""
    pass

class DiscordBotError(NotificationError):
    """Error sending Discord bot notifications"""
    pass

class ImageProcessingError(ChaptrixError):
    """Error processing images"""
    pass

class StitchingError(ImageProcessingError):
    """Error stitching images"""
    pass

class CroppingError(ImageProcessingError):
    """Error cropping images"""
    pass
```

### 2. Implement Centralized Error Handler

Create a centralized error handler in `error_handler.py`:

```python
import logging
import traceback
import threading
from collections import defaultdict, deque
from typing import Dict, List, Any, Callable, Optional
from errors import ChaptrixError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chaptrix_error.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('chaptrix.error_handler')

class ErrorHandler:
    """Centralized error handler for Chaptrix"""
    
    def __init__(self):
        """Initialize error handler"""
        self._lock = threading.RLock()
        self._error_counts = defaultdict(int)
        self._recent_errors = deque(maxlen=100)
        self._error_handlers = {}
        self._default_handler = self._default_error_handler
    
    def register_handler(self, error_type: type, handler: Callable[[Exception, Dict[str, Any]], None]) -> None:
        """Register a handler for a specific error type
        
        Args:
            error_type: Type of error to handle
            handler: Function to handle the error
        """
        with self._lock:
            self._error_handlers[error_type] = handler
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle an error
        
        Args:
            error: Error to handle
            context: Additional context for the error
        """
        context = context or {}
        error_type = type(error)
        
        # Log the error
        self._log_error(error, context)
        
        # Update error statistics
        with self._lock:
            self._error_counts[error_type.__name__] += 1
            self._recent_errors.append((error, context))
        
        # Find and call the appropriate handler
        handler = self._find_handler(error_type)
        handler(error, context)
    
    def _find_handler(self, error_type: type) -> Callable[[Exception, Dict[str, Any]], None]:
        """Find the appropriate handler for an error type
        
        Args:
            error_type: Type of error to handle
            
        Returns:
            Function to handle the error
        """
        with self._lock:
            # Check for exact match
            if error_type in self._error_handlers:
                return self._error_handlers[error_type]
            
            # Check for parent class match
            for registered_type, handler in self._error_handlers.items():
                if issubclass(error_type, registered_type):
                    return handler
            
            # Use default handler
            return self._default_handler
    
    def _log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log an error
        
        Args:
            error: Error to log
            context: Additional context for the error
        """
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        # Determine log level based on error type
        if isinstance(error, ChaptrixError):
            log_level = logging.ERROR
        else:
            log_level = logging.CRITICAL
        
        # Log the error
        logger.log(log_level, f"Error: {error_message}")
        logger.log(log_level, f"Context: {context}")
        logger.log(log_level, f"Stack trace: {stack_trace}")
    
    def _default_error_handler(self, error: Exception, context: Dict[str, Any]) -> None:
        """Default error handler
        
        Args:
            error: Error to handle
            context: Additional context for the error
        """
        # Default behavior is to log the error (already done in _log_error)
        pass
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics
        
        Returns:
            Dictionary of error statistics
        """
        with self._lock:
            return {
                'error_counts': dict(self._error_counts),
                'recent_errors': [
                    {
                        'error_type': type(error).__name__,
                        'message': str(error),
                        'context': context
                    }
                    for error, context in self._recent_errors
                ]
            }

# Singleton instance
_error_handler = None
_error_handler_lock = threading.RLock()

def get_error_handler() -> ErrorHandler:
    """Get the singleton error handler instance
    
    Returns:
        ErrorHandler instance
    """
    global _error_handler
    with _error_handler_lock:
        if _error_handler is None:
            _error_handler = ErrorHandler()
        return _error_handler
```

### 3. Implement Retry Decorator

Create a retry decorator in `retry.py`:

```python
import time
import logging
import functools
from typing import Tuple, Type, Callable, TypeVar, Any, Optional

logger = logging.getLogger('chaptrix.retry')

T = TypeVar('T')

def retry(
    max_attempts: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry a function on failure
    
    Args:
        max_attempts: Maximum number of attempts
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Factor to increase delay between retries
        exceptions: Exceptions to retry on
        on_retry: Function to call on retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            delay = retry_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        if on_retry:
                            on_retry(e, attempt)
                        
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            # If we get here, all attempts failed
            if last_exception:
                raise last_exception
            
            # This should never happen, but just in case
            raise RuntimeError(f"All {max_attempts} attempts failed for {func.__name__}")
        
        return wrapper
    
    return decorator
```

### 4. Implement Circuit Breaker

Create a circuit breaker in `circuit_breaker.py`:

```python
import time
import logging
import functools
import threading
from enum import Enum
from typing import Tuple, Type, Callable, TypeVar, Any, Dict, Optional

logger = logging.getLogger('chaptrix.circuit_breaker')

T = TypeVar('T')

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = 'CLOSED'  # Normal operation, requests are allowed
    OPEN = 'OPEN'      # Circuit is open, requests are not allowed
    HALF_OPEN = 'HALF_OPEN'  # Testing if the circuit can be closed

class CircuitBreaker:
    """Circuit breaker to prevent cascading failures"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """Initialize circuit breaker
        
        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds before testing if the circuit can be closed
            exceptions: Exceptions to count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.exceptions = exceptions
        
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time = 0
        self._lock = threading.RLock()
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorate a function with circuit breaker
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with self._lock:
                if self._state == CircuitState.OPEN:
                    # Check if recovery timeout has elapsed
                    if time.time() - self._last_failure_time >= self.recovery_timeout:
                        logger.info(f"Circuit {self.name} is half-open, testing if it can be closed")
                        self._state = CircuitState.HALF_OPEN
                    else:
                        # Circuit is still open
                        raise CircuitBreakerOpenError(
                            f"Circuit {self.name} is open",
                            circuit_name=self.name,
                            recovery_time=self._last_failure_time + self.recovery_timeout - time.time()
                        )
            
            try:
                result = func(*args, **kwargs)
                
                # If we get here and the circuit is half-open, close it
                with self._lock:
                    if self._state == CircuitState.HALF_OPEN:
                        logger.info(f"Circuit {self.name} is now closed")
                        self._state = CircuitState.CLOSED
                        self._failure_count = 0
                
                return result
            except self.exceptions as e:
                with self._lock:
                    self._last_failure_time = time.time()
                    
                    if self._state == CircuitState.CLOSED:
                        self._failure_count += 1
                        
                        if self._failure_count >= self.failure_threshold:
                            logger.warning(
                                f"Circuit {self.name} is now open after {self._failure_count} failures"
                            )
                            self._state = CircuitState.OPEN
                    elif self._state == CircuitState.HALF_OPEN:
                        logger.warning(f"Circuit {self.name} remains open after test failure")
                        self._state = CircuitState.OPEN
                
                raise e
        
        return wrapper

class CircuitBreakerOpenError(Exception):
    """Error raised when a circuit breaker is open"""
    
    def __init__(self, message: str, circuit_name: str, recovery_time: float):
        """Initialize circuit breaker open error
        
        Args:
            message: Error message
            circuit_name: Name of the circuit breaker
            recovery_time: Time in seconds until the circuit breaker will be tested again
        """
        super().__init__(message)
        self.circuit_name = circuit_name
        self.recovery_time = recovery_time

# Registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = threading.RLock()

def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to apply circuit breaker pattern
    
    Args:
        name: Name of the circuit breaker
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Time in seconds before testing if the circuit can be closed
        exceptions: Exceptions to count as failures
        
    Returns:
        Decorated function
    """
    with _registry_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                exceptions=exceptions
            )
        
        return _circuit_breakers[name]

def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """Get a circuit breaker by name
    
    Args:
        name: Name of the circuit breaker
        
    Returns:
        CircuitBreaker instance or None if not found
    """
    with _registry_lock:
        return _circuit_breakers.get(name)

def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all circuit breakers
    
    Returns:
        Dictionary of circuit breakers
    """
    with _registry_lock:
        return dict(_circuit_breakers)
```

### 5. Implement Fallback Strategy

Create a fallback decorator in `fallback.py`:

```python
import logging
import functools
from typing import Tuple, Type, Callable, TypeVar, Any, Optional

logger = logging.getLogger('chaptrix.fallback')

T = TypeVar('T')

def fallback(
    fallback_function: Callable[..., T],
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_fallback: Optional[Callable[[Exception], None]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to provide fallback for a function on failure
    
    Args:
        fallback_function: Function to call as fallback
        exceptions: Exceptions to trigger fallback on
        on_fallback: Function to call when fallback is triggered
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.warning(
                    f"Function {func.__name__} failed with {type(e).__name__}: {str(e)}. "
                    f"Using fallback {fallback_function.__name__}."
                )
                
                if on_fallback:
                    on_fallback(e)
                
                return fallback_function(*args, **kwargs)
        
        return wrapper
    
    return decorator
```

### 6. Implement Error Reporting

Create an error reporting module in `error_reporting.py`:

```python
import os
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger('chaptrix.error_reporting')

# Directory to store error reports
ERROR_REPORTS_DIR = Path('error_reports')

def report_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
    """Report an error
    
    Args:
        error: Error to report
        context: Additional context for the error
        
    Returns:
        ID of the error report
    """
    context = context or {}
    
    # Create error report directory if it doesn't exist
    os.makedirs(ERROR_REPORTS_DIR, exist_ok=True)
    
    # Generate error report ID
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    error_id = f"{timestamp}_{type(error).__name__}"
    
    # Create error report
    error_report = {
        'error_id': error_id,
        'error_type': type(error).__name__,
        'message': str(error),
        'timestamp': datetime.datetime.now().isoformat(),
        'context': context
    }
    
    # Add details if available (for ChaptrixError)
    if hasattr(error, 'to_dict'):
        error_report.update(error.to_dict())
    
    # Save error report to file
    report_path = ERROR_REPORTS_DIR / f"{error_id}.json"
    with open(report_path, 'w') as f:
        json.dump(error_report, f, indent=2)
    
    logger.info(f"Error report saved to {report_path}")
    
    return error_id

def get_error_report(error_id: str) -> Optional[Dict[str, Any]]:
    """Get an error report by ID
    
    Args:
        error_id: ID of the error report
        
    Returns:
        Error report or None if not found
    """
    report_path = ERROR_REPORTS_DIR / f"{error_id}.json"
    
    if not report_path.exists():
        return None
    
    with open(report_path, 'r') as f:
        return json.load(f)

def get_all_error_reports() -> List[Dict[str, Any]]:
    """Get all error reports
    
    Returns:
        List of error reports
    """
    if not ERROR_REPORTS_DIR.exists():
        return []
    
    reports = []
    for report_path in ERROR_REPORTS_DIR.glob('*.json'):
        try:
            with open(report_path, 'r') as f:
                reports.append(json.load(f))
        except Exception as e:
            logger.error(f"Failed to load error report {report_path}: {str(e)}")
    
    # Sort by timestamp (newest first)
    reports.sort(key=lambda r: r.get('timestamp', ''), reverse=True)
    
    return reports
```

### 7. Implement Error Recovery

Create an error recovery module in `error_recovery.py`:

```python
import os
import logging
import threading
from typing import Dict, Any, List, Protocol, Optional
from errors import ChaptrixError, FileSystemError

logger = logging.getLogger('chaptrix.error_recovery')

class RecoveryAction(Protocol):
    """Protocol for recovery actions"""
    
    def can_recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Check if this action can recover from the error
        
        Args:
            error: Error to recover from
            context: Additional context for the error
            
        Returns:
            True if this action can recover from the error, False otherwise
        """
        ...
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Recover from an error
        
        Args:
            error: Error to recover from
            context: Additional context for the error
            
        Returns:
            True if recovery was successful, False otherwise
        """
        ...

class FileSystemRecovery:
    """Recovery action for file system errors"""
    
    def can_recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Check if this action can recover from the error
        
        Args:
            error: Error to recover from
            context: Additional context for the error
            
        Returns:
            True if this action can recover from the error, False otherwise
        """
        return isinstance(error, FileSystemError) and 'file_path' in context
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Recover from a file system error
        
        Args:
            error: Error to recover from
            context: Additional context for the error
            
        Returns:
            True if recovery was successful, False otherwise
        """
        file_path = context['file_path']
        
        try:
            # Check if the file exists
            if not os.path.exists(file_path):
                # Try to create the directory
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                logger.info(f"Created directory for {file_path}")
                return True
            
            # Check if the file is a backup file
            if file_path.endswith('.bak'):
                # Try to restore from backup
                original_path = file_path[:-4]
                if os.path.exists(original_path):
                    os.remove(file_path)
                    logger.info(f"Removed backup file {file_path}")
                    return True
            
            # Check if there's a backup file
            backup_path = f"{file_path}.bak"
            if os.path.exists(backup_path):
                # Try to restore from backup
                os.replace(backup_path, file_path)
                logger.info(f"Restored {file_path} from backup")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to recover from file system error: {str(e)}")
            return False

class ConfigurationRecovery:
    """Recovery action for configuration errors"""
    
    def __init__(self, validation_function):
        """Initialize configuration recovery
        
        Args:
            validation_function: Function to validate configuration
        """
        self.validation_function = validation_function
    
    def can_recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Check if this action can recover from the error
        
        Args:
            error: Error to recover from
            context: Additional context for the error
            
        Returns:
            True if this action can recover from the error, False otherwise
        """
        return 'config_file' in context
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Recover from a configuration error
        
        Args:
            error: Error to recover from
            context: Additional context for the error
            
        Returns:
            True if recovery was successful, False otherwise
        """
        config_file = context['config_file']
        
        try:
            # Try to validate and fix the configuration
            return self.validation_function(config_file)
        except Exception as e:
            logger.error(f"Failed to recover from configuration error: {str(e)}")
            return False

class ErrorRecoveryManager:
    """Manager for error recovery actions"""
    
    def __init__(self):
        """Initialize error recovery manager"""
        self._actions: List[RecoveryAction] = []
        self._lock = threading.RLock()
    
    def register_action(self, action: RecoveryAction) -> None:
        """Register a recovery action
        
        Args:
            action: Recovery action to register
        """
        with self._lock:
            self._actions.append(action)
    
    def recover(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """Recover from an error
        
        Args:
            error: Error to recover from
            context: Additional context for the error
            
        Returns:
            True if recovery was successful, False otherwise
        """
        context = context or {}
        
        with self._lock:
            for action in self._actions:
                if action.can_recover(error, context):
                    logger.info(f"Attempting to recover from {type(error).__name__} using {type(action).__name__}")
                    if action.recover(error, context):
                        logger.info(f"Successfully recovered from {type(error).__name__}")
                        return True
        
        logger.warning(f"Failed to recover from {type(error).__name__}")
        return False

# Singleton instance
_recovery_manager = None
_recovery_manager_lock = threading.RLock()

def get_recovery_manager() -> ErrorRecoveryManager:
    """Get the singleton error recovery manager instance
    
    Returns:
        ErrorRecoveryManager instance
    """
    global _recovery_manager
    with _recovery_manager_lock:
        if _recovery_manager is None:
            _recovery_manager = ErrorRecoveryManager()
        return _recovery_manager
```

### 8. Implement Safe File Operations

Create a module for safe file operations in `safe_file.py`:

```python
import os
import json
import shutil
import logging
from typing import Any, Dict, List, Optional, Union
from errors import FileSystemError

logger = logging.getLogger('chaptrix.safe_file')

def safe_read_file(file_path: str, default: Optional[str] = None) -> str:
    """Safely read a file
    
    Args:
        file_path: Path to the file
        default: Default value to return if the file doesn't exist
        
    Returns:
        File contents or default value
        
    Raises:
        FileSystemError: If the file doesn't exist and no default is provided
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        if default is not None:
            return default
        raise FileSystemError(f"File not found: {file_path}", details={'file_path': file_path})
    except Exception as e:
        raise FileSystemError(f"Failed to read file: {str(e)}", details={'file_path': file_path})

def safe_write_file(file_path: str, content: str) -> None:
    """Safely write to a file
    
    Args:
        file_path: Path to the file
        content: Content to write
        
    Raises:
        FileSystemError: If the file can't be written
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    
    # Create backup if the file exists
    if os.path.exists(file_path):
        backup_path = f"{file_path}.bak"
        try:
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            logger.warning(f"Failed to create backup of {file_path}: {str(e)}")
    
    # Write to a temporary file first
    temp_path = f"{file_path}.tmp"
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Replace the original file with the temporary file
        os.replace(temp_path, file_path)
    except Exception as e:
        # Clean up temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        
        raise FileSystemError(f"Failed to write file: {str(e)}", details={'file_path': file_path})

def safe_read_json(file_path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Safely read a JSON file
    
    Args:
        file_path: Path to the file
        default: Default value to return if the file doesn't exist
        
    Returns:
        JSON data or default value
        
    Raises:
        FileSystemError: If the file doesn't exist and no default is provided
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        if default is not None:
            return default
        raise FileSystemError(f"File not found: {file_path}", details={'file_path': file_path})
    except json.JSONDecodeError as e:
        # Try to recover from backup
        backup_path = f"{file_path}.bak"
        if os.path.exists(backup_path):
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        raise FileSystemError(f"Invalid JSON in file: {str(e)}", details={'file_path': file_path})
    except Exception as e:
        raise FileSystemError(f"Failed to read JSON file: {str(e)}", details={'file_path': file_path})

def safe_write_json(file_path: str, data: Union[Dict[str, Any], List[Any]]) -> None:
    """Safely write JSON to a file
    
    Args:
        file_path: Path to the file
        data: JSON data to write
        
    Raises:
        FileSystemError: If the file can't be written
    """
    try:
        content = json.dumps(data, indent=2)
        safe_write_file(file_path, content)
    except Exception as e:
        raise FileSystemError(f"Failed to write JSON file: {str(e)}", details={'file_path': file_path})

def safe_delete_file(file_path: str) -> bool:
    """Safely delete a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file was deleted, False if it didn't exist
        
    Raises:
        FileSystemError: If the file can't be deleted
    """
    try:
        if os.path.exists(file_path):
            # Create backup before deleting
            backup_path = f"{file_path}.bak"
            try:
                shutil.copy2(file_path, backup_path)
            except Exception as e:
                logger.warning(f"Failed to create backup of {file_path}: {str(e)}")
            
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        raise FileSystemError(f"Failed to delete file: {str(e)}", details={'file_path': file_path})
```

### 9. Create Error Monitoring Dashboard

Create a Streamlit dashboard for error monitoring in `error_dashboard.py`:

```python
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
from error_reporting import get_all_error_reports
from error_handler import get_error_handler

def main():
    """Main function for error monitoring dashboard"""
    st.set_page_config(page_title="Chaptrix Error Dashboard", page_icon="🔍", layout="wide")
    
    st.title("Chaptrix Error Dashboard")
    
    # Get error statistics
    error_handler = get_error_handler()
    error_stats = error_handler.get_error_statistics()
    
    # Display error counts
    st.header("Error Counts")
    
    error_counts = error_stats['error_counts']
    if error_counts:
        # Create DataFrame for chart
        error_df = pd.DataFrame({
            'Error Type': list(error_counts.keys()),
            'Count': list(error_counts.values())
        })
        error_df = error_df.sort_values('Count', ascending=False)
        
        # Display chart
        st.bar_chart(error_df.set_index('Error Type'))
    else:
        st.info("No errors recorded in this session.")
    
    # Display recent errors
    st.header("Recent Errors")
    
    recent_errors = error_stats['recent_errors']
    if recent_errors:
        for i, error in enumerate(recent_errors[:10]):
            with st.expander(f"{error['error_type']}: {error['message']}"):
                st.json(error)
    else:
        st.info("No recent errors in this session.")
    
    # Display error reports
    st.header("Error Reports")
    
    reports = get_all_error_reports()
    if reports:
        # Filter options
        error_types = sorted(set(report['error_type'] for report in reports))
        selected_types = st.multiselect("Filter by error type", error_types, default=error_types)
        
        # Filter reports
        filtered_reports = [report for report in reports if report['error_type'] in selected_types]
        
        # Display reports
        for report in filtered_reports[:20]:  # Limit to 20 reports for performance
            with st.expander(f"{report['error_type']}: {report['message']} ({report['timestamp']})"):
                st.json(report)
        
        # Display timeline
        st.subheader("Error Timeline")
        
        if filtered_reports:
            # Group errors by day
            timeline_data = {}
            for report in reports:
                timestamp = report.get('timestamp', '')
                if timestamp:
                    date = timestamp.split('T')[0]
                    if date not in timeline_data:
                        timeline_data[date] = 0
                    timeline_data[date] += 1
            
            # Create DataFrame for chart
            timeline_df = pd.DataFrame({
                'Date': list(timeline_data.keys()),
                'Count': list(timeline_data.values())
            })
            timeline_df['Date'] = pd.to_datetime(timeline_df['Date'])
            timeline_df = timeline_df.sort_values('Date')
            
            st.line_chart(timeline_df.set_index('Date'))
        else:
            st.info("No error reports found.")

if __name__ == "__main__":
    main()
```

### 10. Update Main Functions to Use Error Handling

Update the main functions to use the new error handling system:

```python
# unified_workflow.py (partial update)
from error_handler import get_error_handler
from error_reporting import report_error
from error_recovery import get_recovery_manager, FileSystemRecovery, ConfigurationRecovery
from errors import ChaptrixError, NetworkError, ParsingError, StorageError, NotificationError, ImageProcessingError
from retry import retry
from circuit_breaker import circuit_breaker
from fallback import fallback
from safe_file import safe_read_json, safe_write_json
from config_validator import ensure_valid_configuration

# Initialize error recovery
def initialize_error_recovery():
    """Initialize error recovery"""
    recovery_manager = get_recovery_manager()
    recovery_manager.register_action(FileSystemRecovery())
    recovery_manager.register_action(ConfigurationRecovery(ensure_valid_configuration))

# Example of using retry decorator
@retry(max_attempts=3, retry_delay=2.0, exceptions=(NetworkError, TimeoutError))
def download_image(url, save_path):
    """Download an image with automatic retries
    
    Args:
        url: URL of the image
        save_path: Path to save the image
        
    Returns:
        bool: True if download was successful, False otherwise
        
    Raises:
        NetworkError: If the download fails after all retries
    """
    try:
        # ... (download logic)
        return True
    except Exception as e:
        raise NetworkError(f"Failed to download image: {str(e)}", details={'url': url, 'save_path': save_path})

# Example of using circuit breaker
@circuit_breaker(name="discord_notification", failure_threshold=3, recovery_timeout=300.0, exceptions=(NotificationError,))
def send_discord_notification(webhook_url, message):
    """Send a Discord notification with circuit breaker protection
    
    Args:
        webhook_url: Discord webhook URL
        message: Message to send
        
    Returns:
        bool: True if notification was sent successfully, False otherwise
        
    Raises:
        NotificationError: If the notification fails
    """
    try:
        # ... (notification logic)
        return True
    except Exception as e:
        raise NotificationError(f"Failed to send Discord notification: {str(e)}", details={'webhook_url': webhook_url})

# Example of using fallback
def fallback_image_processing(image_path):
    """Fallback image processing function
    
    Args:
        image_path: Path to the image
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        # ... (simplified image processing logic)
        return True
    except Exception as e:
        logger.warning(f"Fallback image processing failed: {str(e)}")
        return False

@fallback(fallback_function=fallback_image_processing, exceptions=(ImageProcessingError,))
def process_image(image_path):
    """Process an image with fallback
    
    Args:
        image_path: Path to the image
        
    Returns:
        bool: True if processing was successful, False otherwise
        
    Raises:
        ImageProcessingError: If processing fails and fallback fails
    """
    try:
        # ... (image processing logic)
        return True
    except Exception as e:
        raise ImageProcessingError(f"Failed to process image: {str(e)}", details={'image_path': image_path})

# Example of using safe file operations
def load_comics(comics_file="comics.json"):
    """Load comics from file
    
    Args:
        comics_file: Path to comics file
        
    Returns:
        dict: Comics dictionary
    """
    try:
        return safe_read_json(comics_file, default={"sites": {}})
    except FileSystemError as e:
        # Report the error
        report_error(e, {'config_file': comics_file})
        
        # Try to recover
        if get_recovery_manager().recover(e, {'file_path': comics_file}):
            # Recovery successful, try again
            return safe_read_json(comics_file, default={"sites": {}})
        
        # Recovery failed, use default
        logger.error(f"Failed to load comics configuration, using default")
        return {"sites": {}}

def save_comics(comics_data, comics_file="comics.json"):
    """Save comics to file
    
    Args:
        comics_data: Comics dictionary
        comics_file: Path to comics file
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        safe_write_json(comics_file, comics_data)
        return True
    except FileSystemError as e:
        # Report the error
        report_error(e, {'config_file': comics_file})
        
        # Try to recover
        if get_recovery_manager().recover(e, {'file_path': comics_file}):
            # Recovery successful, try again
            try:
                safe_write_json(comics_file, comics_data)
                return True
            except Exception as retry_error:
                logger.error(f"Failed to save comics configuration after recovery: {str(retry_error)}")
        
        return False

# Example of using error handler in main function
def main():
    """Main function"""
    # Initialize error recovery
    initialize_error_recovery()
    
    # ... (existing code)
    
    try:
        # ... (main logic)
        pass
    except ChaptrixError as e:
        # Handle known errors
        error_handler = get_error_handler()
        error_handler.handle_error(e, {'function': 'main'})
        
        # Report the error
        report_error(e, {'function': 'main'})
        
        # Try to recover
        if get_recovery_manager().recover(e, {'function': 'main'}):
            # Recovery successful, continue with reduced functionality
            logger.info("Recovered from error, continuing with reduced functionality")
        else:
            # Recovery failed, exit
            logger.error("Failed to recover from error, exiting")
            return 1
    except Exception as e:
        # Handle unknown errors
        logger.critical(f"Unhandled error: {str(e)}")
        report_error(e, {'function': 'main'})
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
```

## Integration with GitHub Actions

To ensure that errors are properly handled in the GitHub Actions workflow, update the `unified-workflow.yml` file to include error handling:

```yaml
# Add to unified-workflow.yml
    - name: Run Unified Workflow
      run: |
        python unified_workflow.py
        if [ $? -ne 0 ]; then
          echo "::warning::Unified workflow encountered errors but continued execution"
        fi
```

## Best Practices for Error Handling

### 1. Be Specific with Exceptions

Use specific exception types rather than catching all exceptions:

```python
# Bad
try:
    # ... (code)
except Exception as e:
    # ... (handle error)

# Good
try:
    # ... (code)
except NetworkError as e:
    # ... (handle network error)
except ParsingError as e:
    # ... (handle parsing error)
except Exception as e:
    # ... (handle unexpected error)
```

### 2. Provide Context in Error Messages

Include relevant context in error messages:

```python
# Bad
raise NetworkError("Download failed")

# Good
raise NetworkError(
    f"Download failed for URL {url}",
    error_code="DOWNLOAD_FAILED",
    details={'url': url, 'status_code': response.status_code}
)
```

### 3. Log at Appropriate Levels

Use appropriate logging levels:

- `DEBUG`: Detailed information for debugging
- `INFO`: Confirmation that things are working as expected
- `WARNING`: Something unexpected happened, but the application can continue
- `ERROR`: Something failed, but the application can still function
- `CRITICAL`: A serious error that may prevent the application from continuing

### 4. Fail Fast, Recover Gracefully

Detect errors early, but recover gracefully:

```python
# Validate inputs early
def process_comic(comic_url):
    if not comic_url:
        raise ValueError("Comic URL cannot be empty")
    
    # ... (processing logic)
```

### 5. Use Context Managers

Use context managers for resource management:

```python
# Bad
f = open(file_path, 'r')
try:
    data = f.read()
finally:
    f.close()

# Good
with open(file_path, 'r') as f:
    data = f.read()
```

## Conclusion

Implementing a robust error handling and recovery system in Chaptrix will significantly improve the reliability, maintainability, and user experience of the application. By following the guidelines and implementing the components described in this document, Chaptrix will be better equipped to handle errors gracefully, recover from failures, and provide clear feedback to users and developers.

The key components of the error handling system are:

1. **Custom Exception Hierarchy**: A structured hierarchy of exception types for different error categories
2. **Centralized Error Handler**: A singleton error handler for consistent error handling across the application
3. **Retry Mechanism**: Automatic retries for transient errors
4. **Circuit Breaker**: Protection against cascading failures
5. **Fallback Strategies**: Alternative methods when primary methods fail
6. **Error Recovery**: Automatic recovery from certain types of errors
7. **Safe File Operations**: Robust file operations with backup and recovery
8. **Error Reporting**: Detailed error reports for debugging and monitoring
9. **Error Monitoring Dashboard**: A Streamlit dashboard for visualizing and analyzing errors

By implementing these components, Chaptrix will be more resilient to errors and provide a better experience for users, even when things go wrong.