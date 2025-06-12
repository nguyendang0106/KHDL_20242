// (Your existing api.js content - ensure API_BASE_URL is correct)
const API_BASE_URL = 'http://127.0.0.1:8000'; // Or http://127.0.0.1:8000

async function predictWebcamFrame(imageDataBlob) {
    const formData = new FormData();
    formData.append('file', imageDataBlob, 'webcam_frame.jpg');

    try {
        const response = await fetch(`${API_BASE_URL}/predict_webcam`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
            console.error('Error from /predict_webcam:', response.status, errorData);
            throw new Error(`Server error: ${response.status} - ${errorData.detail || 'Failed to process frame'}`);
        }
        return await response.blob();
    } catch (error) {
        console.error('Network or other error in predictWebcamFrame:', error);
        throw error;
    }
}

async function uploadVideoForProcessing(videoFile) {
    const formData = new FormData();
    formData.append('file', videoFile);

    try {
        const response = await fetch(`${API_BASE_URL}/predict_video`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
            console.error('Error from /predict_video:', response.status, errorData);
            throw new Error(`Server error: ${response.status} - ${errorData.detail || 'Failed to process video'}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Network or other error in uploadVideoForProcessing:', error);
        throw error;
    }
}