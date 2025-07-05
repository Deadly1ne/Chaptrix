import cv2 
import os 
import numpy as np 

def crop_banner_if_found(image_path, ref_banner, threshold=0.9): 
    image = cv2.imread(image_path) 
    if image is None: 
        print(f"Warning: Could not open: {image_path}") 
        return 

    ref_h, ref_w = ref_banner.shape[:2] 
    img_h, img_w = image.shape[:2]
    
    # Skip if image is smaller than reference banner
    if img_h < ref_h or img_w < ref_w:
        print(f"Warning: Image too small for banner detection: {image_path}")
        return
    
    for location in ['top', 'bottom']: 
        # Make sure we don't try to access more pixels than exist in the image
        if location == 'top':
            area_height = min(ref_h + 20, img_h)
            crop_area = image[:area_height, :]
        else:  # bottom
            area_height = min(ref_h + 20, img_h)
            crop_area = image[-area_height:, :]
        
        # Skip if crop area is smaller than reference banner
        if crop_area.shape[0] < ref_h or crop_area.shape[1] < ref_w:
            continue
            
        try:
            res = cv2.matchTemplate(crop_area, ref_banner, cv2.TM_CCOEFF_NORMED) 
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res) 

            if max_val >= threshold: 
                print(f"Success: Match found at {location} of {image_path} (confidence={max_val:.2f})") 
                if location == 'top': 
                    image = image[ref_h:, :] 
                else: 
                    image = image[:-(ref_h), :]
        except cv2.error as e:
            print(f"Warning: Error processing {location} of {image_path}: {e}")
            continue

    cv2.imwrite(image_path, image) 


def crop_folder(folder_path, banner_path): 
    ref_banner = cv2.imread(banner_path) 
    if ref_banner is None: 
        print(f"❌ Could not load banner image from: {banner_path}") 
        return 

    print(f"🔍 Looking in: {folder_path}") 
    for filename in os.listdir(folder_path): 
        if filename.lower().endswith(".jpg"): 
            full_path = os.path.join(folder_path, filename) 
            print(f"🔍 Checking image: {full_path}") 
            crop_banner_if_found(full_path, ref_banner) 


def run_cropper(comic_name, chapter_name): 
    folder_path = f"downloads/{comic_name}/{chapter_name}" 
    banner_path = "assets/banner.png" 
    crop_folder(folder_path, banner_path) 

if __name__ == "__main__": 
    run_cropper("Apocalyptic Food Stall", "Chapter_53")