import os
import cv2
import numpy as np
import face_recognition
from scipy.spatial import distance
import serial
import time
import warnings

warnings.filterwarnings('ignore')

# === CONFIGURATION ===
EYE_AR_THRESH = 0.25          # Eye Aspect Ratio threshold
MOUTH_AR_THRESH = 0.4         # Mouth Aspect Ratio threshold
EYE_SCORE_LIMIT = 3           # Number of consecutive detections for drowsiness
YAWN_COOLDOWN = 2.0           # Seconds to ignore repeated yawns

# === INITIALIZE SERIAL COMMUNICATION ===
def init_arduino(port='COM14', baudrate=9600):
    try:
        arduino = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Allow Arduino to initialize
        print(f"[INFO] Connected to Arduino on {port}")
        return arduino
    except:
        print(f"[WARN] Could not connect to Arduino on {port}")
        return None

arduino = init_arduino()

# === FEATURE CALCULATIONS ===
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def mouth_aspect_ratio(mouth):
    A = distance.euclidean(mouth[3], mouth[9])   # Middle vertical
    B = distance.euclidean(mouth[2], mouth[10])  # Left vertical
    C = distance.euclidean(mouth[4], mouth[8])   # Right vertical
    D = distance.euclidean(mouth[0], mouth[6])   # Horizontal width
    return (A + B + C) / (3.0 * D)


# === FRAME ANALYSIS ===
def process_image(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)

    eye_closed = False
    yawn_detected = False

    for face_location in face_locations:
        landmarks = face_recognition.face_landmarks(rgb_frame, [face_location])[0]

        left_eye = np.array(landmarks['left_eye'])
        right_eye = np.array(landmarks['right_eye'])
        mouth = np.array(landmarks['bottom_lip'])

        ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0
        mar = mouth_aspect_ratio(mouth)

        if ear < EYE_AR_THRESH:
            eye_closed = True
        if mar > MOUTH_AR_THRESH:
            yawn_detected = True

    return eye_closed, yawn_detected

# === VIDEO INITIALIZATION ===
video_cap = cv2.VideoCapture(1)
video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# === MAIN LOOP VARIABLES ===
count = 0
eye_score = 0
last_yawn_time = 0
last_arduino_signal = None
start_time = time.time()

# === MAIN LOOP ===
while True:
    success, frame = video_cap.read()
    if not success:
        print("[ERROR] Frame capture failed.")
        break

    frame = cv2.resize(frame, (960, 540))
    count += 1

    n = 5  # Process every 5th frame
    current_time = time.time()

    if count % n == 0:
        eye_flag, mouth_flag = process_image(frame)

        # Eye logic
        if eye_flag:
            eye_score += 1
        else:
            eye_score = max(eye_score - 1, 0)

        # Yawn logic with cooldown
        if mouth_flag and (current_time - last_yawn_time) > YAWN_COOLDOWN:
            last_yawn_time = current_time
            yawn_alert = True
        else:
            yawn_alert = False

        # Send signal to Arduino only when status changes
        alert_condition = eye_score >= EYE_SCORE_LIMIT or yawn_alert
        new_signal = b'a' if alert_condition else b'b'

        if arduino and new_signal != last_arduino_signal:
            arduino.write(new_signal)
            last_arduino_signal = new_signal

    # === DISPLAY INFORMATION ===
    elapsed_time = current_time - start_time
    fps = count / elapsed_time if elapsed_time > 0 else 0

    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    cv2.putText(frame, f"Drwsiness Score: {eye_score}", (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    if eye_score >= EYE_SCORE_LIMIT:
        cv2.putText(frame, "Drowsy!", (frame.shape[1] - 200, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    if (current_time - last_yawn_time) <= 1.5:  # Show yawn warning for 1.5 sec
        cv2.putText(frame, "Yawning!", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)

    cv2.imshow('Drowsiness Detection', frame)

    # Exit on ESC key
    if cv2.waitKey(1) & 0xFF == 27:
        break

# === CLEANUP ===
video_cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()
