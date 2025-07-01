import csv
import os
from datetime import datetime
import threading

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(BASE_DIR, 'logs', 'emotion_log.csv')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure the log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Use a lock to prevent race conditions when writing to the file from multiple requests
file_lock = threading.Lock()

def setup_log_file():
    """Initializes the log file with headers if it doesn't exist."""
    with file_lock:
        if not os.path.exists(LOG_FILE_PATH):
            with open(LOG_FILE_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 
                    'source', 
                    'emotion', 
                    'video_filename'
                ])

def log_emotion_data(source: str, detections: list, video_filename: str = "N/A"):
    """
    Logs detected emotions to the CSV file.
    
    Args:
        source (str): The source of the detection (e.g., 'webcam', 'video').
        detections (list): The list of detection dicts from processing.py.
        video_filename (str, optional): The name of the video file if source is 'video'.
    """
    if not detections:
        return

    timestamp = datetime.now().isoformat()
    
    rows_to_write = []
    for detection in detections:
        emotion = detection.get('emotion', 'UNKNOWN')
        rows_to_write.append([
            timestamp,
            source,
            emotion,
            video_filename
        ])

    with file_lock:
        try:
            with open(LOG_FILE_PATH, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(rows_to_write)
        except IOError as e:
            print(f"Error writing to log file: {e}") # Replace with proper logging if available

setup_log_file()