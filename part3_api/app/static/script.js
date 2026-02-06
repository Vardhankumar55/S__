document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('upload-area');
    const uploadBox = uploadArea.querySelector('.upload-box');
    const fileInput = document.getElementById('audio-input');
    const processingArea = document.getElementById('processing-area');
    const resultArea = document.getElementById('result-area');
    const resultCard = document.getElementById('result-card');
    const resetBtn = document.getElementById('reset-btn');
    
    // UI Elements for updates
    const statusText = document.getElementById('status-text');
    const verdictText = document.getElementById('verdict-text');
    const confidenceScore = document.getElementById('confidence-score');
    const explanationText = document.getElementById('explanation-text');

    // === Event Listeners ===
    
    // Click to upload
    uploadBox.addEventListener('click', () => fileInput.click());

    // Drag & Drop effects
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadBox.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadBox.addEventListener(eventName, () => uploadBox.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadBox.addEventListener(eventName, () => uploadBox.classList.remove('dragover'), false);
    });

    // Handle File Drop
    uploadBox.addEventListener('drop', handleDrop, false);
    
    // Handle File Select
    fileInput.addEventListener('change', handleFiles, false);

    // Reset
    resetBtn.addEventListener('click', resetUI);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles({ target: { files: files } });
    }

    function handleFiles(e) {
        const file = e.target.files[0];
        if (file) {
            validateAndProcess(file);
        }
    }

    // === Logic ===

    function validateAndProcess(file) {
        // Max 4MB size check (Render limit safety)
        if (file.size > 4 * 1024 * 1024) {
            alert('File too large. Please upload an audio file smaller than 4MB.');
            return;
        }

        // Switch UI to processing state
        uploadArea.classList.add('hidden');
        processingArea.classList.remove('hidden');
        
        // Simulating different statuses for UX
        const stages = [
            "Analyzing Waveform Structure...",
            " extracting MFCC & Spectral Features...",
            "Running Neural Inference...",
            "Calibrating Confidence Score..."
        ];
        
        let step = 0;
        const statusInterval = setInterval(() => {
            if(step < stages.length) {
                statusText.innerText = stages[step];
                step++;
            }
        }, 800);

        // Process File
        const reader = new FileReader();
        reader.onload = function(e) {
            const base64Audio = e.target.result.split(',')[1];
            sendToAPI(base64Audio, file.name);
            clearInterval(statusInterval);
        };
        reader.onerror = function() {
            clearInterval(statusInterval);
            showError("Failed to read file");
        };
        reader.readAsDataURL(file);
    }

    async function sendToAPI(base64Audio, filename) {
        try {
            const response = await fetch('/detect-voice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': 'demo-key' // Hardcoded for demo/hackathon convenience
                },
                body: JSON.stringify({
                    audioBase64: base64Audio,
                    language: 'en',
                    audioFormat: 'wav' // API auto-detects, but sending generic 'wav' is fine
                })
            });

            if (!response.ok) {
                throw new Error(`Server Error: ${response.status}`);
            }

            const data = await response.json();
            showResult(data);

        } catch (error) {
            console.error(error);
            showError("Analysis Failed. Server might be busy.");
        }
    }

    function showResult(data) {
        processingArea.classList.add('hidden');
        resultArea.classList.remove('hidden');

        // Reset classes
        resultCard.classList.remove('real', 'fake', 'error');

        // Apply Logic
        const isReal = data.classification.toLowerCase() === 'real';
        resultCard.classList.add(isReal ? 'real' : 'fake');

        verdictText.innerText = isReal ? "GENUINE HUMAN AUDIO" : "DEEPFAKE DETECTED";
        
        // Format confidence: 0.9823 -> 98.2%
        const confPercent = (data.confidence * 100).toFixed(1);
        confidenceScore.innerText = `${confPercent}% CONFIDENCE`;

        explanationText.innerText = data.explanation;
    }

    function showError(msg) {
        processingArea.classList.add('hidden');
        resultArea.classList.remove('hidden');
        resultCard.classList.remove('real', 'fake');
        resultCard.classList.add('error');
        
        verdictText.innerText = "ERROR";
        confidenceScore.innerText = "";
        explanationText.innerText = msg;
    }

    function resetUI() {
        resultArea.classList.add('hidden');
        uploadArea.classList.remove('hidden');
        fileInput.value = ''; // Reset input
    }
});
