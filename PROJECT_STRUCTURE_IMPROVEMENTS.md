# Project Structure Improvements

## Overview

This document provides recommendations for improving the project structure and organization of the Chaptrix application. A well-organized project structure enhances maintainability, readability, and scalability.

## Current Structure

The current project structure is relatively flat, with most functionality in a few large files:

- `main.py`: Contains core functionality, site adapters, and integrations
- `unified_workflow.py`: Contains the unified processing workflow
- `stitcher.py`: Contains image stitching functionality
- `banner_cropper.py`: Contains banner cropping functionality

This structure works for a small project but can become difficult to maintain as the project grows.

## Recommended Structure

### Package-Based Organization

Refactor the codebase into a proper Python package structure:

```
chaptrix/
  ├── __init__.py                # Package initialization
  ├── __main__.py                # Entry point for running as module
  ├── config.py                  # Configuration management
  ├── adapters/                  # Site-specific adapters
  │   ├── __init__.py
  │   ├── base.py                # Base adapter class
  │   ├── baozimh.py             # Baozimh adapter
  │   └── twmanga.py             # Twmanga adapter
  ├── processing/                # Image processing
  │   ├── __init__.py
  │   ├── stitcher.py            # Image stitching
  │   └── cropper.py             # Banner cropping
  ├── integrations/              # External services
  │   ├── __init__.py
  │   ├── drive.py               # Google Drive integration
  │   └── discord.py             # Discord integration
  ├── utils/                     # Utility functions
  │   ├── __init__.py
  │   ├── error.py               # Error handling
  │   └── logging.py             # Logging configuration
  └── cli/                       # Command-line interfaces
      ├── __init__.py
      ├── main_cli.py            # Main CLI
      └── workflow_cli.py        # Unified workflow CLI
```

### Scripts Directory

Move batch files and shell scripts to a dedicated directory:

```
scripts/
  ├── run_check.bat              # Windows script for checking comics
  ├── run_check.sh               # Linux/Mac script for checking comics
  ├── run_unified_workflow.bat   # Windows script for unified workflow
  ├── run_unified_workflow.sh    # Linux/Mac script for unified workflow
  └── setup_github_token.bat     # GitHub token setup script
```

### Tests Directory

Organize tests to mirror the package structure:

```
tests/
  ├── __init__.py
  ├── conftest.py                # Pytest configuration and fixtures
  ├── test_adapters/             # Tests for adapters
  │   ├── __init__.py
  │   ├── test_base.py
  │   ├── test_baozimh.py
  │   └── test_twmanga.py
  ├── test_processing/           # Tests for image processing
  │   ├── __init__.py
  │   ├── test_stitcher.py
  │   └── test_cropper.py
  └── test_integrations/         # Tests for external integrations
      ├── __init__.py
      ├── test_drive.py
      └── test_discord.py
```

### Documentation Directory

Organize documentation files:

```
docs/
  ├── README.md                  # Main README
  ├── INSTALLATION.md            # Installation guide
  ├── USAGE.md                   # Usage guide
  ├── CONFIGURATION.md           # Configuration guide
  ├── TROUBLESHOOTING.md         # Troubleshooting guide
  └── guides/                    # Detailed guides
      ├── GOOGLE_DRIVE_SETUP.md  # Google Drive setup guide
      ├── DISCORD_SETUP.md       # Discord setup guide
      └── SITE_ADAPTER_GUIDE.md  # Guide for creating site adapters
```

## Implementation Steps

### 1. Create Package Structure

```bash
# Create directory structure
mkdir -p chaptrix/{adapters,processing,integrations,utils,cli}
mkdir -p tests/{test_adapters,test_processing,test_integrations}
mkdir -p docs/guides
mkdir -p scripts

# Create __init__.py files
touch chaptrix/__init__.py
touch chaptrix/{adapters,processing,integrations,utils,cli}/__init__.py
touch tests/__init__.py
touch tests/{test_adapters,test_processing,test_integrations}/__init__.py
```

### 2. Refactor Core Functionality

1. **Extract Site Adapters**:
   - Move the `BaseSiteAdapter` class to `chaptrix/adapters/base.py`
   - Move site-specific adapters to their respective files

2. **Extract Image Processing**:
   - Move stitcher functionality to `chaptrix/processing/stitcher.py`
   - Move banner cropper functionality to `chaptrix/processing/cropper.py`

3. **Extract Integrations**:
   - Move Google Drive functionality to `chaptrix/integrations/drive.py`
   - Move Discord functionality to `chaptrix/integrations/discord.py`

4. **Create Configuration Module**:
   - Create `chaptrix/config.py` for configuration management
   - Implement a `Config` class for loading/saving settings and comics

### 3. Create Entry Points

1. **Package Entry Point**:

```python
# chaptrix/__main__.py
import sys
from chaptrix.cli.main_cli import main

if __name__ == "__main__":
    sys.exit(main())
```

2. **CLI Modules**:

```python
# chaptrix/cli/main_cli.py
import argparse
from chaptrix.config import Config

def main():
    parser = argparse.ArgumentParser(description="Chaptrix Manga Automation")
    # Add arguments...
    args = parser.parse_args()
    
    # Process arguments...
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
```

### 4. Update Scripts

Update batch files and shell scripts to use the new package structure:

```batch
@echo off
python -m chaptrix --check-comics
```

### 5. Update Documentation

Move and update documentation files to reflect the new structure.

## Benefits of the New Structure

### Improved Maintainability

- **Separation of Concerns**: Each module has a clear responsibility
- **Reduced File Size**: Smaller files are easier to understand and maintain
- **Clear Dependencies**: Dependencies between modules are explicit

### Better Testability

- **Isolated Components**: Each component can be tested in isolation
- **Mock Dependencies**: Dependencies can be easily mocked for testing
- **Test Organization**: Tests are organized to mirror the package structure

### Enhanced Scalability

- **Easy to Add Features**: New features can be added as new modules
- **Easy to Add Site Adapters**: New site adapters can be added without modifying existing code
- **Pluggable Architecture**: Components can be swapped or extended

## Backward Compatibility

To maintain backward compatibility during the transition:

1. Create wrapper modules that import from the new structure
2. Gradually update import statements in existing code
3. Add deprecation warnings to old entry points

## Conclusion

Refactoring the Chaptrix application into a well-organized package structure will significantly improve maintainability, testability, and scalability. While it requires an initial investment of time, the benefits will become increasingly apparent as the project continues to grow and evolve.