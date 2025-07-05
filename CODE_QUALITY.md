# Code Quality Improvements for Chaptrix

This document provides recommendations for enhancing the code quality, maintainability, and reliability of the Chaptrix project.

## Architecture Improvements

### 1. Modular Design

- **Current State**: The project has some modularization with separate files for stitching, banner cropping, and main functionality.
- **Recommendation**: Further separate concerns by creating dedicated modules for:
  - Site adapters (move from `main.py` to `adapters/`)
  - Discord notifications (move to `notifications/`)
  - Google Drive integration (move to `cloud/`)
  - Configuration management (move to `config/`)

```
chaptrix/
├── adapters/
│   ├── __init__.py
│   ├── base.py  # Base adapter class
│   ├── baozimh.py
│   └── [other_sites].py
├── cloud/
│   ├── __init__.py
│   └── google_drive.py
├── notifications/
│   ├── __init__.py
│   ├── discord_webhook.py
│   └── discord_bot.py
├── processing/
│   ├── __init__.py
│   ├── stitcher.py
│   └── banner_cropper.py
├── config/
│   ├── __init__.py
│   └── settings.py
└── main.py
```

### 2. Dependency Injection

- **Current State**: Direct imports and instantiation of components.
- **Recommendation**: Implement dependency injection to improve testability and flexibility.

```python
class ComicProcessor:
    def __init__(self, site_adapter, image_processor, notifier, cloud_storage):
        self.site_adapter = site_adapter
        self.image_processor = image_processor
        self.notifier = notifier
        self.cloud_storage = cloud_storage
        
    def process_comic(self, comic_data):
        # Use injected dependencies
```

## Code Quality Improvements

### 1. Error Handling

- **Current State**: Basic error handling with try/except blocks.
- **Recommendation**: Implement more robust error handling:
  - Create custom exception classes
  - Add detailed logging for each exception
  - Implement graceful degradation (continue processing other comics if one fails)

```python
class SiteAdapterError(Exception):
    """Base exception for site adapter errors."""
    pass

class ConnectionError(SiteAdapterError):
    """Raised when connection to the site fails."""
    pass

class ParsingError(SiteAdapterError):
    """Raised when parsing the site content fails."""
    pass

# Usage
try:
    chapter_data = adapter.get_latest_chapter()
except ConnectionError as e:
    logger.error(f"Connection error for {comic_name}: {e}")
    # Implement retry logic or skip
except ParsingError as e:
    logger.error(f"Parsing error for {comic_name}: {e}")
    # Handle parsing errors
except SiteAdapterError as e:
    logger.error(f"General adapter error for {comic_name}: {e}")
    # Handle general errors
```

### 2. Type Hints

- **Current State**: Limited or no type hints.
- **Recommendation**: Add comprehensive type hints to improve code readability and enable static type checking.

```python
from typing import List, Dict, Optional, Union, Tuple

def stitch_images_multi_page(image_paths: List[str], width: int, height: Optional[int] = 0) -> List[Image.Image]:
    """Stitch multiple images into pages.
    
    Args:
        image_paths: List of paths to images to stitch
        width: Target width for the stitched image
        height: Optional target height (0 means auto-calculate)
        
    Returns:
        List of stitched PIL Image objects
    """
```

### 3. Configuration Validation

- **Current State**: Basic configuration loading without validation.
- **Recommendation**: Implement schema validation for configuration files.

```python
from pydantic import BaseModel, HttpUrl, validator

class ComicConfig(BaseModel):
    name: str
    url: HttpUrl
    last_known_chapter: str
    template_image: Optional[str] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v
```

### 4. Unit Testing

- **Current State**: Some test files exist but coverage may be limited.
- **Recommendation**: Expand test coverage with:
  - Unit tests for each module
  - Integration tests for workflows
  - Mock objects for external dependencies

```python
import unittest
from unittest.mock import MagicMock, patch
from adapters.baozimh import BaozimhAdapter

class TestBaozimhAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = BaozimhAdapter()
        
    @patch('requests.get')
    def test_get_latest_chapter(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html>...</html>'  # Sample HTML
        mock_get.return_value = mock_response
        
        # Test the method
        result = self.adapter.get_latest_chapter('test-comic')
        
        # Assertions
        self.assertEqual(result['chapter'], 'Chapter 10')
        mock_get.assert_called_once()
```

## Performance Improvements

### 1. Asynchronous Processing

- **Current State**: Synchronous processing of comics.
- **Recommendation**: Implement asynchronous processing to improve performance.

```python
import asyncio
import aiohttp

async def fetch_comic_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def process_comics(comics):
    tasks = [process_comic(comic) for comic in comics]
    return await asyncio.gather(*tasks, return_exceptions=True)

async def process_comic(comic):
    # Async implementation
```

### 2. Caching

- **Current State**: Repeated network requests and processing.
- **Recommendation**: Implement caching for network requests and processed data.

```python
import functools
import time

def timed_cache(seconds=3600):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            if hasattr(wrapper, 'cache') and key in wrapper.cache:
                result, timestamp = wrapper.cache[key]
                if now - timestamp < seconds:
                    return result
            result = func(*args, **kwargs)
            if not hasattr(wrapper, 'cache'):
                wrapper.cache = {}
            wrapper.cache[key] = (result, now)
            return result
        return wrapper
    return decorator

@timed_cache(seconds=3600)  # Cache for 1 hour
def get_comic_info(url):
    # Implementation
```

## Security Improvements

### 1. Secrets Management

- **Current State**: Environment variables and local files for secrets.
- **Recommendation**: Enhance secrets management:
  - Use a dedicated secrets manager for local development
  - Implement proper encryption for stored credentials
  - Add validation for required secrets

```python
from cryptography.fernet import Fernet

def encrypt_credentials(credentials, key):
    f = Fernet(key)
    return f.encrypt(credentials.encode())

def decrypt_credentials(encrypted_credentials, key):
    f = Fernet(key)
    return f.decrypt(encrypted_credentials).decode()
```

### 2. Input Validation

- **Current State**: Limited input validation.
- **Recommendation**: Add comprehensive input validation for all user inputs and external data.

```python
def validate_url(url):
    """Validate that a URL is safe and properly formatted."""
    import re
    from urllib.parse import urlparse
    
    # Check if URL is properly formatted
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
```

## Documentation Improvements

### 1. Code Documentation

- **Current State**: Some documentation exists.
- **Recommendation**: Add comprehensive docstrings following Google or NumPy style.

```python
def stitch_images_multi_page(image_paths, width, height=0):
    """Stitch multiple images into pages.
    
    This function takes a list of image paths, loads them, and stitches them
    together into one or more pages based on the specified dimensions.
    
    Args:
        image_paths (List[str]): List of paths to images to stitch.
        width (int): Target width for the stitched image.
        height (int, optional): Target height for the stitched image.
            If 0, height will be calculated automatically. Defaults to 0.
    
    Returns:
        List[PIL.Image.Image]: List of stitched PIL Image objects.
        
    Raises:
        FileNotFoundError: If an image file cannot be found.
        PIL.UnidentifiedImageError: If an image cannot be opened or identified.
    """
```

### 2. API Documentation

- **Current State**: Limited API documentation.
- **Recommendation**: Generate API documentation using tools like Sphinx.

```python
# Add a docs/ directory with Sphinx configuration
# Example sphinx-quickstart command:
# sphinx-quickstart docs -p Chaptrix -a "Your Name" -v "0.1" --ext-autodoc --ext-viewcode
```

## Continuous Integration/Continuous Deployment

### 1. CI Pipeline

- **Current State**: GitHub Actions for automation.
- **Recommendation**: Enhance CI pipeline with:
  - Code linting (flake8, pylint)
  - Type checking (mypy)
  - Unit test execution
  - Code coverage reporting

```yaml
# .github/workflows/ci.yml
name: Chaptrix CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
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
          pip install flake8 pytest mypy pytest-cov
          pip install -r requirements.txt
      - name: Lint with flake8
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
      - name: Type check with mypy
        run: mypy --ignore-missing-imports .
      - name: Test with pytest
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v1
```

### 2. Versioning

- **Current State**: No explicit versioning.
- **Recommendation**: Implement semantic versioning and release management.

```python
# Add a version.py file
__version__ = '0.1.0'
```

## Conclusion

Implementing these recommendations will significantly improve the code quality, maintainability, and reliability of the Chaptrix project. Start with the highest priority items and gradually incorporate the rest as the project evolves.

Priority order for implementation:
1. Error handling improvements
2. Type hints
3. Unit testing
4. Modular design
5. Configuration validation
6. Code documentation
7. CI pipeline
8. Asynchronous processing
9. Dependency injection
10. Secrets management