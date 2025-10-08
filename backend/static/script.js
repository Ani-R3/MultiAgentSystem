document.addEventListener('DOMContentLoaded', () => {
    // Form elements
    const uploadForm = document.getElementById('uploadForm');
    const pdfFile = document.getElementById('pdfFile');
    const uploadStatus = document.getElementById('uploadStatus');
    const askForm = document.getElementById('askForm');
    const queryInput = document.getElementById('queryInput');
    
    // Result elements
    const loader = document.getElementById('loader');
    const resultContent = document.getElementById('result-content');
    const rationaleBox = document.getElementById('rationaleBox');
    const answerBox = document.getElementById('answerBox');

    // Logs elements
    const loadLogsBtn = document.getElementById('loadLogs');
    const logsBox = document.getElementById('logsBox');

    // Handle PDF Upload
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!pdfFile.files.length) {
            uploadStatus.textContent = 'Please select a file first.';
            uploadStatus.style.color = 'var(--error-color)';
            return;
        }

        const formData = new FormData();
        formData.append('file', pdfFile.files[0]);

        uploadStatus.textContent = `Uploading "${pdfFile.files[0].name}"...`;
        uploadStatus.style.color = 'var(--muted-text-color)';

        try {
            const response = await fetch('/uploadPdf', { method: 'POST', body: formData });
            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Unknown upload error');
            
            uploadStatus.textContent = data.message;
            uploadStatus.style.color = 'var(--success-color)';
        } catch (error) {
            uploadStatus.textContent = `Upload failed: ${error.message}`;
            uploadStatus.style.color = 'var(--error-color)';
        }
    });

    // Handle Ask Question
    askForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;

        // Show loader and hide previous result
        loader.style.display = 'block';
        resultContent.style.display = 'none';

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Failed to get an answer');

            rationaleBox.textContent = `Agent Used: ${data.agentUsed} | Rationale: ${data.rationale}`;
            rationaleBox.style.display = 'block';
            answerBox.textContent = data.answer;

        } catch (error) {
            rationaleBox.style.display = 'none';
            answerBox.textContent = `An error occurred: ${error.message}`;
        } finally {
            // Hide loader and show result
            loader.style.display = 'none';
            resultContent.style.display = 'block';
        }
    });

    // Handle Load Logs
    loadLogsBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/logs');
            const logData = await response.text();
            logsBox.textContent = logData;
            logsBox.style.display = 'block';
            // Scroll to the bottom of the logs
            logsBox.scrollTop = logsBox.scrollHeight;
        } catch (error) {
            logsBox.textContent = 'Failed to load logs.';
        }
    });
});