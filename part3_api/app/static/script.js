document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('upload-area');

    const processingArea = document.getElementById('processing-area');
    const resultArea = document.getElementById('result-area');
    const resultCard = document.getElementById('result-card');
    const resetBtn = document.getElementById('reset-btn');
    const base64Input = document.getElementById('base64-input');
    const languageSelect = document.getElementById('language-select');
    const analyzeBtn = document.getElementById('analyze-btn');

    // UI Elements for updates
    const statusText = document.getElementById('status-text');
    const verdictText = document.getElementById('verdict-text');
    const confidenceScore = document.getElementById('confidence-score');
    const explanationText = document.getElementById('explanation-text');

    // === Event Listeners ===
    analyzeBtn.addEventListener('click', handleAnalyze);
    resetBtn.addEventListener('click', resetUI);

    // === Logic ===

    function handleAnalyze() {
        const rawInput = base64Input.value.trim();

        if (!rawInput) {
            alert('Please paste a Base64 string or JSON object first.');
            return;
        }

        let finalBase64 = rawInput;
        let finalLanguage = languageSelect.value;
        let finalFormat = "mp3";

        // 1. Smart Parse: Try to see if it's JSON
        try {
            if (rawInput.startsWith('{') && rawInput.endsWith('}')) {
                const parsed = JSON.parse(rawInput);

                if (parsed.audioBase64) finalBase64 = parsed.audioBase64;
                if (parsed.language) finalLanguage = parsed.language;
                if (parsed.audioFormat) finalFormat = parsed.audioFormat;

                // Auto-update UI to reflect what was parsed (optional, but nice)
                languageSelect.value = finalLanguage;
            }
        } catch (e) {
            // Not JSON, treat as raw base64 string
            console.log("Input is not JSON, treating as raw Base64");
        }

        // Switch UI to processing state
        uploadArea.classList.add('hidden');
        processingArea.classList.remove('hidden');

        // Simulating different statuses for UX
        const stages = [
            `Analyzing ${finalLanguage} Audio...`,
            "Extracting Spectral Features...",
            "Running Neural Inference...",
            "Calibrating Confidence Score..."
        ];

        let step = 0;
        const statusInterval = setInterval(() => {
            if (step < stages.length) {
                statusText.innerText = stages[step];
                step++;
            }
        }, 800);

        // Prep data
        let cleanBase64 = finalBase64;
        if (cleanBase64.includes('base64,')) {
            cleanBase64 = cleanBase64.split('base64,')[1];
        }

        // Process directly
        setTimeout(() => {
            sendToAPI(cleanBase64, finalLanguage, finalFormat);
            clearInterval(statusInterval);
        }, 500);
    }

    async function sendToAPI(base64Audio, language, format) {
        try {
            const response = await fetch('/detect-voice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': 'demo-key'
                },
                body: JSON.stringify({
                    audioBase64: base64Audio,
                    language: language,
                    audioFormat: format
                })
            });

            if (!response.ok) {
                let errorMsg = `Server Error: ${response.status}`;
                try {
                    const errorData = await response.json();
                    // New Error Format: {"status": "error", "message": "..."}
                    if (errorData.message) errorMsg = errorData.message;
                    else if (errorData.detail) errorMsg = errorData.detail; // Fallback
                } catch (e) {
                    // Ignore JSON parse error if body is empty
                }
                throw new Error(errorMsg);
            }

            const data = await response.json();

            if (data.status === 'error') {
                throw new Error(data.message);
            }

            showResult(data);

        } catch (error) {
            console.error(error);
            showError(error.message || "Analysis Failed. Server might be busy.");
        }
    }

    function showResult(data) {
        processingArea.classList.add('hidden');
        resultArea.classList.remove('hidden');

        // Reset classes
        resultCard.classList.remove('real', 'fake', 'error');

        // Apply Logic
        // New Classification: "HUMAN" vs "AI_GENERATED"
        const isReal = data.classification === 'HUMAN';
        resultCard.classList.add(isReal ? 'real' : 'fake');

        verdictText.innerText = isReal ? "GENUINE HUMAN AUDIO" : "DEEPFAKE DETECTED";

        // Format confidence: 0.9823 -> 98.2%
        // New Field: confidenceScore
        const confPercent = (data.confidenceScore * 100).toFixed(1);
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
        base64Input.value = ''; // Reset input
    }
});
