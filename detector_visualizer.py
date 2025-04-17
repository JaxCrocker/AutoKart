import cv2
from object_detector import detect_objects

def visualize_detections(frame, detections):
    """Draw bounding boxes and labels on the frame."""
    output = frame.copy()
    for detection in detections:
        bbox = detection["bbox"]
        class_name = detection["class_name"]
        confidence = detection["confidence"]
        
        # Draw bounding box
        cv2.rectangle(output, 
                     (bbox[0], bbox[1]), 
                     (bbox[2], bbox[3]), 
                     (0, 255, 0), 2)
        
        # Prepare label text
        label = f'{class_name} {confidence:.2f}'
        
        # Draw label background
        (label_width, label_height), _ = cv2.getTextSize(label, 
                                                        cv2.FONT_HERSHEY_SIMPLEX, 
                                                        0.5, 1)
        cv2.rectangle(output, 
                     (bbox[0], bbox[1] - label_height - 10),
                     (bbox[0] + label_width, bbox[1]),
                     (0, 255, 0), -1)
        
        # Draw label text
        cv2.putText(output, label, 
                    (bbox[0], bbox[1] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                    (0, 0, 0), 1)
    
    return output

def main():
    # Initialize camera
    cam = cv2.VideoCapture(0)

    # warm up camera. Just taking the picture doesn't give time for autofocus/brightness
    print("Warming up camera...")
    for _ in range(30):
        ret = cam.read()[0]
        if not ret:
            break
    
    # Capture one frame
    ret, frame = cam.read()
    if not ret:
        print("Failed to capture frame")
        return
    
    # Run object detection
    detections = detect_objects(frame)
    
    # Draw detections
    output_frame = visualize_detections(frame, detections)
    
    # Save the result
    cv2.imwrite('object_detection.png', output_frame)
    
    # Clean up
    cam.release()

if __name__ == "__main__":
    main()
