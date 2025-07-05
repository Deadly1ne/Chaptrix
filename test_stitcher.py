import os
import sys
import logging
import numpy as np
from PIL import Image
import time

# Import the stitcher module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from stitcher import stitch_images_multi_page, save_stitched_images

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stitcher_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StitcherTest")

def create_test_images(num_images=5, width=600, height=800):
    """
    Create test images with different patterns for stitching tests
    
    Args:
        num_images: Number of test images to create
        width: Width of test images
        height: Height of test images
        
    Returns:
        List of PIL Image objects
    """
    images = []
    
    for i in range(num_images):
        # Create a white background
        img = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Add a colored rectangle
        color = [
            np.random.randint(0, 255),
            np.random.randint(0, 255),
            np.random.randint(0, 255)
        ]
        
        rect_x1 = width // 4
        rect_y1 = height // 4
        rect_x2 = width * 3 // 4
        rect_y2 = height * 3 // 4
        
        # Draw rectangle (BGR format for OpenCV)
        img[rect_y1:rect_y2, rect_x1:rect_x2] = color
        
        # Add text indicating image number
        font_size = 2
        font_thickness = 2
        text = f"Test Image {i+1}"
        text_x = width // 10
        text_y = height // 10
        
        # Draw black text
        for dy in range(-font_thickness, font_thickness+1):
            for dx in range(-font_thickness, font_thickness+1):
                if dx != 0 or dy != 0:  # Skip the center position
                    y = text_y + dy
                    x = text_x + dx
                    if 0 <= y < height and 0 <= x < width:
                        img[y-10:y+10, x-10:x+150] = [0, 0, 0]
        
        # Draw white text
        img[text_y-5:text_y+5, text_x-5:text_x+120] = [255, 255, 255]
        
        # Convert to PIL Image
        pil_img = Image.fromarray(img.astype('uint8'))
        images.append(pil_img)
    
    return images

def test_stitcher():
    """
    Test the stitcher functionality
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("Starting test_stitcher function")
    logger.info("Creating test directory")
    test_dir = "test_stitching"
    os.makedirs(test_dir, exist_ok=True)
    
    # Test 1: Basic stitching
    print("Starting Test 1: Basic stitching")
    logger.info("Test 1: Basic stitching")
    test_images = create_test_images(5)
    print(f"Created {len(test_images)} test images")
    stitched_images = stitch_images_multi_page(test_images)
    print(f"Stitched images result: {stitched_images is not None}, count: {len(stitched_images) if stitched_images else 0}")
    
    if not stitched_images:
        logger.error("Test 1 failed: stitch_images_multi_page returned empty list")
        return False
    
    # Save the stitched images
    output_path_template = os.path.join(test_dir, "basic_stitch.jpg")
    saved_files = save_stitched_images(stitched_images, output_path_template)
    if not saved_files:
        logger.error("Test 1 failed: Could not save stitched images")
        return False
    
    # Verify dimensions of first image
    stitched_img = stitched_images[0]
    expected_width = max(img.width for img in test_images)
    if stitched_img.width != expected_width:
        logger.error(f"Test 1 failed: Expected width {expected_width}, got {stitched_img.width}")
        return False
    
    # Test 2: Custom width
    logger.info("Test 2: Custom width")
    custom_width = 800
    stitched_images = stitch_images_multi_page(test_images, target_width=custom_width)
    
    if not stitched_images:
        logger.error("Test 2 failed: stitch_images_multi_page returned empty list")
        return False
    
    # Save the stitched images
    output_path_template = os.path.join(test_dir, "custom_width_stitch.jpg")
    saved_files = save_stitched_images(stitched_images, output_path_template)
    if not saved_files:
        logger.error("Test 2 failed: Could not save stitched images")
        return False
    
    # Verify dimensions
    stitched_img = stitched_images[0]
    if stitched_img.width != custom_width:
        logger.error(f"Test 2 failed: Expected width {custom_width}, got {stitched_img.width}")
        return False
    
    # Test 3: Custom max height (to force multiple images)
    logger.info("Test 3: Custom max height")
    custom_max_height = 1000
    stitched_images = stitch_images_multi_page(test_images, max_height=custom_max_height)
    
    if not stitched_images:
        logger.error("Test 3 failed: stitch_images_multi_page returned empty list")
        return False
    
    # Save the stitched images
    output_path_template = os.path.join(test_dir, "custom_height_stitch.jpg")
    saved_files = save_stitched_images(stitched_images, output_path_template)
    if not saved_files:
        logger.error("Test 3 failed: Could not save stitched images")
        return False
    
    # Verify we have multiple images due to height restriction
    if len(stitched_images) < 2:
        logger.error(f"Test 3 failed: Expected multiple images due to height restriction, got {len(stitched_images)}")
        return False
    
    # Test 4: Empty image list
    logger.info("Test 4: Empty image list")
    stitched_images = stitch_images_multi_page([])
    
    if stitched_images:
        logger.error("Test 4 failed: Expected empty list for empty image list")
        return False
    
    # Test 5: Performance test with many images
    logger.info("Test 5: Performance test")
    many_test_images = create_test_images(20, width=400, height=600)
    
    start_time = time.time()
    stitched_images = stitch_images_multi_page(many_test_images)
    elapsed_time = time.time() - start_time
    
    if not stitched_images:
        logger.error("Test 5 failed: stitch_images_multi_page returned empty list")
        return False
    
    # Save the stitched images
    output_path_template = os.path.join(test_dir, "performance_test_stitch.jpg")
    saved_files = save_stitched_images(stitched_images, output_path_template)
    if not saved_files:
        logger.error("Test 5 failed: Could not save stitched images")
        return False
    
    logger.info(f"Performance test completed in {elapsed_time:.2f} seconds")
    
    return True

def test_save_stitched_images():
    """
    Test the save_stitched_images function with the new naming convention
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    logger.info("Testing save_stitched_images with new naming convention")
    test_dir = "test_stitching_multi"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create test images
    test_images = create_test_images(3, width=400, height=600)
    
    # Test saving multiple images with new naming convention
    output_path_template = os.path.join(test_dir, "chapter_test.jpg")
    saved_files = save_stitched_images(test_images, output_path_template)
    
    if not saved_files or len(saved_files) != 3:
        logger.error(f"Expected 3 saved files, got {len(saved_files) if saved_files else 0}")
        return False
    
    # Check if the files follow the new naming convention (1.jpg, 2.jpg, 3.jpg)
    expected_filenames = [os.path.join(test_dir, f"{i+1}.jpg") for i in range(3)]
    for expected, actual in zip(expected_filenames, saved_files):
        if os.path.basename(expected) != os.path.basename(actual):
            logger.error(f"Expected filename {os.path.basename(expected)}, got {os.path.basename(actual)}")
            return False
    
    logger.info("All files saved with correct naming convention")
    for file in saved_files:
        logger.info(f"  - {file}")
    
    return True

# Define a compatibility function for old tests
def save_stitched_image(image, output_path, quality=90, format="JPEG"):
    """Compatibility function for old tests"""
    try:
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the image
        image.save(output_path, format, quality=quality)
        logger.info(f"Saved stitched image to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving stitched image: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting stitcher tests")
    
    try:
        basic_tests_passed = test_stitcher()
        print(f"Basic tests passed: {basic_tests_passed}")
    except Exception as e:
        logger.error(f"Error in test_stitcher: {str(e)}")
        print(f"Error in test_stitcher: {str(e)}")
        basic_tests_passed = False
    
    try:
        naming_tests_passed = test_save_stitched_images()
        print(f"Naming tests passed: {naming_tests_passed}")
    except Exception as e:
        logger.error(f"Error in test_save_stitched_images: {str(e)}")
        print(f"Error in test_save_stitched_images: {str(e)}")
        naming_tests_passed = False
    
    if basic_tests_passed and naming_tests_passed:
        logger.info("All stitcher tests passed successfully!")
        print("\nSUCCESS: Stitcher is working correctly!")
        sys.exit(0)
    else:
        logger.error("Stitcher tests failed!")
        print("\nERROR: Stitcher tests failed. Check the logs for details.")
        sys.exit(1)