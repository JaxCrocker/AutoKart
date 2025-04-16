import cv2
import time
import serial
from road_detector import find_road
from object_detector import detect_objects

# Add timing variables
stop_sign_timer = 0
STOP_DURATION = 5  # seconds to stop at sign
cooldown_timer = 0
COOLDOWN_DURATION = 20  # seconds before allowing another stop

MIN_STEER = -220
MAX_STEER = 220

def send_command(steering, speed, ser_connection):
    """
    Combines steering (-140 to +140) and speed (0 to 100) into a single integer.
    Examples:
        steering=30, speed=15  -> 30015
        steering=-80, speed=0  -> -80000
        steering=-30, speed=20 -> -30020
    """    
    if steering < 0:
        combined = (steering * 1000) - speed
    else:
        combined = (steering * 1000) + speed
        
    command = f"{combined}\n"
    ser_connection.write(command.encode())
    print(combined)

def determine_command(detections, road_center):
    """logic to determine steering and speed"""
    global stop_sign_timer, cooldown_timer
    
    # Default: go straight at moderate speed
    steering = 0
    speed = 30
    
    current_time = time.time()
    
    # SPEED DETERMINATION - DETECTIONS ONLY

    # Check if we're in a stop sign wait period
    if stop_sign_timer > 0:
        if current_time - stop_sign_timer >= STOP_DURATION:
            stop_sign_timer = 0  # Reset timer after waiting
            cooldown_timer = current_time  # Start cooldown
        else:
            speed = 0  # Keep stopping while timer active
    
    # Check for obstacles
    for det in detections:
        size = det["bbox"][2] - det["bbox"][0]  # width
        if det["class_name"] == "person" and size > 100:
            speed = 0
        if det["class_name"] == "stop sign" and size > 75:
            # Only stop if we're not in cooldown period
            if cooldown_timer == 0 or (current_time - cooldown_timer >= COOLDOWN_DURATION):
                if stop_sign_timer == 0:  # Start stop timer if not already timing
                    stop_sign_timer = current_time
                speed = 0
    
    # STEERING DETERMINATION - ROAD ONLY
    if road_center is not None:
        steering = int((road_center - 50)*MAX_STEER/10)
        if steering > MAX_STEER:
            steering = MAX_STEER
        elif steering < MIN_STEER:
            steering = MIN_STEER

    return steering, speed

if __name__ == "__main__":
    # Initialize serial only when running as main script
    ser = serial.Serial('COM3', 115200)
    time.sleep(2)  # Let serial settle

    # Main control loop
    cam = cv2.VideoCapture(1) # 0 for laptop, 1 or 2 for cameras

    try:
        while True:
            start_time = time.time()
            
            ret, frame = cam.read()
            if not ret:
                print("Error: Unable to read from camera")
                break

            # Process frame
            detections = detect_objects(frame)
            road_center = find_road(frame)

            # Determine and send command
            steering, speed = determine_command(detections, road_center)
            send_command(steering, speed, ser)

            # Maintain 2 FPS
            time.sleep(max(0, 0.5 - (time.time() - start_time)))

    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        send_command(0, 0, ser)  # Stop the kart if there's an error
        cam.release()
        ser.close()
