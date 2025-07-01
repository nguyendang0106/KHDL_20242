from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware # For frontend development
import cv2
import numpy as np
import os
import shutil
import uuid
import logging
import io
from contextlib import asynccontextmanager

from .processing import load_resources, predict_emotions_on_frame_data, draw_labels_on_frame
from .datalogger import log_emotion_data


# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- FastAPI Lifespan Event for Model Loading ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model and cascade
    logger.info("Application startup: Loading ML model and cascade...")
    try:
        load_resources()
        logger.info("ML model and cascade loaded successfully.")
    except RuntimeError as e:
        logger.error(f"Fatal error during startup: {e}")
        # Depending on policy, you might want to prevent FastAPI from starting
        # or let it start in a degraded state. For now, it will log and continue.
    yield
    # Clean up the ML models and release the resources
    logger.info("Application shutdown: Cleaning up resources...")
    # Add any cleanup logic here if necessary

app = FastAPI(title="Emotion Recognition API", lifespan=lifespan)

# --- CORS Middleware (allow all for development, restrict in production) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

TEMP_VIDEO_DIR = "temp_videos_api" 
PROCESSED_VIDEO_DIR = "processed_videos_api"
os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)
os.makedirs(PROCESSED_VIDEO_DIR, exist_ok=True)

# --- Health Check ---
@app.get("/")
async def read_root():
    return {"message": "Emotion Recognition API is running. Model and cascade should be loaded."}

# --- API Endpoint for Webcam Frame Prediction ---
@app.post("/predict_webcam")
async def predict_webcam_frame(file: UploadFile = File(...)):
    """
    Receives a single webcam frame image, predicts emotions,
    and returns the frame with emotion labels drawn.
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            logger.warning("Received empty or invalid frame for webcam prediction.")
            raise HTTPException(status_code=400, detail="Could not decode image from received data.")

        detections = predict_emotions_on_frame_data(frame)

        # --- LOG THE DATA ---
        log_emotion_data(source='webcam', detections=detections)
        # --------------------

        labeled_frame = draw_labels_on_frame(frame.copy(), detections) # Use a copy

        # Encode the labeled frame to JPEG
        is_success, buffer = cv2.imencode(".jpg", labeled_frame)
        if not is_success:
            logger.error("Failed to encode labeled frame to JPEG.")
            raise HTTPException(status_code=500, detail="Failed to encode processed image.")
        
        io_buf = io.BytesIO(buffer)
        
        # Return the image as a streaming response
        return StreamingResponse(io_buf, media_type="image/jpeg")

    except HTTPException as e:
        # Re-raise HTTPException to let FastAPI handle it
        raise e
    except Exception as e:
        logger.error(f"Error in /predict_webcam: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")
    finally:
        if file:
            await file.close()


# --- API Endpoint for Uploading and Processing Video ---
@app.post("/predict_video")
async def predict_video_emotions(file: UploadFile = File(...)):
    """
    Receives an uploaded video file, processes it to detect and label emotions
    on each frame (or Nth frame), and returns the processed video file.
    """
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.webm')):
        raise HTTPException(status_code=400, detail="Invalid video file type. Please upload MP4, AVI, MOV, or WebM.")

    temp_file_path = os.path.join(TEMP_VIDEO_DIR, f"{uuid.uuid4()}_{file.filename}")
    processed_file_id = str(uuid.uuid4())
    # Ensure output is mp4 for broader compatibility, even if input is different
    output_video_path = os.path.join(PROCESSED_VIDEO_DIR, f"{processed_file_id}.mp4")

    try:
        # Save uploaded file temporarily
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Video '{file.filename}' uploaded and saved to '{temp_file_path}'.")

        cap = cv2.VideoCapture(temp_file_path)
        if not cap.isOpened():
            logger.error(f"Could not open video file: {temp_file_path}")
            raise HTTPException(status_code=500, detail=f"Could not open video file: {file.filename}")

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0: fps = 25 # Default fps if not readable

        # Use 'mp4v' for .mp4 output
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))
        
        logger.info(f"Processing video '{file.filename}' to '{output_video_path}'. Resolution: {frame_width}x{frame_height}, FPS: {fps}")

        frame_count = 0
        PROCESS_EVERY_N_FRAMES = 5 # Optimization: process every 5th frame
        last_detections = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break # End of video
            
            frame_count += 1
            current_detections_to_draw = []

            if frame_count % PROCESS_EVERY_N_FRAMES == 0:
                detections = predict_emotions_on_frame_data(frame)

                # --- LOG THE DATA ---
                log_emotion_data(source='video', detections=detections, video_filename=file.filename)
                # --------------------
                
                last_detections = detections # Store for intermediate frames
                current_detections_to_draw = detections
                if frame_count % (PROCESS_EVERY_N_FRAMES * 10) == 0: # Log progress less frequently
                    logger.info(f"Processing video '{file.filename}', around frame {frame_count}...")
            else:
                # For intermediate frames, use the last known detections
                current_detections_to_draw = last_detections
            
            frame_with_emotions = draw_labels_on_frame(frame.copy(), current_detections_to_draw)
            out_writer.write(frame_with_emotions)

        cap.release()
        out_writer.release()
        logger.info(f"Video processing complete for '{file.filename}'. Output: '{output_video_path}'")
        
        # Provide a way to download the processed video
        # The frontend will typically call a GET endpoint for this ID
        return {
            "message": "Video processed successfully.", 
            "processed_video_id": processed_file_id, # ID to use for downloading
            "download_url": f"/download_video/{processed_file_id}.mp4" # Relative URL for download
        }

    except HTTPException as e:
        raise e # Re-raise FastAPI's HTTP exceptions
    except Exception as e:
        logger.error(f"Error processing video '{file.filename}': {e}", exc_info=True)
        if os.path.exists(output_video_path): # Clean up partially processed file
            os.remove(output_video_path)
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")
    finally:
        if os.path.exists(temp_file_path): # Clean up temporary uploaded file
            os.remove(temp_file_path)
        if file:
            await file.close()

@app.get("/download_video/{video_file_name}")
async def download_video(video_file_name: str):
    """
    Allows downloading of a processed video file.
    'video_file_name' should include the .mp4 extension.
    """
    file_path = os.path.join(PROCESSED_VIDEO_DIR, video_file_name)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, media_type='video/mp4', filename=video_file_name)
    else:
        logger.warning(f"Download request for non-existent video: {video_file_name}")
        raise HTTPException(status_code=404, detail="Processed video not found.")

