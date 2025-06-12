import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import os
import logging

# --- Configuration ---
# Assuming this script is in emotion-recognition-app/app/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'model_optimal.h5')
HAAR_CASCADE_PATH = os.path.join(BASE_DIR, 'cascades', 'haarcascade_frontalface_default.xml')

EMOTION_LABELS = ['SURPRISED', 'FEARFUL', 'DISGUSTED', 'HAPPY', 'SAD', 'ANGRY', 'NEUTRAL']
CNN_INPUT_SIZE = (100, 100) # Should match targetx, targety from your cnn.py

# --- Load Model and Face Detector ---
emotion_model = None
face_cascade = None

def load_resources():
    global emotion_model, face_cascade
    if emotion_model is None:
        try:
            emotion_model = load_model(MODEL_PATH)
            logging.info(f"Keras model loaded successfully from {MODEL_PATH}")
        except Exception as e:
            logging.error(f"Error loading Keras model from {MODEL_PATH}: {e}", exc_info=True)
            raise RuntimeError(f"Could not load emotion model: {e}")

    if face_cascade is None:
        try:
            face_cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
            if face_cascade.empty():
                raise IOError(f"Haar cascade file not found or is empty at {HAAR_CASCADE_PATH}")
            logging.info(f"Haar cascade loaded successfully from {HAAR_CASCADE_PATH}")
        except Exception as e:
            logging.error(f"Error loading Haar Cascade from {HAAR_CASCADE_PATH}: {e}", exc_info=True)
            raise RuntimeError(f"Could not load face cascade: {e}")

def predict_emotions_on_frame_data(frame: np.ndarray):
    """
    Detects faces in a frame and predicts emotions.
    Returns a list of dictionaries, each containing 'roi' (x,y,w,h) and 'emotion'.
    """
    if emotion_model is None or face_cascade is None:
        logging.warning("Model or cascade not loaded. Call load_resources() first.")
        return []

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray_frame,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    detections = []
    for (x, y, w, h) in faces:
        face_roi_color = frame[y:y+h, x:x+w]
        if face_roi_color.size == 0:
            logging.warning(f"Empty face ROI at ({x},{y},{w},{h}), skipping.")
            continue
        try:
            resized_face = cv2.resize(face_roi_color, CNN_INPUT_SIZE)
            face_array = img_to_array(resized_face)
            face_array = face_array / 255.0  # Normalize
            face_batch = np.expand_dims(face_array, axis=0)

            predictions = emotion_model.predict(face_batch, verbose=0) # verbose=0 for less console output
            emotion_index = np.argmax(predictions[0])
            predicted_emotion = EMOTION_LABELS[emotion_index]
            detections.append({"roi": [int(x), int(y), int(w), int(h)], "emotion": predicted_emotion})
        except Exception as e:
            logging.error(f"Error during prediction for a face ROI: {e}", exc_info=True)
            detections.append({"roi": [int(x), int(y), int(w), int(h)], "emotion": "Error"})
            
    return detections

def draw_labels_on_frame(frame: np.ndarray, detections: list) -> np.ndarray:
    """
    Draws bounding boxes and emotion labels on the frame.
    """
    for detection in detections:
        x, y, w, h = detection["roi"]
        emotion = detection["emotion"]
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    return frame

# Call load_resources() when this module is imported so model and cascade are ready.
# However, for FastAPI, it's better to load them during startup event.
# We'll keep the function and call it from main.py's startup.