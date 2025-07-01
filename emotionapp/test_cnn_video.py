import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import os

# --- Configuration ---
MODEL_PATH = 'model/model_optimal.h5'  # Path to your trained Keras CNN model
HAAR_CASCADE_PATH = 'haarcascade_frontalface_default.xml' # Path to Haar Cascade XML
EMOTION_LABELS = ['SURPRISED', 'FEARFUL', 'DISGUSTED', 'HAPPY', 'SAD', 'ANGRY', 'NEUTRAL']
CNN_INPUT_SIZE = (100, 100) # Should match targetx, targety from cnn.py

INPUT_VIDEO_PATH = 'neutral.mp4' # Replace with your input video file
OUTPUT_VIDEO_PATH = 'output_neutral.mp4' # Changed output name

PROCESS_EVERY_N_FRAMES = 5 # Process every 5th frame

# --- Load Model and Face Detector ---
try:
    emotion_model = load_model(MODEL_PATH)
    print(f"Model '{MODEL_PATH}' loaded successfully.")
except Exception as e:
    print(f"Error loading Keras model: {e}")
    print(f"Please ensure '{MODEL_PATH}' exists and is a valid Keras model file.")
    exit()

try:
    face_cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
    if face_cascade.empty():
        raise IOError(f"Could not load Haar cascade classifier from '{HAAR_CASCADE_PATH}'")
    print(f"Face detector '{HAAR_CASCADE_PATH}' loaded successfully.")
except Exception as e:
    print(f"Error loading Haar Cascade: {e}")
    print(f"Please ensure '{HAAR_CASCADE_PATH}' is in the correct path or download it.")
    exit()

# --- Initialize Video Capture and Writer ---
cap = cv2.VideoCapture(INPUT_VIDEO_PATH)
if not cap.isOpened():
    print(f"Error: Could not open video file {INPUT_VIDEO_PATH}")
    exit()

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, fps, (frame_width, frame_height))

print(f"Processing video: {INPUT_VIDEO_PATH}")
print(f"Output will be saved to: {OUTPUT_VIDEO_PATH}")
print(f"Processing every {PROCESS_EVERY_N_FRAMES} frames.")

frame_count = 0
last_detected_faces_emotions = [] # Store last known faces and emotions

while True:
    ret, frame = cap.read()
    if not ret:
        print("End of video or error reading frame.")
        break

    frame_count += 1

    current_faces_emotions = []

    if frame_count % PROCESS_EVERY_N_FRAMES == 0:
        # Only process this frame for new detections and predictions
        if frame_count % 100 < PROCESS_EVERY_N_FRAMES : # Log progress less frequently but aligned with processing
             print(f"Processing around frame {frame_count}...")

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        processed_face_data = []
        for (x, y, w, h) in faces:
            face_roi_color = frame[y:y+h, x:x+w]
            try:
                resized_face = cv2.resize(face_roi_color, CNN_INPUT_SIZE)
                face_array = img_to_array(resized_face)
                face_array = face_array / 255.0
                face_batch = np.expand_dims(face_array, axis=0)

                predictions = emotion_model.predict(face_batch, verbose=0)
                emotion_index = np.argmax(predictions[0])
                predicted_emotion = EMOTION_LABELS[emotion_index]
                processed_face_data.append(((x, y, w, h), predicted_emotion))
            except Exception as e:
                # print(f"Error during prediction for a face: {e}")
                processed_face_data.append(((x, y, w, h), "Error"))
        
        last_detected_faces_emotions = processed_face_data # Update with new detections
        current_faces_emotions = processed_face_data
    else:
        # For non-processed frames, use the last known detections
        current_faces_emotions = last_detected_faces_emotions

    # Draw results on the frame (either new or from last processed frame)
    for (coords, emotion_label) in current_faces_emotions:
        (x, y, w, h) = coords
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, emotion_label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    out.write(frame)

cap.release()
out.release()
cv2.destroyAllWindows()
print(f"Video processing complete. Output saved to {OUTPUT_VIDEO_PATH}")