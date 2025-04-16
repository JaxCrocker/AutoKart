import torch
import numpy as np
import cv2
from PIL import Image
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation

# Load processor and model
processor = SegformerImageProcessor(do_reduce_labels=True)
model = SegformerForSemanticSegmentation.from_pretrained("nvidia/segformer-b0-finetuned-ade-512-512")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
model.eval()

# make sure road pieces too far away are not included
highest_road_center = 1

# ADE20K road class is 6
ROAD_CLASS_ID = 6

def preprocess_image(image):
    # Convert cv2 image to PIL
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    # Keep original size for later
    original_size = image.size
    # Preprocess image
    inputs = processor(images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    return inputs, image, original_size

def get_drivable_mask(outputs, original_size):
    logits = outputs.logits
    # Get predictions
    preds = torch.argmax(logits.squeeze(), dim=0).detach().cpu().numpy()
    # Create binary mask
    mask = (preds == ROAD_CLASS_ID).astype(np.uint8)
    # Resize mask back to original image size
    mask = cv2.resize(mask, original_size, interpolation=cv2.INTER_NEAREST)
    return mask

def calculate_road_center(mask):
    # Crop mask to only consider the bottom portion
    height = mask.shape[0]
    crop_height = int(height * highest_road_center)
    cropped_mask = mask[height - crop_height:height, :]
    
    # Calculate moments of the binary mask
    M = cv2.moments(cropped_mask)
    # Calculate horizontal position as percentage
    if M["m00"] != 0:
        cX = int(M["m10"] / M["m00"])
        # Convert to percentage (0-100)
        width = mask.shape[1]
        percentage = int((cX / width) * 100)
        return percentage
    return None

def find_road(frame):
    # Preprocess
    inputs, original_image, original_size = preprocess_image(frame)
    
    # Run inference
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Get mask and resize to original image size
    drivable_mask = get_drivable_mask(outputs, original_size)
    
    # Calculate road center as percentage
    center_percent = calculate_road_center(drivable_mask)
    
    return center_percent

#example usage
if __name__ == "__main__":
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    # Warm up the camera
    print("Warming up camera...")
    for _ in range(30):
        ret = cap.read()[0]
        if not ret:
            break
    
    # Capture the actual frame
    print("Capturing frame...")
    ret, frame = cap.read()
    if ret:
        # Process frame
        center_percent = find_road(frame)
        
        if center_percent is not None:
            print(f"Road center percentage: {center_percent}%")
    
    # Cleanup
    cap.release()