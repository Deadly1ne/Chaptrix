import os
import logging
from PIL import Image
import numpy as np
import time
from utils import handle_error

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stitcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MultiPageStitcher")


def stitch_images_multi_page(images, target_width=800, max_height=12000, quality=100, format="JPEG"):
    """
    Stitch multiple images vertically into multiple output images if height exceeds max_height
    
    Args:
        images: List of PIL Image objects to stitch
        target_width: Target width for the stitched image (default: 800)
        max_height: Maximum height for a single stitched image (default: 12000px)
        quality: JPEG quality setting (0-100) for the output image
        format: Output image format ("JPEG", "PNG", etc.)
        
    Returns:
        List of PIL Image objects for the stitched images or empty list if an error occurred
    """
    if not images:
        handle_error(ValueError("No images to stitch"), "stitching images", critical=False)
        return []
    
    try:
        # Track memory usage and processing time
        try:
            start_time = time.time()
        except Exception as e:
            logger.warning(f"Error getting start time: {e}")
            start_time = 0  # Fallback value
        
        # Calculate dimensions
        if not target_width or target_width <= 0:
            target_width = max(img.width for img in images)
            logger.info(f"Using auto-detected width: {target_width}px")
        
        # Calculate height based on aspect ratio and prepare image data
        image_data = []
        for img in images:
            aspect_ratio = img.height / img.width
            new_height = int(target_width * aspect_ratio)
            image_data.append({
                'image': img,
                'height': new_height
            })
        
        # Create multiple stitched images if needed
        stitched_images = []
        current_images = []
        current_height = 0
        
        for img_data in image_data:
            # If adding this image would exceed max_height, create a new stitched image
            if current_height + img_data['height'] > max_height and current_images:
                # Create and add the current stitched image
                logger.info(f"Creating stitched image with height: {current_height}px")
                stitched_img = create_single_stitched_image(current_images, target_width)
                if stitched_img:
                    stitched_images.append(stitched_img)
                
                # Reset for the next stitched image
                current_images = []
                current_height = 0
            
            # Add the current image to the batch
            current_images.append(img_data)
            current_height += img_data['height']
        
        # Create the final stitched image with any remaining images
        if current_images:
            logger.info(f"Creating final stitched image with height: {current_height}px")
            stitched_img = create_single_stitched_image(current_images, target_width)
            if stitched_img:
                stitched_images.append(stitched_img)
        
        try:
            elapsed_time = time.time() - start_time
            logger.info(f"Stitching completed in {elapsed_time:.2f} seconds, created {len(stitched_images)} image(s)")
        except Exception as e:
            logger.warning(f"Error calculating elapsed time: {e}")
            logger.info(f"Stitching completed, created {len(stitched_images)} image(s)")
        
        return stitched_images
    
    except Exception as e:
        handle_error(e, "stitching images", critical=False)
        return []


def create_single_stitched_image(image_data, target_width):
    """
    Create a single stitched image from the provided image data
    
    Args:
        image_data: List of dictionaries containing 'image' and 'height'
        target_width: Width for the stitched image
        
    Returns:
        PIL Image object of the stitched image or None if an error occurred
    """
    try:
        total_height = sum(data['height'] for data in image_data)
        
        # Create a new blank image
        stitched_img = Image.new('RGB', (target_width, total_height), (255, 255, 255))
        
        # Paste each image
        y_offset = 0
        for i, data in enumerate(image_data):
            try:
                # Resize the image to fit the target width while maintaining aspect ratio
                resized_img = data['image'].resize((target_width, data['height']), Image.LANCZOS)
                stitched_img.paste(resized_img, (0, y_offset))
                y_offset += data['height']
                
                # Free up memory
                resized_img = None
                
            except Exception as e:
                handle_error(e, f"processing image {i+1}", critical=False)
                # Continue with remaining images
        
        return stitched_img
    
    except Exception as e:
        handle_error(e, "creating stitched image", critical=False)
        return None


def save_stitched_images(stitched_images, output_path_template, quality=90, format="JPEG"):
    """
    Save multiple stitched images to disk with error handling
    
    Args:
        stitched_images: List of PIL Image objects to save
        output_path_template: Template path where images should be saved (e.g., "path/to/chapter.jpg")
                             Will be modified to "path/to/1.jpg", "path/to/2.jpg", etc. for multiple images
        quality: JPEG quality setting (0-100)
        format: Output image format ("JPEG", "PNG", etc.)
        
    Returns:
        list: List of saved file paths, empty if failed
    """
    if not stitched_images:
        handle_error(ValueError("No images to save"), "saving stitched images", critical=False)
        return []
    
    saved_paths = []
    
    try:
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path_template)
        os.makedirs(output_dir, exist_ok=True)
        
        # Get file extension
        _, ext = os.path.splitext(output_path_template)
        
        # If there's only one image, use simple "1.jpg" naming
        if len(stitched_images) == 1:
            output_path = os.path.join(output_dir, f"1{ext}")
            stitched_images[0].save(output_path, format, quality=quality)
            logger.info(f"Saved stitched image to {output_path}")
            saved_paths.append(output_path)
        else:
            # Save multiple images with simple numeric names: 1.jpg, 2.jpg, etc.
            for i, img in enumerate(stitched_images):
                output_path = os.path.join(output_dir, f"{i+1}{ext}")
                img.save(output_path, format, quality=quality)
                logger.info(f"Saved stitched image part {i+1} to {output_path}")
                saved_paths.append(output_path)
        
        return saved_paths
        
    except Exception as e:
        handle_error(e, "saving stitched images", critical=False)
        return saved_paths


def stitch_folder_multi_page(input_folder, output_file, target_width=None, max_height=12000, quality=90):
    """
    Stitch all images in a folder into multiple images if needed
    
    Args:
        input_folder: Path to folder containing images to stitch
        output_file: Path template where the stitched images should be saved
        target_width: Target width for the stitched images
        max_height: Maximum height for a single stitched image
        quality: JPEG quality setting (0-100)
        
    Returns:
        list: List of saved file paths, empty if failed
    """
    if not os.path.exists(input_folder):
        handle_error(FileNotFoundError(f"Input folder does not exist: {input_folder}"), "stitching folder", critical=False)
        return []
    
    try:
        # Get all image files in the folder
        image_files = [f for f in os.listdir(input_folder) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        
        if not image_files:
            handle_error(ValueError(f"No image files found in {input_folder}"), "stitching folder", critical=False)
            return []
        
        # Sort files numerically if possible
        try:
            image_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))
        except:
            # Fall back to alphabetical sorting
            image_files.sort()
            
        logger.info(f"Found {len(image_files)} images to stitch")
        
        # Load all images
        images = []
        for img_file in image_files:
            try:
                img_path = os.path.join(input_folder, img_file)
                img = Image.open(img_path)
                images.append(img)
            except Exception as e:
                handle_error(e, f"loading image {img_file}", critical=False)
        
        # Stitch images
        stitched_images = stitch_images_multi_page(images, target_width, max_height, quality)
        
        # Save results
        if stitched_images:
            return save_stitched_images(stitched_images, output_file, quality)
        else:
            return []
            
    except Exception as e:
        handle_error(e, "stitching folder", critical=False)
        return []


def run_multi_page_stitcher(comic_name, chapter_name, target_width=None, max_height=12000, quality=90):
    """
    Run the multi-page stitcher for a given comic and chapter
    
    Args:
        comic_name: Name of the comic
        chapter_name: Name of the chapter
        target_width: Target width for the stitched image
        max_height: Maximum height for a single stitched image
        quality: JPEG quality setting (0-100)
        
    Returns:
        list: List of saved file paths, empty if failed
    """
    # Sanitize names for file paths
    safe_comic_name = comic_name.replace('/', '_').replace('\\', '_')
    safe_chapter_name = chapter_name.replace('/', '_').replace('\\', '_')
    
    # Set up paths
    input_folder = os.path.join("downloads", safe_comic_name, safe_chapter_name)
    output_dir = os.path.join("processed", safe_comic_name)
    output_file = os.path.join(output_dir, f"{safe_chapter_name}.jpg")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Stitching {comic_name} - {chapter_name} with multi-page support")
    return stitch_folder_multi_page(input_folder, output_file, target_width, max_height, quality)


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Stitch manga images into multiple files if needed")
    parser.add_argument("comic_name", help="Name of the comic")
    parser.add_argument("chapter_name", help="Name of the chapter")
    parser.add_argument("--width", type=int, help="Target width for the stitched image")
    parser.add_argument("--max-height", type=int, default=12000, help="Maximum height for a single stitched image")
    parser.add_argument("--quality", type=int, default=90, help="JPEG quality (0-100)")
    
    args = parser.parse_args()
    
    saved_files = run_multi_page_stitcher(
        args.comic_name, 
        args.chapter_name, 
        args.width, 
        args.max_height, 
        args.quality
    )
    
    if saved_files:
        print(f"Successfully stitched {args.comic_name} - {args.chapter_name} into {len(saved_files)} file(s)")
        for file in saved_files:
            print(f"  - {file}")
    else:
        print(f"Failed to stitch {args.comic_name} - {args.chapter_name}")
        sys.exit(1)