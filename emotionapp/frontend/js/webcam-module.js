const WebcamModule = (() => {
    let stream = null;
    let animationFrameId = null;
    let isProcessingFrame = false;

    // DOM Elements (will be queried when page is active)
    let webcamVideoFeed, webcamOverlayCanvas, webcamStatusMessage, startWebcamBtn, stopWebcamBtn;
    let webcamOverlayContext;

    function queryDOMElements() {
        webcamVideoFeed = document.getElementById('webcamVideoFeed');
        webcamOverlayCanvas = document.getElementById('webcamOverlayCanvas');
        webcamStatusMessage = document.getElementById('webcamStatusMessage');
        startWebcamBtn = document.getElementById('startWebcamBtn');
        stopWebcamBtn = document.getElementById('stopWebcamBtn');
        if (webcamOverlayCanvas) {
            webcamOverlayContext = webcamOverlayCanvas.getContext('2d');
        }
    }

    async function startWebcam() {
        if (!webcamVideoFeed) queryDOMElements(); // Ensure elements are queried

        try {
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
                webcamVideoFeed.srcObject = stream;
                webcamStatusMessage.textContent = 'Webcam active. Initializing...';
                startWebcamBtn.style.display = 'none';
                stopWebcamBtn.style.display = 'inline-flex';

                webcamVideoFeed.onloadedmetadata = () => {
                    webcamOverlayCanvas.width = webcamVideoFeed.videoWidth;
                    webcamOverlayCanvas.height = webcamVideoFeed.videoHeight;
                    webcamStatusMessage.textContent = 'Processing frames...';
                    startFrameProcessingLoop();
                };
            } else {
                const msg = 'getUserMedia not supported on your browser!';
                webcamStatusMessage.textContent = msg;
                alert(msg);
            }
        } catch (err) {
            console.error("Error accessing webcam: ", err);
            const msg = `Error accessing webcam: ${err.name} - ${err.message}`;
            webcamStatusMessage.textContent = msg;
            alert(msg);
            stopWebcam(); // Reset UI
        }
    }

    function stopWebcam() {
        if (!webcamVideoFeed) queryDOMElements();

        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }
        if (webcamVideoFeed) webcamVideoFeed.srcObject = null;
        if (webcamOverlayContext) webcamOverlayContext.clearRect(0, 0, webcamOverlayCanvas.width, webcamOverlayCanvas.height);
        
        webcamStatusMessage.textContent = 'Webcam is off.';
        startWebcamBtn.style.display = 'inline-flex';
        stopWebcamBtn.style.display = 'none';
        isProcessingFrame = false;
    }

    
    async function processCurrentFrame() {
        if (!stream || webcamVideoFeed.paused || webcamVideoFeed.ended || isProcessingFrame) {
            if (stream) animationFrameId = requestAnimationFrame(processCurrentFrame);
            return;
        }
        isProcessingFrame = true;

        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = webcamVideoFeed.videoWidth;
        tempCanvas.height = webcamVideoFeed.videoHeight;
        const tempCtx = tempCanvas.getContext('2d');
        
        // REMOVE/COMMENT OUT THESE MIRRORING LINES:
        // tempCtx.translate(tempCanvas.width, 0);
        // tempCtx.scale(-1, 1); 
        
        tempCtx.drawImage(webcamVideoFeed, 0, 0, tempCanvas.width, tempCanvas.height);
        
        // And no need to reset transform if it wasn't applied for capture
        // tempCtx.setTransform(1, 0, 0, 1, 0, 0); 

        try {
            tempCanvas.toBlob(async (blob) => {
                if (blob) {
                    const processedImageBlob = await predictWebcamFrame(blob); // from api.js
                    const imageUrl = URL.createObjectURL(processedImageBlob);
                    
                    const img = new Image();
                    img.onload = () => {
                        if (webcamOverlayContext && webcamOverlayCanvas) { // Check if context and canvas are still valid
                            webcamOverlayContext.clearRect(0, 0, webcamOverlayCanvas.width, webcamOverlayCanvas.height);
                            webcamOverlayContext.drawImage(img, 0, 0, webcamOverlayCanvas.width, webcamOverlayCanvas.height);
                        }
                        URL.revokeObjectURL(imageUrl);
                        isProcessingFrame = false;
                        if (stream) animationFrameId = requestAnimationFrame(processCurrentFrame);
                    };
                    img.onerror = () => {
                        console.error("Error loading processed image onto canvas.");
                        isProcessingFrame = false;
                        if (stream) animationFrameId = requestAnimationFrame(processCurrentFrame);
                    };
                    img.src = imageUrl;
                } else {
                    console.warn("Failed to create blob from canvas for webcam frame.");
                    isProcessingFrame = false;
                    if (stream) animationFrameId = requestAnimationFrame(processCurrentFrame);
                }
            }, 'image/jpeg');
        } catch (error) {
            console.error('Error processing frame:', error);
            if(webcamStatusMessage) webcamStatusMessage.textContent = `Error: ${error.message}. Retrying...`;
            isProcessingFrame = false;
            setTimeout(() => {
                if (stream) animationFrameId = requestAnimationFrame(processCurrentFrame);
            }, 500);
        }
    }


    function startFrameProcessingLoop() {
        if (animationFrameId) cancelAnimationFrame(animationFrameId);
        animationFrameId = requestAnimationFrame(processCurrentFrame);
    }

    function init() {
        queryDOMElements();
        startWebcamBtn.addEventListener('click', startWebcam);
        stopWebcamBtn.addEventListener('click', stopWebcam);
        // Ensure webcam is stopped if user navigates away
        // This will be handled by main.js by calling stopWebcam when page deactivates
    }
    
    function cleanup() { // Called when navigating away from the page
        stopWebcam();
        // Remove event listeners if they were added directly here and not delegated
        // For this setup, stopWebcam handles most cleanup.
    }

    return {
        init: init,
        stop: stopWebcam, // Expose stop for external calls (e.g., page navigation)
        cleanup: cleanup
    };
})();