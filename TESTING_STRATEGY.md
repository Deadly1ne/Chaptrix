# Testing Strategy

## Overview

This document outlines a comprehensive testing strategy for the Chaptrix application. Implementing a robust testing approach will help identify issues early, ensure code quality, and make the application more maintainable.

## Current Testing State

The application currently has some basic test files:

- `test_automation.py`
- `test_banner_cropper.py`
- `test_installation.py`
- `test_stitcher.py`

However, these tests appear to be limited in scope and don't provide comprehensive coverage of the codebase.

## Recommended Testing Approach

### 1. Test Pyramid Structure

Implement a test pyramid with three levels:

1. **Unit Tests**: Fast, focused tests for individual functions and classes
2. **Integration Tests**: Tests that verify interactions between components
3. **End-to-End Tests**: Tests that verify complete workflows

### 2. Unit Testing

#### Core Functionality Tests

```python
# test_config.py
import unittest
import tempfile
import json
import os
from unittest.mock import patch

# Import the functions to test
from main import load_settings, save_settings, DEFAULT_SETTINGS

class TestConfigFunctions(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.settings_path = os.path.join(self.test_dir.name, "settings.json")
        
        # Patch the SETTINGS_FILE constant
        self.patcher = patch("main.SETTINGS_FILE", self.settings_path)
        self.patcher.start()
    
    def tearDown(self):
        # Clean up the temporary directory
        self.patcher.stop()
        self.test_dir.cleanup()
    
    def test_load_settings_file_not_found(self):
        """Test loading settings when file doesn't exist"""
        # File doesn't exist yet
        settings = load_settings()
        
        # Should return default settings
        self.assertEqual(settings, DEFAULT_SETTINGS)
        
        # Should create the file with default settings
        self.assertTrue(os.path.exists(self.settings_path))
    
    def test_load_settings_invalid_json(self):
        """Test loading settings with invalid JSON"""
        # Create an invalid JSON file
        with open(self.settings_path, "w") as f:
            f.write("invalid json")
        
        # Should return default settings
        settings = load_settings()
        self.assertEqual(settings, DEFAULT_SETTINGS)
    
    def test_save_and_load_settings(self):
        """Test saving and loading settings"""
        test_settings = {
            "check_interval": 3600,
            "image_width": 1000,
            "custom_setting": "test"
        }
        
        # Save the settings
        save_settings(test_settings)
        
        # Load the settings
        loaded_settings = load_settings()
        
        # Should merge with default settings
        expected = DEFAULT_SETTINGS.copy()
        expected.update(test_settings)
        
        self.assertEqual(loaded_settings, expected)
```

#### Image Processing Tests

```python
# test_stitcher.py
import unittest
import tempfile
import os
from PIL import Image
import numpy as np

from stitcher import stitch_images_multi_page

class TestStitcher(unittest.TestCase):
    def setUp(self):
        # Create test images
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_images = []
        
        # Create 3 test images with different content
        for i in range(3):
            img = Image.new('RGB', (100, 200), color=(i*50, i*50, i*50))
            self.test_images.append(img)
    
    def tearDown(self):
        self.test_dir.cleanup()
    
    def test_stitch_images_basic(self):
        """Test basic image stitching"""
        result = stitch_images_multi_page(self.test_images, target_width=100)
        
        # Should return a list with one image
        self.assertEqual(len(result), 1)
        
        # The height should be the sum of the heights of the input images
        expected_height = sum(img.height for img in self.test_images)
        self.assertEqual(result[0].height, expected_height)
        self.assertEqual(result[0].width, 100)
    
    def test_stitch_images_with_max_height(self):
        """Test image stitching with max height constraint"""
        # Set max height to less than the sum of image heights
        max_height = 300  # Less than 3*200=600
        
        result = stitch_images_multi_page(self.test_images, target_width=100, max_height=max_height)
        
        # Should return multiple images
        self.assertGreater(len(result), 1)
        
        # Each image should not exceed max height
        for img in result:
            self.assertLessEqual(img.height, max_height)
            self.assertEqual(img.width, 100)
```

#### Web Scraping Tests

```python
# test_adapters.py
import unittest
from unittest.mock import patch, MagicMock

from main import BaseSiteAdapter, BaozimhAdapter

class TestBaozimhAdapter(unittest.TestCase):
    @patch('requests.get')
    def test_get_latest_chapter(self, mock_get):
        """Test getting the latest chapter"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <body>
                <div class="comics-chapters">
                    <a href="/comic/123/chapter/456" title="Chapter 10">Chapter 10</a>
                </div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # Create the adapter
        comic = {"name": "Test Comic", "url": "https://www.baozimh.com/comic/123", "site": "baozimh"}
        adapter = BaozimhAdapter(comic)
        
        # Get the latest chapter
        chapter, url = adapter.get_latest_chapter()
        
        # Verify the results
        self.assertEqual(chapter, "Chapter 10")
        self.assertEqual(url, "https://www.baozimh.com/comic/123/chapter/456")
        
        # Verify the request was made correctly
        mock_get.assert_called_once_with("https://www.baozimh.com/comic/123")
```

### 3. Integration Testing

#### External Service Integration Tests

```python
# test_integrations.py
import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile

from main import upload_to_drive, send_discord_notification

class TestGoogleDriveIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary test file
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(b"Test content")
        self.test_file.close()
    
    def tearDown(self):
        # Remove the test file
        os.unlink(self.test_file.name)
    
    @patch('main.get_drive_service')
    def test_upload_to_drive_success(self, mock_get_drive_service):
        """Test successful upload to Google Drive"""
        # Mock the drive service
        mock_service = MagicMock()
        mock_files = MagicMock()
        mock_service.files.return_value = mock_files
        
        # Mock the create method
        mock_create = MagicMock()
        mock_files.create.return_value = mock_create
        
        # Mock the execute method
        mock_create.execute.return_value = {"id": "test_file_id"}
        
        # Set up the mock service
        mock_get_drive_service.return_value = mock_service
        
        # Call the function
        result = upload_to_drive(self.test_file.name, "Test Folder")
        
        # Verify the result
        self.assertEqual(result, "https://drive.google.com/file/d/test_file_id/view")
    
    @patch('main.get_drive_service')
    def test_upload_to_drive_service_unavailable(self, mock_get_drive_service):
        """Test upload when drive service is unavailable"""
        # Mock the drive service as None (unavailable)
        mock_get_drive_service.return_value = None
        
        # Call the function
        result = upload_to_drive(self.test_file.name, "Test Folder")
        
        # Verify the result is None
        self.assertIsNone(result)

class TestDiscordIntegration(unittest.TestCase):
    @patch('requests.post')
    @patch('main.load_settings')
    def test_send_discord_notification(self, mock_load_settings, mock_post):
        """Test sending a Discord notification"""
        # Mock the settings
        mock_load_settings.return_value = {"discord_webhook_url": "https://discord.com/api/webhooks/test"}
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # Call the function
        result = send_discord_notification("Test message")
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the request was made correctly
        mock_post.assert_called_once_with(
            "https://discord.com/api/webhooks/test",
            json={"content": "Test message", "embeds": []}
        )
```

### 4. End-to-End Testing

```python
# test_workflow.py
import unittest
import os
import tempfile
import shutil
from unittest.mock import patch

from unified_workflow import unified_process_comic

class TestUnifiedWorkflow(unittest.TestCase):
    def setUp(self):
        # Create temporary directories
        self.test_dir = tempfile.TemporaryDirectory()
        self.downloads_dir = os.path.join(self.test_dir.name, "downloads")
        self.processed_dir = os.path.join(self.test_dir.name, "processed")
        os.makedirs(self.downloads_dir)
        os.makedirs(self.processed_dir)
        
        # Create a test comic
        self.test_comic = {
            "name": "Test Comic",
            "url": "https://example.com/comic/123",
            "site": "baozimh",
            "last_known_chapter": "Chapter 1"
        }
        
        self.tracked_comics = [self.test_comic]
    
    def tearDown(self):
        self.test_dir.cleanup()
    
    @patch('main.load_settings')
    @patch('main.get_site_adapter')
    def test_unified_process_comic_no_new_chapter(self, mock_get_site_adapter, mock_load_settings):
        """Test processing a comic with no new chapter"""
        # Mock the settings
        mock_load_settings.return_value = {
            "download_path": self.downloads_dir,
            "processed_path": self.processed_dir,
            "upload_to_drive": False,
            "upload_to_discord": False
        }
        
        # Mock the site adapter
        mock_adapter = unittest.mock.MagicMock()
        mock_adapter.get_latest_chapter.return_value = ("Chapter 1", "https://example.com/comic/123/chapter/1")
        mock_get_site_adapter.return_value = mock_adapter
        
        # Call the function
        result = unified_process_comic(self.test_comic, self.tracked_comics, 0)
        
        # Verify the result
        self.assertFalse(result)
        
        # Verify the comic was not updated
        self.assertEqual(self.test_comic["last_known_chapter"], "Chapter 1")
```

### 5. Mocking External Services

Create mock classes for external services to use in tests:

```python
# conftest.py
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_drive_service():
    """Mock Google Drive service"""
    service = MagicMock()
    files = MagicMock()
    service.files.return_value = files
    
    # Mock the create method
    create = MagicMock()
    files.create.return_value = create
    
    # Mock the execute method
    create.execute.return_value = {"id": "test_file_id"}
    
    return service

@pytest.fixture
def mock_requests_session():
    """Mock requests session"""
    session = MagicMock()
    response = MagicMock()
    session.get.return_value = response
    session.post.return_value = response
    
    # Default response attributes
    response.status_code = 200
    response.text = "<html><body>Mock HTML</body></html>"
    response.content = b"Mock content"
    
    return session
```

### 6. Test Data Management

Create fixtures for common test data:

```python
# conftest.py
import pytest
import os
import tempfile
from PIL import Image
import numpy as np

@pytest.fixture
def test_images():
    """Create test images"""
    images = []
    
    # Create 3 test images with different content
    for i in range(3):
        img = Image.new('RGB', (100, 200), color=(i*50, i*50, i*50))
        images.append(img)
    
    return images

@pytest.fixture
def test_comic_data():
    """Create test comic data"""
    return {
        "name": "Test Comic",
        "url": "https://example.com/comic/123",
        "site": "baozimh",
        "last_known_chapter": "Chapter 1"
    }

@pytest.fixture
def test_settings():
    """Create test settings"""
    return {
        "check_interval": 3600,
        "image_width": 800,
        "image_height": 0,
        "upload_to_drive": False,
        "upload_to_discord": False,
        "download_path": "test_downloads",
        "processed_path": "test_processed",
        "discord_webhook_url": "",
        "discord_bot_token": "",
        "discord_channel_id": ""
    }
```

## Test Automation

### 1. GitHub Actions Integration

Create a GitHub Actions workflow for running tests:

```yaml
# .github/workflows/run-tests.yml
name: Run Tests

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
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        pip install pytest pytest-cov
    - name: Test with pytest
      run: |
        pytest --cov=. --cov-report=xml
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
```

### 2. Pre-commit Hooks

Set up pre-commit hooks to run tests before commits:

```yaml
# .pre-commit-config.yaml
repos:
-   repo: local
    hooks:
    -   id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Test Coverage Goals

### 1. Coverage Targets

- **Unit Tests**: Aim for 80%+ coverage of core functionality
- **Integration Tests**: Cover all external service integrations
- **End-to-End Tests**: Cover main user workflows

### 2. Coverage Reporting

Use pytest-cov to generate coverage reports:

```bash
pytest --cov=. --cov-report=html
```

## Implementation Plan

### Phase 1: Basic Unit Tests

1. Set up the testing framework (pytest)
2. Write unit tests for core utility functions
3. Write unit tests for image processing functions

### Phase 2: Integration Tests

1. Create mock classes for external services
2. Write integration tests for Google Drive integration
3. Write integration tests for Discord integration

### Phase 3: End-to-End Tests

1. Write end-to-end tests for the unified workflow
2. Set up GitHub Actions for continuous testing

## Conclusion

Implementing a comprehensive testing strategy will significantly improve the reliability and maintainability of the Chaptrix application. By focusing on a mix of unit, integration, and end-to-end tests, you can catch issues early and ensure that the application continues to work correctly as it evolves.