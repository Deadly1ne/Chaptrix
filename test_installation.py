#!/usr/bin/env python3
"""
Chaptrix Installation Test Script
This script checks if all required dependencies are installed correctly.
"""

import sys
import importlib.util
import os

required_packages = [
    "requests",
    "bs4",  # BeautifulSoup4
    "PIL",  # Pillow
    "numpy",
    "google",
    "streamlit",
    "discord",
    "dotenv"
]

def check_package(package_name):
    """Check if a package is installed"""
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return False
    return True

def main():
    """Main function to test installation"""
    print("\n===== Chaptrix Installation Test =====\n")
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
    else:
        print("✅ Python version is compatible")
    
    # Check required packages
    print("\nChecking required packages:")
    all_packages_installed = True
    for package in required_packages:
        if check_package(package):
            print(f"✅ {package} is installed")
        else:
            print(f"❌ {package} is NOT installed")
            all_packages_installed = False
    
    # Check required files
    print("\nChecking required files:")
    required_files = ["main.py", "requirements.txt", "comics.json", "settings.json"]
    all_files_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} does NOT exist")
            all_files_exist = False
    
    # Check directories
    print("\nChecking directories:")
    required_dirs = ["downloads", "processed", "templates"]
    all_dirs_exist = True
    for directory in required_dirs:
        if os.path.isdir(directory):
            print(f"✅ {directory} directory exists")
        else:
            print(f"❌ {directory} directory does NOT exist")
            all_dirs_exist = False
    
    # Final verdict
    print("\n===== Test Results =====\n")
    if all_packages_installed and all_files_exist and all_dirs_exist:
        print("✅ All checks passed! Chaptrix should work correctly.")
        print("\nTo run Chaptrix:")
        print("  - Dashboard mode: streamlit run main.py")
        print("  - Check mode: python main.py --check")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nTo install required packages:")
        print("  pip install -r requirements.txt")

if __name__ == "__main__":
    main()