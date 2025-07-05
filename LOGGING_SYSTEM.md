# Logging System Implementation Guide for Chaptrix

This guide outlines how to implement a comprehensive logging system for Chaptrix to improve debugging, monitoring, and troubleshooting capabilities.

## Benefits of a Robust Logging System

- **Enhanced Debugging**: Quickly identify and resolve issues
- **Improved Monitoring**: Track application behavior and performance
- **Better User Support**: Provide detailed information for troubleshooting
- **Historical Analysis**: Review past operations and identify patterns
- **Automated Alerting**: Set up notifications for critical issues

## Current Logging Implementation

Currently, Chaptrix uses basic logging with Python's built-in logging module. The implementation can be enhanced to provide more structured and comprehensive logging.

## Proposed Logging Architecture

### 1. Logging Levels

Implement a hierarchical logging system with appropriate levels:

- **DEBUG**: Detailed information for debugging
- **INFO**: General operational information
- **WARNING**: Indication of potential issues
- **ERROR**: Error events that might still allow the application to continue
- **CRITICAL**: Critical errors that may prevent the application from continuing

### 2. Log Formatting

Implement a consistent log format that includes:

- Timestamp
- Log level
- Module/component name
- Process/thread ID (for concurrent operations)
- Message
- Exception information (when applicable)

### 3. Log Handlers

Implement multiple log handlers for different purposes:

- **Console Handler**: Display logs in the terminal
- **File Handler**: Write logs to files with rotation
- **Stream Handler**: For integration with external logging systems

## Implementation Steps

### 1. Create a Logging Configuration Module

```python
# logging_config.py
import os
import logging
import logging.handlers
from datetime import datetime

def setup_logging(log_level=logging.INFO, log_dir="logs"):
    """Set up logging configuration
    
    Args:
        log_level: The logging level (default: INFO)
        log_dir: Directory to store log files (default: logs)
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"chaptrix_{timestamp}.log")
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:  
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    # Create a separate error log file
    error_log_file = os.path.join(log_dir, f"chaptrix_error_{timestamp}.log")
    error_file_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_file_handler)
    
    # Log the start of the application
    logging.info("Logging initialized")
    logging.info(f"Log level set to {logging.getLevelName(log_level)}")
    
    return root_logger

def get_logger(name):
    """Get a logger with the specified name
    
    Args:
        name: Name of the logger (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
```

### 2. Integrate Logging in Main Modules

Update the main modules to use the new logging system:

```python
# unified_workflow.py (partial update)
from logging_config import setup_logging, get_logger

# Initialize logging at the start of the script
setup_logging(log_level=logging.INFO)
logger = get_logger(__name__)

def unified_process_comic(comic_data, site_adapter, settings):
    """Process a comic using the unified workflow"""
    logger.info(f"Processing comic: {comic_data['title']}")
    try:
        # Existing code...
        logger.debug(f"Checking for new chapters after {comic_data['last_chapter']}")
        # More existing code...
        
        if new_chapters:
            logger.info(f"Found {len(new_chapters)} new chapter(s) for {comic_data['title']}")
            # Process new chapters...
        else:
            logger.info(f"No new chapters found for {comic_data['title']}")
            
        # More existing code...
        return True
    except Exception as e:
        logger.error(f"Error processing comic {comic_data['title']}: {str(e)}", exc_info=True)
        return False
```

### 3. Add Context-Specific Logging

Enhance logging with context-specific information:

```python
# site_adapters/base_adapter.py (partial update)
from logging_config import get_logger

class MangaSiteAdapter:
    """Base class for manga site adapters"""
    
    def __init__(self, site_name):
        self.site_name = site_name
        self.logger = get_logger(f"adapter.{site_name}")
        
    def get_chapters(self, comic_url, last_chapter=None):
        """Get chapters for a comic"""
        self.logger.info(f"Fetching chapters for {comic_url}")
        # Existing code...
        
    def download_chapter_images(self, chapter_url, download_path):
        """Download images for a chapter"""
        self.logger.info(f"Downloading images from {chapter_url} to {download_path}")
        try:
            # Existing code...
            self.logger.debug(f"Found {len(image_urls)} images in chapter")
            # More existing code...
            
            self.logger.info(f"Successfully downloaded {len(image_urls)} images")
            return image_paths
        except Exception as e:
            self.logger.error(f"Error downloading chapter {chapter_url}: {str(e)}", exc_info=True)
            raise
```

### 4. Add Performance Logging

Implement performance logging to track execution time:

```python
# utils/performance.py
import time
import functools
from logging_config import get_logger

logger = get_logger(__name__)

def log_execution_time(func):
    """Decorator to log the execution time of a function"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"{func.__name__} executed in {execution_time:.2f} seconds")
        return result
    return wrapper
```

Usage example:

```python
# stitcher.py (partial update)
from utils.performance import log_execution_time

@log_execution_time
def stitch_images_multi_page(image_paths, output_path, template_path=None):
    """Stitch multiple images into a single image"""
    # Existing code...
```

### 5. Add Error Tracking and Recovery

Implement error tracking and recovery mechanisms:

```python
# utils/error_handling.py
import functools
from logging_config import get_logger

logger = get_logger(__name__)

def retry(max_attempts=3, delay=1):
    """Decorator to retry a function on failure"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {str(e)}", exc_info=True)
                        raise
                    logger.warning(f"Attempt {attempts} failed: {str(e)}. Retrying in {delay} seconds...")
                    time.sleep(delay)
        return wrapper
    return decorator
```

Usage example:

```python
# site_adapters/some_adapter.py (partial update)
from utils.error_handling import retry

class SomeAdapter(MangaSiteAdapter):
    # Existing code...
    
    @retry(max_attempts=3, delay=2)
    def download_chapter_images(self, chapter_url, download_path):
        """Download images for a chapter with retry"""
        # Existing code...
```

### 6. Add Structured Logging for Complex Operations

Implement structured logging for complex operations:

```python
# utils/structured_logging.py
import json
import logging
from logging_config import get_logger

logger = get_logger(__name__)

class StructuredLogRecord:
    """Class for creating structured log records"""
    
    def __init__(self, operation, context=None):
        """Initialize a structured log record
        
        Args:
            operation: Name of the operation
            context: Dictionary with context information
        """
        self.operation = operation
        self.context = context or {}
        self.events = []
        self.start_time = None
        self.end_time = None
        
    def start(self):
        """Start the operation"""
        import time
        self.start_time = time.time()
        self._log_event("start", {})
        return self
        
    def end(self, status="success", error=None):
        """End the operation"""
        import time
        self.end_time = time.time()
        data = {"status": status}
        if error:
            data["error"] = str(error)
        self._log_event("end", data)
        
        # Log the complete record
        duration = self.end_time - self.start_time if self.start_time else None
        record = {
            "operation": self.operation,
            "context": self.context,
            "events": self.events,
            "duration": duration,
            "status": status
        }
        if error:
            record["error"] = str(error)
            logger.error(f"Operation {self.operation} failed: {json.dumps(record)}")
        else:
            logger.info(f"Operation {self.operation} completed: {json.dumps(record)}")
        
    def add_event(self, event_type, data=None):
        """Add an event to the log record"""
        self._log_event(event_type, data or {})
        return self
        
    def _log_event(self, event_type, data):
        """Log an event"""
        import time
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": data
        }
        self.events.append(event)
```

Usage example:

```python
# unified_workflow.py (partial update)
from utils.structured_logging import StructuredLogRecord

def unified_process_comic(comic_data, site_adapter, settings):
    """Process a comic using the unified workflow"""
    log_record = StructuredLogRecord(
        "process_comic",
        {"comic": comic_data["title"], "site": site_adapter.site_name}
    ).start()
    
    try:
        # Check for new chapters
        new_chapters = site_adapter.get_chapters(comic_data["url"], comic_data["last_chapter"])
        log_record.add_event("chapters_checked", {"count": len(new_chapters)})
        
        # Process new chapters
        if new_chapters:
            for chapter in new_chapters:
                # Download images
                log_record.add_event("download_started", {"chapter": chapter["number"]})
                # Existing code...
                log_record.add_event("download_completed", {"chapter": chapter["number"]})
                
                # Stitch images
                log_record.add_event("stitch_started", {"chapter": chapter["number"]})
                # Existing code...
                log_record.add_event("stitch_completed", {"chapter": chapter["number"]})
        
        log_record.end("success")
        return True
    except Exception as e:
        log_record.end("failure", str(e))
        return False
```

## Advanced Logging Features

### 1. Log Aggregation

Implement log aggregation for distributed deployments:

```python
# logging_config.py (additional code)
def setup_remote_logging(log_server_url, app_name="chaptrix"):
    """Set up remote logging to a log aggregation server
    
    Args:
        log_server_url: URL of the log server
        app_name: Name of the application
    """
    import logging
    import socket
    import json
    import requests
    from logging.handlers import HTTPHandler
    
    class JSONHTTPHandler(HTTPHandler):
        """Custom HTTP handler that sends logs as JSON"""
        
        def __init__(self, url, app_name):
            super().__init__(url, "/", method="POST")
            self.app_name = app_name
            self.hostname = socket.gethostname()
            
        def mapLogRecord(self, record):
            """Map log record to JSON format"""
            log_data = {
                "app": self.app_name,
                "hostname": self.hostname,
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "timestamp": record.created,
                "logger": record.name
            }
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_data)
    
    # Create HTTP handler
    http_handler = JSONHTTPHandler(log_server_url, app_name)
    http_handler.setLevel(logging.WARNING)  # Only send warnings and above
    
    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(http_handler)
    
    logging.info(f"Remote logging configured to {log_server_url}")
```

### 2. Log Analysis Tools

Implement a simple log analysis script:

```python
# scripts/analyze_logs.py
import os
import re
import sys
import json
from collections import Counter, defaultdict
from datetime import datetime

def parse_log_line(line):
    """Parse a log line into components"""
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([\w\.]+) - (\w+) - (.+)'
    match = re.match(pattern, line)
    if match:
        timestamp_str, logger, level, message = match.groups()
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
        return {
            "timestamp": timestamp,
            "logger": logger,
            "level": level,
            "message": message
        }
    return None

def analyze_logs(log_file):
    """Analyze a log file and print statistics"""
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return
    
    # Counters for statistics
    level_counts = Counter()
    logger_counts = Counter()
    error_messages = []
    operation_durations = defaultdict(list)
    
    # Parse log file
    with open(log_file, 'r') as f:
        for line in f:
            log_entry = parse_log_line(line.strip())
            if not log_entry:
                continue
                
            # Count log levels
            level_counts[log_entry["level"]] += 1
            
            # Count loggers
            logger_counts[log_entry["logger"]] += 1
            
            # Collect error messages
            if log_entry["level"] in ["ERROR", "CRITICAL"]:
                error_messages.append(log_entry)
                
            # Extract operation durations
            if "executed in" in log_entry["message"]:
                match = re.search(r"([\w\.]+) executed in ([\d\.]+) seconds", log_entry["message"])
                if match:
                    operation, duration = match.groups()
                    operation_durations[operation].append(float(duration))
    
    # Print statistics
    print(f"Log Analysis for {log_file}")
    print("=" * 50)
    
    print("\nLog Level Distribution:")
    for level, count in level_counts.most_common():
        print(f"  {level}: {count}")
    
    print("\nLogger Distribution:")
    for logger, count in logger_counts.most_common(10):  # Top 10
        print(f"  {logger}: {count}")
    
    print("\nOperation Performance:")
    for operation, durations in operation_durations.items():
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        print(f"  {operation}:")
        print(f"    Count: {len(durations)}")
        print(f"    Avg: {avg_duration:.2f}s")
        print(f"    Min: {min_duration:.2f}s")
        print(f"    Max: {max_duration:.2f}s")
    
    print(f"\nErrors ({len(error_messages)}):")
    for i, error in enumerate(error_messages[:10], 1):  # Top 10
        print(f"  {i}. [{error['timestamp']}] {error['message']}")
    
    if len(error_messages) > 10:
        print(f"  ... and {len(error_messages) - 10} more errors")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_logs.py <log_file>")
        sys.exit(1)
    
    analyze_logs(sys.argv[1])
```

### 3. Log Visualization

Implement a simple log visualization dashboard using Streamlit:

```python
# scripts/log_dashboard.py
import os
import re
import glob
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from collections import Counter

# Function to parse log files
def parse_log_files(log_dir, days=7):
    """Parse log files from the specified directory"""
    # Find log files
    log_files = glob.glob(os.path.join(log_dir, "chaptrix_*.log"))
    
    # Filter by date
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Parse log entries
    log_entries = []
    
    for log_file in log_files:
        with open(log_file, 'r') as f:
            for line in f:
                # Parse log line
                pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([\w\.]+) - (\w+) - (.+)'
                match = re.match(pattern, line.strip())
                if match:
                    timestamp_str, logger, level, message = match.groups()
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                    
                    # Skip old entries
                    if timestamp < cutoff_date:
                        continue
                    
                    log_entries.append({
                        "timestamp": timestamp,
                        "logger": logger,
                        "level": level,
                        "message": message
                    })
    
    return pd.DataFrame(log_entries)

# Streamlit app
st.title("Chaptrix Log Dashboard")

# Sidebar
st.sidebar.header("Settings")
log_dir = st.sidebar.text_input("Log Directory", "logs")
days = st.sidebar.slider("Days to Show", 1, 30, 7)

# Load data
if os.path.exists(log_dir):
    df = parse_log_files(log_dir, days)
    
    if len(df) > 0:
        st.write(f"Found {len(df)} log entries from the past {days} days")
        
        # Overview metrics
        st.header("Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Logs", len(df))
        with col2:
            st.metric("Errors", len(df[df['level'].isin(['ERROR', 'CRITICAL'])]))
        with col3:
            st.metric("Unique Loggers", df['logger'].nunique())
        
        # Log level distribution
        st.header("Log Level Distribution")
        level_counts = df['level'].value_counts()
        st.bar_chart(level_counts)
        
        # Time series of logs
        st.header("Logs Over Time")
        df['date'] = df['timestamp'].dt.date
        date_counts = df.groupby(['date', 'level']).size().unstack().fillna(0)
        st.line_chart(date_counts)
        
        # Error logs
        st.header("Recent Errors")
        error_df = df[df['level'].isin(['ERROR', 'CRITICAL'])].sort_values('timestamp', ascending=False)
        if len(error_df) > 0:
            for _, row in error_df.head(10).iterrows():
                st.error(f"[{row['timestamp']}] {row['logger']}: {row['message']}")
        else:
            st.success("No errors found!")
        
        # Log explorer
        st.header("Log Explorer")
        selected_level = st.selectbox("Log Level", ['All'] + list(df['level'].unique()))
        selected_logger = st.selectbox("Logger", ['All'] + list(df['logger'].unique()))
        search_term = st.text_input("Search in messages")
        
        filtered_df = df.copy()
        if selected_level != 'All':
            filtered_df = filtered_df[filtered_df['level'] == selected_level]
        if selected_logger != 'All':
            filtered_df = filtered_df[filtered_df['logger'] == selected_logger]
        if search_term:
            filtered_df = filtered_df[filtered_df['message'].str.contains(search_term, case=False)]
        
        st.write(f"Found {len(filtered_df)} matching logs")
        st.dataframe(filtered_df[['timestamp', 'level', 'logger', 'message']].sort_values('timestamp', ascending=False))
    else:
        st.warning(f"No log entries found in the past {days} days")
else:
    st.error(f"Log directory not found: {log_dir}")
```

## Integration with External Logging Services

### 1. Sentry Integration

Implement Sentry integration for error tracking:

```python
# logging_config.py (additional code)
def setup_sentry(dsn, environment="production"):
    """Set up Sentry integration for error tracking
    
    Args:
        dsn: Sentry DSN
        environment: Environment name
    """
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        # Set up Sentry logging integration
        sentry_logging = LoggingIntegration(
            level=logging.INFO,        # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )
        
        # Initialize Sentry SDK
        sentry_sdk.init(
            dsn=dsn,
            integrations=[sentry_logging],
            environment=environment,
            traces_sample_rate=0.1,  # Adjust sampling rate as needed
        )
        
        logging.info(f"Sentry initialized for environment: {environment}")
    except ImportError:
        logging.warning("Sentry SDK not installed. Error tracking disabled.")
```

### 2. ELK Stack Integration

Implement integration with ELK Stack (Elasticsearch, Logstash, Kibana):

```python
# logging_config.py (additional code)
def setup_elk_logging(logstash_host, logstash_port, app_name="chaptrix"):
    """Set up logging to ELK Stack via Logstash
    
    Args:
        logstash_host: Logstash host
        logstash_port: Logstash port
        app_name: Application name
    """
    try:
        import socket
        from logstash_async.handler import AsynchronousLogstashHandler
        from logstash_async.formatter import LogstashFormatter
        
        # Create logstash handler
        logstash_handler = AsynchronousLogstashHandler(
            host=logstash_host,
            port=logstash_port,
            database_path='logstash.db'
        )
        
        # Create formatter
        formatter = LogstashFormatter(
            message_type='python-logstash',
            extra={
                'app': app_name,
                'hostname': socket.gethostname()
            }
        )
        logstash_handler.setFormatter(formatter)
        
        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(logstash_handler)
        
        logging.info(f"ELK Stack logging configured to {logstash_host}:{logstash_port}")
    except ImportError:
        logging.warning("logstash_async not installed. ELK Stack logging disabled.")
```

## Conclusion

Implementing a comprehensive logging system for Chaptrix will significantly improve debugging, monitoring, and troubleshooting capabilities. The proposed architecture provides a solid foundation that can be extended as needed.

Key benefits of the proposed logging system include:

1. **Hierarchical Logging**: Different log levels for different types of information
2. **Structured Logging**: Consistent format for easy parsing and analysis
3. **Multiple Handlers**: Console, file, and remote logging options
4. **Performance Tracking**: Monitor execution time of critical operations
5. **Error Handling**: Robust error tracking and recovery mechanisms
6. **Log Analysis**: Tools for analyzing and visualizing logs
7. **External Integration**: Options for integrating with external logging services

By following this guide, you'll establish a robust logging system that will help maintain high reliability and provide valuable insights into the operation of Chaptrix.