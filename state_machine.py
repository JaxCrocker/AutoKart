# DEPRECATED - NOT USED FOR FINAL IMPLEMENTATION

from transitions import Machine
import serial
import time

# === Serial Setup ===
ser = serial.Serial('COM3', 9600)  # COM3 - closer port on left side
time.sleep(2)  # Let serial connection settle

# === Constants ===
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter"
]

# === State Machine ===
states = [
    'normal_drive', 'slow_drive', 'slight_left', 'slight_right', 'stop',
    'hard_left', 'hard_right'
]

transitions = [
    {'trigger': 'see_person_close', 'source': '*', 'dest': 'stop'},
    {'trigger': 'see_stop_sign_close', 'source': '*', 'dest': 'stop'},
    {'trigger': 'see_clear_path', 'source': '*', 'dest': 'normal_drive'},
    {'trigger': 'see_narrow_road', 'source': '*', 'dest': 'slow_drive'},
    {'trigger': 'see_curb_left', 'source': '*', 'dest': 'slight_right'},
    {'trigger': 'see_curb_right', 'source': '*', 'dest': 'slight_left'},
    {'trigger': 'make_hard_left', 'source': '*', 'dest': 'hard_left'},
    {'trigger': 'make_hard_right', 'source': '*', 'dest': 'hard_right'},
    {'trigger': 'resume_straight', 'source': ['slight_left', 'slight_right', 'hard_left', 'hard_right'], 'dest': 'normal_drive'},
]

# === Class Definition ===
class GoKart:
    def __init__(self):
        self.machine = Machine(model=self, states=states, transitions=transitions, initial='normal_drive')

    def compute_command(self):
        # Define commands for each state: (steering, speed_percent)
        command_map = {
            'stop': (0, 0),
            'normal_drive': (0, 40),
            'slow_drive': (0, 20),
            'slight_left': (-30, 30),
            'slight_right': (30, 30),
            'hard_left': (-80, 20),
            'hard_right': (80, 20)
        }
        return command_map[self.state]
# OLD COMMAND IMPLEMENTATION
    def send_to_teensy(self):
        steer, speed = self.compute_command()
        packet = f"{steer},{speed}\n"
        print(f"Sending: {packet.strip()}")
        ser.write(packet.encode())
