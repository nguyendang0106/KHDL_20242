import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

# --- Configuration ---
MODEL_PATH = 'model/model_optimal.h5'  
HAAR_CASCADE_PATH = 'haarcascade_frontalface_default.xml' 
EMOTION_LABELS = ['SURPRISED', 'FEARFUL', 'DISGUSTED', 'HAPPY', 'SAD', 'ANGRY', 'NEUTRAL']
CNN_INPUT_SIZE = (100, 100) # targetx, targety from cnn.py

# --- Load Model and Face Detector ---
try:
    emotion_model = load_model(MODEL_PATH)
except Exception as e:
    print(f"Error loading Keras model: {e}")
    print(f"Please ensure '{MODEL_PATH}' exists and is a valid Keras model file.")
    exit()

try:
    face_cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
    if face_cascade.empty():
        raise IOError(f"Could not load Haar cascade classifier from '{HAAR_CASCADE_PATH}'")
except Exception as e:
    print(f"Error loading Haar Cascade: {e}")
    print("Please ensure 'haarcascade_frontalface_default.xml' is in the correct path or download it.")
    exit()

# --- Initialize Camera ---
cap = cv2.VideoCapture(0) # 0 is usually the default webcam
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Starting camera feed. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray_frame,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30), # Min face size to detect
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    for (x, y, w, h) in faces:
        # Extract the face ROI (Region of Interest)
        face_roi_color = frame[y:y+h, x:x+w]

        # Preprocess the face ROI for the CNN
        # 1. Resize to CNN input size
        resized_face = cv2.resize(face_roi_color, CNN_INPUT_SIZE)
        
        # 2. Convert to NumPy array and rescale (as done in ImageDataGenerator)
        face_array = img_to_array(resized_face)
        face_array = face_array / 255.0
        
        # 3. Expand dimensions to create a batch of 1
        face_batch = np.expand_dims(face_array, axis=0)

        # Predict emotion
        try:
            predictions = emotion_model.predict(face_batch)
            emotion_index = np.argmax(predictions[0])
            predicted_emotion = EMOTION_LABELS[emotion_index]
        except Exception as e:
            print(f"Error during prediction: {e}")
            predicted_emotion = "Error"

        # Draw rectangle around the face and put emotion text
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, predicted_emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Display the resulting frame
    cv2.imshow('Emotion Recognition CNN', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- Release resources ---
cap.release()
cv2.destroyAllWindows()
print("Application closed.")