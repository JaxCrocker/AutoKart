from ultralytics import YOLO
import cv2

# Load YOLO model
model = YOLO("yolov8n.pt")

# COCO class names up to stop sign as the ones after don't relate to roads
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign"
]

def detect_objects(frame):
    """
    Run YOLO inference a frame and return detections
    """
    # Run YOLO inference on both frames
    results = model(frame)

    # Extract detection details for Camera 1
    detections = []
    for box in results[0].boxes:
        class_id = int(box.cls.item())
        if class_id >= len(COCO_CLASSES):  # Ignore classes outside the defined range
            continue
        bbox = box.xyxy[0].tolist()  # Ensure bbox is a flat list
        detections.append({
            "class_id": class_id,
            "class_name": COCO_CLASSES[class_id],
            "confidence": round(box.conf.item(), 2),
            "bbox": [int(coord) for coord in bbox]
        })
    return detections


# Standalone testing
if __name__ == "__main__":
    # Initialize webcams
    cam1 = cv2.VideoCapture(0)  # First webcam (ID 0)

    # Read frames from both cameras
    ret1, frame = cam1.read()

    if ret1:
        # Detect objects in both frames
        detections = detect_objects(frame)

        # Print detection results
        print("Detections from Camera 1:", detections)
    else:
        print("Error: Unable to read from one or both cameras.")

    # Release resources
    cam1.release()
