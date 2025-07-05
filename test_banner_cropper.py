import os
import sys
import logging
from banner_cropper import crop_banner_if_found, crop_folder, run_cropper
from PIL import Image
import cv2
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cropper_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CropperTest")

def create_test_image_with_banner(output_path, banner_path, position='top'):
    """Create a test image with a banner at the specified position"""
    # Load the banner
    banner = cv2.imread(banner_path)
    if banner is None:
        logger.error(f"Could not load banner from {banner_path}")
        return False
    
    banner_height, banner_width = banner.shape[:2]
    
    # Create a blank image (white background) - ensure it's larger than the banner
    test_image_height = max(1000, banner_height * 3)  # Make sure image is at least 3x banner height
    test_image_width = max(banner_width, 800)  # Make sure image is at least as wide as banner
    test_image = np.ones((test_image_height, test_image_width, 3), dtype=np.uint8) * 255
    
    # Add some random content to simulate manga page
    for i in range(10):
        y = np.random.randint(banner_height + 10, test_image_height - banner_height - 10)
        cv2.rectangle(test_image, 
                     (np.random.randint(0, test_image_width//2), y), 
                     (np.random.randint(test_image_width//2, test_image_width), y + np.random.randint(20, 50)), 
                     (0, 0, 0), 
                     -1)
    
    # Add the banner at the specified position
    if position == 'top':
        # Make sure we don't exceed image dimensions
        h = min(banner_height, test_image_height)
        w = min(banner_width, test_image_width)
        test_image[:h, :w] = banner[:h, :w]
    else:  # bottom
        h = min(banner_height, test_image_height)
        w = min(banner_width, test_image_width)
        test_image[-h:, :w] = banner[:h, :w]
    
    # Save the test image
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, test_image)
    logger.info(f"Created test image with {position} banner at {output_path}")
    return True

def test_banner_cropping():
    """Test the banner cropping functionality"""
    banner_path = "assets/banner.png"
    
    if not os.path.exists(banner_path):
        logger.error(f"Banner template not found at {banner_path}")
        return False
    
    # Create test directory
    test_dir = "test_cropping"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create test images
    top_banner_image = os.path.join(test_dir, "top_banner.jpg")
    bottom_banner_image = os.path.join(test_dir, "bottom_banner.jpg")
    no_banner_image = os.path.join(test_dir, "no_banner.jpg")
    
    create_test_image_with_banner(top_banner_image, banner_path, 'top')
    create_test_image_with_banner(bottom_banner_image, banner_path, 'bottom')
    
    # Create an image without a banner - make sure it's large enough
    banner = cv2.imread(banner_path)
    if banner is None:
        logger.error(f"Could not load banner from {banner_path}")
        return False
        
    banner_height, banner_width = banner.shape[:2]
    img_height = max(800, banner_height * 3)
    img_width = max(600, banner_width * 2)
    
    img = np.ones((img_height, img_width, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, 
                 (img_width//4, img_height//4), 
                 (img_width*3//4, img_height*3//4), 
                 (0, 0, 0), 
                 -1)
    cv2.imwrite(no_banner_image, img)
    
    # Test cropping on the images
    logger.info("Testing banner cropping...")
    
    # Get original dimensions
    top_img = cv2.imread(top_banner_image)
    bottom_img = cv2.imread(bottom_banner_image)
    no_banner_img = cv2.imread(no_banner_image)
    
    top_original_height = top_img.shape[0]
    bottom_original_height = bottom_img.shape[0]
    no_banner_original_height = no_banner_img.shape[0]
    
    # Apply cropping
    crop_banner_if_found(top_banner_image, cv2.imread(banner_path))
    crop_banner_if_found(bottom_banner_image, cv2.imread(banner_path))
    crop_banner_if_found(no_banner_image, cv2.imread(banner_path))
    
    # Check results
    top_img_after = cv2.imread(top_banner_image)
    bottom_img_after = cv2.imread(bottom_banner_image)
    no_banner_img_after = cv2.imread(no_banner_image)
    
    top_cropped = top_img_after.shape[0] < top_original_height
    bottom_cropped = bottom_img_after.shape[0] < bottom_original_height
    no_banner_unchanged = no_banner_img_after.shape[0] == no_banner_original_height
    
    logger.info(f"Top banner image cropped: {top_cropped}")
    logger.info(f"Bottom banner image cropped: {bottom_cropped}")
    logger.info(f"No banner image unchanged: {no_banner_unchanged}")
    
    return top_cropped and bottom_cropped and no_banner_unchanged

if __name__ == "__main__":
    logger.info("Starting banner cropper test")
    
    if test_banner_cropping():
        logger.info("Banner cropper test passed successfully!")
        print("\nSUCCESS: Banner cropper is working correctly!")
    else:
        logger.error("Banner cropper test failed!")
        print("\nERROR: Banner cropper test failed. Check the logs for details.")