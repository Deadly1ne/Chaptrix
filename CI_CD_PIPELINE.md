# CI/CD Pipeline Guide for Chaptrix

This guide outlines how to implement a comprehensive Continuous Integration and Continuous Deployment (CI/CD) pipeline for Chaptrix to enhance development workflow, ensure code quality, and streamline deployment.

## Benefits of CI/CD for Chaptrix

- **Automated Testing**: Catch bugs and issues early in the development process
- **Consistent Code Quality**: Enforce coding standards and best practices
- **Streamlined Deployment**: Automate the deployment process to various environments
- **Reduced Manual Errors**: Minimize human error in the build and deployment process
- **Faster Feedback**: Get immediate feedback on code changes

## CI/CD Pipeline Components

### 1. Continuous Integration (CI)

#### Linting and Code Quality

Implement automated code quality checks using tools like Flake8, Pylint, and Black.

```yaml
name: Code Quality

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.9'
          cache: 'pip'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 pylint black isort
          pip install -r requirements.txt
      - name: Lint with flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
      - name: Check formatting with black
        run: black --check .
      - name: Check imports with isort
        run: isort --check-only --profile black .
      - name: Analyze with pylint
        run: pylint --disable=all --enable=unused-import,unused-variable,unused-argument,redefined-outer-name .
```

#### Unit Testing

Implement automated unit tests using pytest.

```yaml
name: Unit Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.9'
          cache: 'pip'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov
          pip install -r requirements.txt
      - name: Test with pytest
        run: |
          pytest --cov=. --cov-report=xml
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

#### Security Scanning

Implement security scanning to identify vulnerabilities in dependencies.

```yaml
name: Security Scan

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install safety bandit
      - name: Check for security vulnerabilities
        run: safety check -r requirements.txt
      - name: Run bandit
        run: bandit -r . -x ./tests
```

### 2. Continuous Deployment (CD)

#### Automated Releases

Implement automated releases when pushing tags.

```yaml
name: Create Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install build
      - name: Build package
        run: python -m build
      - name: Create Release
        id: create_release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
      - name: Upload Release Asset
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ steps.create_release.outputs.upload_url }}
          asset_path: ./dist/chaptrix-${{ github.ref_name }}.tar.gz
          asset_name: chaptrix-${{ github.ref_name }}.tar.gz
          asset_content_type: application/gzip
```

#### Docker Image Building

Implement Docker image building for containerized deployment.

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      - name: Login to DockerHub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: yourusername/chaptrix
          tags: |
            type=ref,event=branch
            type=ref,event=tag
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=yourusername/chaptrix:buildcache
          cache-to: type=registry,ref=yourusername/chaptrix:buildcache,mode=max
```

## Setting Up the Development Environment

### 1. Branch Protection Rules

Set up branch protection rules for the main branch:

1. Go to your GitHub repository
2. Navigate to Settings > Branches
3. Add rule for the main branch
4. Enable the following options:
   - Require pull request reviews before merging
   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Include administrators

### 2. Pull Request Template

Create a pull request template to standardize contributions:

```markdown
<!-- .github/pull_request_template.md -->
## Description

Please include a summary of the change and which issue is fixed. Please also include relevant motivation and context.

Fixes # (issue)

## Type of change

Please delete options that are not relevant.

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?

Please describe the tests that you ran to verify your changes.

## Checklist:

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

### 3. Issue Templates

Create issue templates for bug reports and feature requests:

```markdown
<!-- .github/ISSUE_TEMPLATE/bug_report.md -->
---
name: Bug report
about: Create a report to help us improve
title: '[BUG]'
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment (please complete the following information):**
 - OS: [e.g. Windows, macOS, Linux]
 - Python Version: [e.g. 3.9.5]
 - Chaptrix Version: [e.g. 1.0.0]

**Additional context**
Add any other context about the problem here.
```

```markdown
<!-- .github/ISSUE_TEMPLATE/feature_request.md -->
---
name: Feature request
about: Suggest an idea for this project
title: '[FEATURE]'
labels: enhancement
assignees: ''

---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
```

## Implementing Unit Tests

To support the CI pipeline, implement unit tests for Chaptrix. Here's a basic structure:

### 1. Test Directory Structure

```
tests/
├── __init__.py
├── test_banner_cropper.py
├── test_config_validator.py
├── test_site_adapters.py
├── test_stitcher.py
└── test_unified_workflow.py
```

### 2. Sample Test File

```python
# tests/test_config_validator.py
import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_validator import validate_comics_json, validate_settings_json

class TestConfigValidator(unittest.TestCase):
    def setUp(self):
        # Sample valid comics.json content
        self.valid_comics = {
            "sites": {
                "example_site": {
                    "enabled": True,
                    "comics": {
                        "example_comic": {
                            "title": "Example Comic",
                            "url": "https://example.com/comic",
                            "last_chapter": "1",
                            "enabled": True
                        }
                    }
                }
            }
        }
        
        # Sample valid settings.json content
        self.valid_settings = {
            "download_path": "./downloads",
            "google_drive": {
                "enabled": False,
                "folder_id": ""
            },
            "discord": {
                "enabled": False,
                "webhook_url": "",
                "bot_token": "",
                "channel_id": ""
            },
            "template_processing": {
                "enabled": True
            },
            "banner_cropper": {
                "enabled": True
            }
        }
    
    def test_validate_comics_json_valid(self):
        # Test with valid comics.json
        with patch('builtins.open', MagicMock(return_value=MagicMock(
            __enter__=MagicMock(return_value=MagicMock(
                read=MagicMock(return_value=json.dumps(self.valid_comics))
            )),
            __exit__=MagicMock(return_value=None)
        ))):
            result = validate_comics_json()
            self.assertTrue(result)
    
    def test_validate_comics_json_invalid(self):
        # Test with invalid comics.json (missing required field)
        invalid_comics = self.valid_comics.copy()
        del invalid_comics["sites"]["example_site"]["comics"]["example_comic"]["url"]
        
        with patch('builtins.open', MagicMock(return_value=MagicMock(
            __enter__=MagicMock(return_value=MagicMock(
                read=MagicMock(return_value=json.dumps(invalid_comics))
            )),
            __exit__=MagicMock(return_value=None)
        ))):
            result = validate_comics_json()
            self.assertFalse(result)
    
    def test_validate_settings_json_valid(self):
        # Test with valid settings.json
        with patch('builtins.open', MagicMock(return_value=MagicMock(
            __enter__=MagicMock(return_value=MagicMock(
                read=MagicMock(return_value=json.dumps(self.valid_settings))
            )),
            __exit__=MagicMock(return_value=None)
        ))):
            result = validate_settings_json()
            self.assertTrue(result)
    
    def test_validate_settings_json_invalid(self):
        # Test with invalid settings.json (missing required field)
        invalid_settings = self.valid_settings.copy()
        del invalid_settings["download_path"]
        
        with patch('builtins.open', MagicMock(return_value=MagicMock(
            __enter__=MagicMock(return_value=MagicMock(
                read=MagicMock(return_value=json.dumps(invalid_settings))
            )),
            __exit__=MagicMock(return_value=None)
        ))):
            result = validate_settings_json()
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
```

## Docker Support

To support containerized deployment, add Docker support to Chaptrix:

### 1. Dockerfile

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p /app/downloads

# Run the application
CMD ["python", "unified_workflow.py"]
```

### 2. Docker Compose File

```yaml
version: '3.8'

services:
  chaptrix:
    build: .
    volumes:
      - ./comics.json:/app/comics.json
      - ./settings.json:/app/settings.json
      - ./downloads:/app/downloads
      - ./credentials.json:/app/credentials.json:ro
      - ./.env:/app/.env:ro
    environment:
      - TZ=UTC
    restart: unless-stopped
```

## Versioning Strategy

Implement semantic versioning for Chaptrix:

1. Create a `version.py` file:

```python
# version.py
__version__ = '1.0.0'
```

2. Update the version in your setup.py or pyproject.toml file.

3. Create a version bump script:

```python
# scripts/bump_version.py
import re
import sys

def bump_version(version_type):
    with open('version.py', 'r') as f:
        content = f.read()
    
    version_match = re.search(r"__version__ = ['\"]([^'\"]*)['\"]