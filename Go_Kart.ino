#include <Servo.h>
#include <PID_v1.h>

// Pin definitions
#define SMOTOR_A_PIN A4 //green
#define SMOTOR_B_PIN A5 //white
#define SMOTOR_Z_PIN A6 //yellow
#define STEERING_A_PIN A7
#define STEERING_B_PIN A8
#define STEERING_Z_PIN A9
#define DRIVE_PIN 0
#define STEER_PIN 1
#define AUTONOMOUS 3
#define MANUAL 2
#define LED 13

// manual/auto toggle (UNUSED FOR NOW)
//bool manual = true;

// Servo objects
Servo Steer;
Servo Drive;

// Constants
const int PULSES_PER_REV = 2000;
const double DEGREES_PER_TICK = 360.0 / PULSES_PER_REV;

//Maximum steering speed and drive speed
const int MAX_LEFT = 1750;
const int NO_STEER = 1500;
const int MAX_RIGHT = 1250;
const int MIN_STEERING_POS = -250;
const int MAX_STEERING_POS = 250;
const int MAX_FORWARD = 1650;

// Encoder tick counts (centered at 0)
volatile long desired_steering_pos = 0;  // Steering wheel input
volatile long current_steering_pos = 0;  // Actual wheel position
int drive_percent = 0;

// PID control variables (based on raw tick values)
double PID_input = 0;
double PID_output = 0;
const double PID_setpoint = 0;

// steering logic variables
double goal_deg = 0;
double current_deg = 0;
double error_deg = 0;
int drive_command = 0;

// incoming autonomous command parsing
String inputString = "";
bool stringComplete = false;
int auto_steering = 0;
int auto_speed = 0;

// PID tuning parameters
double Kp = 4.0, Ki = 0.08, Kd = 1;
PID steerPID(&PID_input, &PID_output, &PID_setpoint, Kp, Ki, Kd, DIRECT);

// ISR state tracking
volatile int lastSteeringA = LOW;
volatile int lastSmotorA = LOW;

void setup() {
  Serial.begin(115200);
  inputString.reserve(200);

  Drive.attach(DRIVE_PIN);
  Steer.attach(STEER_PIN);

  pinMode(LED, OUTPUT);
  pinMode(STEERING_A_PIN, INPUT);
  pinMode(STEERING_B_PIN, INPUT);
  pinMode(STEERING_Z_PIN, INPUT);
  pinMode(SMOTOR_A_PIN, INPUT);
  pinMode(SMOTOR_B_PIN, INPUT);
  pinMode(SMOTOR_Z_PIN, INPUT);
  pinMode(AUTONOMOUS, INPUT_PULLUP); // anti glitchy input_pulldown
  pinMode(MANUAL, INPUT_PULLUP);


  // Interrupts for encoders
  attachInterrupt(digitalPinToInterrupt(STEERING_A_PIN), steeringEncoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(SMOTOR_A_PIN), smotorEncoderISR, CHANGE);

  steerPID.SetMode(AUTOMATIC);
  steerPID.SetOutputLimits(NO_STEER - MAX_LEFT, NO_STEER - MAX_RIGHT);

  // Blink LED to confirm setup
  // for (int i = 0; i < 10; i++) {
  //   digitalWrite(LED, HIGH);
  //   delay(100);
  //   digitalWrite(LED, LOW);
  //   delay(100);
  // }
}

void loop() {

  // only run if complete new command has come through
  if (stringComplete) {
      // Parse the complete line into an integer
      int combined = inputString.toInt(); // commands are of the form "steering""speed" such as -80040 (-80,40) or 20000 (20,0)
      
      // Extract steering and speed
      auto_steering = (int) combined / 1000;  // preserve negative sign
      auto_speed = (int) abs(combined % 1000);  // take absolute value to ensure positive speed
      
      // Clear for next command
      inputString = "";
      stringComplete = false;
    }

  // Determining where to read from and reading
  if (digitalRead(AUTONOMOUS) == 0) {
        
    goal_deg = auto_steering;
    drive_percent = auto_speed;
    //Serial.println("Auto");

  } else if (digitalRead(MANUAL) == 0) {
    goal_deg = -2.5 * desired_steering_pos * DEGREES_PER_TICK;
    //driving happens without passing through teensy in manual mode
    //Serial.println("Manual");
  } else {
    // if switch is in off position just dont do anything
    goal_deg = 0;
    drive_percent = 0;
    //Serial.println("Nothing");
  }

  // STEERING
  current_deg = current_steering_pos * DEGREES_PER_TICK;
  goal_deg = checkSteeringMax(goal_deg);
  error_deg = goal_deg - current_deg;
  PID_input = error_deg;
  steerPID.Compute();

  int steer_command = NO_STEER + PID_output;
  steer_command = constrain(steer_command, MAX_RIGHT, MAX_LEFT);
  Steer.writeMicroseconds(steer_command);

  // DRIVING
  drive_percent = constrain(drive_percent, 0, 100);
  drive_command = map(drive_percent, 0, 100, 1545, MAX_FORWARD);
  if (drive_percent == 0){
    drive_command = 1500;
  }
  Drive.writeMicroseconds(drive_command);

  // Debugging info
  // Serial.print("Desired: ");
  // Serial.print(goal_deg);
  // Serial.print("  Current: ");
  // Serial.print(current_deg);
  // Serial.print("  Error: ");
  // Serial.print(error_deg);
  // Serial.print("  PID Output: ");
  // Serial.print(PID_output);
  // Serial.print("  Steer Command: ");
  // Serial.print(steer_command);
  // Serial.print("  Drive Command: ");
  // Serial.print(drive_command);
  // Serial.print("  Drive %: ");
  // Serial.println(drive_percent);

  delay(10);
}

// ISR: Steering wheel encoder (manual input)
void steeringEncoderISR() {
  int A = digitalRead(STEERING_A_PIN);
  int B = digitalRead(STEERING_B_PIN);
  if (A != lastSteeringA) {
    desired_steering_pos += (A == B) ? 1 : -1;
  }
  //rotating the steering wheel past 2 full rotations keeps bringing it back
  if (desired_steering_pos > 4000) {
    desired_steering_pos -= 2000;
  }
  if (desired_steering_pos < -4000) {
    desired_steering_pos += 2000;
  }
  

  lastSteeringA = A;
}

// ISR: Steering motor encoder (feedback)
void smotorEncoderISR() {
  int A = digitalRead(SMOTOR_A_PIN);
  int B = digitalRead(SMOTOR_B_PIN);
  if (A != lastSmotorA) {
    current_steering_pos += (A == B) ? 1 : -1;
  }
  lastSmotorA = A;
}

// constantly checking for new commands - built in arduino function that gets called after every iteration of loop
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}

// making sure we dont oversteer and harm motor
double checkSteeringMax(double angle) {
  if (angle < MIN_STEERING_POS) {
    angle = MIN_STEERING_POS;
  }
  if (angle > MAX_STEERING_POS) {
    angle = MAX_STEERING_POS;
  }
  return angle;
}