const VideoModule = (() => {
    // DOM Elements
    let videoFileInput, selectVideoFileBtn, selectedFileName, processVideoBtn,
        videoUploadStatus, videoResultArea, resultVideoPlayer, downloadResultLink;

    function queryDOMElements() {
        videoFileInput = document.getElementById('videoFileInput');
        selectVideoFileBtn = document.getElementById('selectVideoFileBtn');
        selectedFileName = document.getElementById('selectedFileName');
        processVideoBtn = document.getElementById('processVideoBtn');
        videoUploadStatus = document.getElementById('videoUploadStatus');
        videoResultArea = document.getElementById('videoResultArea');
        resultVideoPlayer = document.getElementById('resultVideoPlayer');
        downloadResultLink = document.getElementById('downloadResultLink');
    }

    function handleFileSelection() {
        if (videoFileInput.files.length > 0) {
            selectedFileName.textContent = videoFileInput.files[0].name;
            processVideoBtn.disabled = false;
        } else {
            selectedFileName.textContent = 'No file selected.';
            processVideoBtn.disabled = true;
        }
    }

    async function uploadAndProcessVideo() {
        const file = videoFileInput.files[0];
        if (!file) {
            alert('Please select a video file first.');
            return;
        }

        processVideoBtn.disabled = true;
        selectVideoFileBtn.disabled = true;
        videoUploadStatus.textContent = 'Uploading and processing... This may take a while.';
        videoUploadStatus.style.display = 'block';
        videoResultArea.style.display = 'none';
        downloadResultLink.style.display = 'none';

        try {
            const result = await uploadVideoForProcessing(file); // from api.js
            videoUploadStatus.textContent = `Server: ${result.message || 'Processing complete.'}`;
            
            if (result.download_url) {
                const fullDownloadUrl = `${API_BASE_URL}${result.download_url}`; // API_BASE_URL from api.js
                resultVideoPlayer.src = fullDownloadUrl;
                downloadResultLink.href = fullDownloadUrl;
                downloadResultLink.download = `processed_${file.name}`;

                videoResultArea.style.display = 'block';
                downloadResultLink.style.display = 'inline-flex';
            } else {
                videoUploadStatus.textContent += ' No download link received.';
            }

        } catch (error) {
            console.error('Error uploading/processing video:', error);
            videoUploadStatus.textContent = `Error: ${error.message}`;
            alert(`Error processing video: ${error.message}`);
        } finally {
            processVideoBtn.disabled = false;
            selectVideoFileBtn.disabled = false;
        }
    }
    
    function resetVideoUploadUI() {
        if (!videoFileInput) queryDOMElements();
        videoFileInput.value = ''; // Clear selected file
        selectedFileName.textContent = 'No file selected.';
        processVideoBtn.disabled = true;
        videoUploadStatus.style.display = 'none';
        videoUploadStatus.textContent = '';
        videoResultArea.style.display = 'none';
        if(resultVideoPlayer) resultVideoPlayer.src = '';
        downloadResultLink.style.display = 'none';
    }


    function init() {
        queryDOMElements();
        selectVideoFileBtn.addEventListener('click', () => videoFileInput.click());
        videoFileInput.addEventListener('change', handleFileSelection);
        processVideoBtn.addEventListener('click', uploadAndProcessVideo);
        resetVideoUploadUI(); // Ensure clean state on init
    }
    
    function cleanup() { // Called when navigating away
        resetVideoUploadUI();
        // Stop video player if playing, etc.
        if (resultVideoPlayer && !resultVideoPlayer.paused) {
            resultVideoPlayer.pause();
        }
        // Optionally reset the UI fully
        // resetVideoUploadUI(); 
        // No specific event listeners to remove here as they are on static elements within the page section
    }

    return {
        init: init,
        cleanup: cleanup
    };
})();