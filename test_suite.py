#!/usr/bin/env python3
"""
Chaptrix Test Suite
Consolidated testing for all Chaptrix components
"""

import os
import sys
import json
import logging
from PIL import Image, ImageDraw, ImageFont
import requests
from utils import handle_error, setup_logging

# Setup logging for tests
setup_logging(logging.INFO, "chaptrix_tests.log")
logger = logging.getLogger("ChaptrixTests")

class ChaptrixTestSuite:
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        
    def log_test_result(self, test_name, success, message=""):
        """Log test result"""
        status = "PASS" if success else "FAIL"
        result = f"[{status}] {test_name}: {message}"
        self.test_results.append(result)
        
        if success:
            logger.info(result)
        else:
            logger.error(result)
            self.failed_tests.append(test_name)
            
        print(result)
    
    def test_python_version(self):
        """Test Python version compatibility"""
        try:
            version = sys.version_info
            if version.major >= 3 and version.minor >= 7:
                self.log_test_result("Python Version", True, f"Python {version.major}.{version.minor}.{version.micro}")
                return True
            else:
                self.log_test_result("Python Version", False, f"Python {version.major}.{version.minor} < 3.7")
                return False
        except Exception as e:
            self.log_test_result("Python Version", False, str(e))
            return False
    
    def test_required_packages(self):
        """Test if required packages are installed"""
        required_packages = [
            'requests', 'beautifulsoup4', 'Pillow', 'opencv-python',
            'google-api-python-client', 'google-auth', 'discord.py',
            'streamlit', 'numpy'
        ]
        
        all_passed = True
        for package in required_packages:
            try:
                __import__(package.replace('-', '_').replace('beautifulsoup4', 'bs4'))
                self.log_test_result(f"Package: {package}", True, "Installed")
            except ImportError:
                self.log_test_result(f"Package: {package}", False, "Not installed")
                all_passed = False
        
        return all_passed
    
    def test_configuration_files(self):
        """Test configuration files"""
        config_files = {
            'settings.json': 'Settings configuration',
            'comics.json': 'Comics configuration',
            'requirements.txt': 'Python requirements'
        }
        
        all_passed = True
        for file_path, description in config_files.items():
            if os.path.exists(file_path):
                try:
                    if file_path.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                    self.log_test_result(f"Config: {file_path}", True, f"{description} - Valid")
                except json.JSONDecodeError:
                    self.log_test_result(f"Config: {file_path}", False, f"{description} - Invalid JSON")
                    all_passed = False
                except Exception as e:
                    self.log_test_result(f"Config: {file_path}", False, f"{description} - {str(e)}")
                    all_passed = False
            else:
                self.log_test_result(f"Config: {file_path}", False, f"{description} - File not found")
                all_passed = False
        
        return all_passed
    
    def test_directory_structure(self):
        """Test required directories"""
        required_dirs = ['downloads', 'processed', 'assets']
        
        all_passed = True
        for dir_path in required_dirs:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                self.log_test_result(f"Directory: {dir_path}", True, "Exists")
            else:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    self.log_test_result(f"Directory: {dir_path}", True, "Created")
                except Exception as e:
                    self.log_test_result(f"Directory: {dir_path}", False, str(e))
                    all_passed = False
        
        return all_passed
    
    def test_image_processing(self):
        """Test image processing capabilities"""
        try:
            # Create a test image
            test_image = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(test_image)
            draw.rectangle([100, 100, 700, 500], fill='blue')
            draw.text((200, 250), "Test Image", fill='white')
            
            # Test saving
            test_path = "test_image_processing.jpg"
            test_image.save(test_path, quality=90)
            
            # Test loading
            loaded_image = Image.open(test_path)
            
            # Cleanup
            os.remove(test_path)
            
            self.log_test_result("Image Processing", True, "PIL operations successful")
            return True
            
        except Exception as e:
            self.log_test_result("Image Processing", False, str(e))
            return False
    
    def test_network_connectivity(self):
        """Test network connectivity"""
        test_urls = [
            'https://www.google.com',
            'https://www.baozimh.com',
            'https://www.twmanga.com'
        ]
        
        all_passed = True
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.log_test_result(f"Network: {url}", True, f"Status {response.status_code}")
                else:
                    self.log_test_result(f"Network: {url}", False, f"Status {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_test_result(f"Network: {url}", False, str(e))
                all_passed = False
        
        return all_passed
    
    def test_stitcher_functionality(self):
        """Test stitcher module"""
        try:
            from stitcher import stitch_images_multi_page, save_stitched_images
            
            # Create test images
            test_images = []
            for i in range(3):
                img = Image.new('RGB', (800, 400), color=f'hsl({i*120}, 100%, 50%)')
                draw = ImageDraw.Draw(img)
                draw.text((300, 180), f"Page {i+1}", fill='white')
                test_images.append(img)
            
            # Test stitching
            stitched = stitch_images_multi_page(test_images, 800, 1200, 90)
            
            if stitched:
                self.log_test_result("Stitcher", True, f"Created {len(stitched)} stitched image(s)")
                return True
            else:
                self.log_test_result("Stitcher", False, "No stitched images created")
                return False
                
        except Exception as e:
            self.log_test_result("Stitcher", False, str(e))
            return False
    
    def test_banner_cropper(self):
        """Test banner cropper functionality"""
        try:
            from banner_cropper import crop_banners_in_folder
            
            # Check if banner template exists
            banner_path = "assets/banner.png"
            if os.path.exists(banner_path):
                self.log_test_result("Banner Cropper", True, "Banner template found")
                return True
            else:
                self.log_test_result("Banner Cropper", False, "Banner template not found")
                return False
                
        except Exception as e:
            self.log_test_result("Banner Cropper", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*50)
        print("         CHAPTRIX TEST SUITE")
        print("="*50)
        
        tests = [
            self.test_python_version,
            self.test_required_packages,
            self.test_configuration_files,
            self.test_directory_structure,
            self.test_image_processing,
            self.test_network_connectivity,
            self.test_stitcher_functionality,
            self.test_banner_cropper
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                handle_error(e, f"running test {test.__name__}")
        
        print("\n" + "="*50)
        print("         TEST RESULTS SUMMARY")
        print("="*50)
        
        total_tests = len(self.test_results)
        failed_count = len(self.failed_tests)
        passed_count = total_tests - failed_count
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        
        if failed_count > 0:
            print("\nFailed Tests:")
            for test in self.failed_tests:
                print(f"  - {test}")
            print("\nPlease fix the failed tests before using Chaptrix.")
            return False
        else:
            print("\n🎉 All tests passed! Chaptrix is ready to use.")
            return True

def main():
    """Main function"""
    test_suite = ChaptrixTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\nYour Chaptrix installation is ready for automation!")
        sys.exit(0)
    else:
        print("\nPlease resolve the issues above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()