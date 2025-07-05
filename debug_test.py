import os
import sys
import logging
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
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DebugTest")

# Create a simple test image
def create_test_image(width=600, height=800):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(width//4, height//4), (width*3//4, height*3//4)], fill=(200, 200, 200))
    draw.text((width//10, height//10), "Test Image", fill=(0, 0, 0))
    return img

# Test the stitcher
def test_stitcher():
    print("Creating test images...")
    test_images = [create_test_image() for _ in range(5)]
    
    print("Stitching images...")
    stitched_images = stitch_images_multi_page(test_images)
    
    if not stitched_images:
        print("ERROR: stitch_images_multi_page returned empty list")
        return False
    
    print(f"Successfully created {len(stitched_images)} stitched images")
    
    # Save the stitched images
    test_dir = "debug_test"
    os.makedirs(test_dir, exist_ok=True)
    output_path_template = os.path.join(test_dir, "test.jpg")
    
    print(f"Saving stitched images with template: {output_path_template}")
    saved_files = save_stitched_images(stitched_images, output_path_template)
    
    if not saved_files:
        print("ERROR: Could not save stitched images")
        return False
    
    print(f"Successfully saved {len(saved_files)} files:")
    for file in saved_files:
        print(f"  - {file}")
    
    return True

if __name__ == "__main__":
    print("Starting debug test...")
    result = test_stitcher()
    print(f"Test result: {'SUCCESS' if result else 'FAILURE'}")