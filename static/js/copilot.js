// AyurCare Copilot Client Script

let selectedImageFile = null;
let speechRecognition = null;
let isRecognizing = false;

// Language code mapper for Web Speech API
const langCodeMap = {
    'Hindi': 'hi-IN',
    'English': 'en-US',
    'Telugu': 'te-IN',
    'Tamil': 'ta-IN',
    'Marathi': 'mr-IN',
    'Bengali': 'bn-IN',
    'Kannada': 'kn-IN',
    'Malayalam': 'ml-IN',
    'Gujarati': 'gu-IN',
    'Spanish': 'es-ES',
    'French': 'fr-FR'
};

function quickSelectSymptom(text) {
    const promptInput = document.getElementById('prompt-input');
    if (promptInput) {
        promptInput.value = text;
        promptInput.focus();
    }
}

function handleImageSelection(event) {
    const file = event.target.files[0];
    if (file) {
        selectedImageFile = file;
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewEl = document.getElementById('image-preview-element');
            const container = document.getElementById('image-preview-container');
            previewEl.src = e.target.result;
            container.classList.remove('d-none');
        };
        reader.readAsDataURL(file);
    }
}

function clearSelectedImage() {
    selectedImageFile = null;
    document.getElementById('image-input').value = '';
    const container = document.getElementById('image-preview-container');
    container.classList.add('d-none');
    document.getElementById('image-preview-element').src = '';
}

function toggleVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Speech Recognition is not supported by your browser. Please type your symptoms.");
        return;
    }

    if (isRecognizing) {
        if (speechRecognition) speechRecognition.stop();
        return;
    }

    const currentLang = document.getElementById('consult-language').value;
    const langCode = langCodeMap[currentLang] || 'en-US';

    speechRecognition = new SpeechRecognition();
    speechRecognition.lang = langCode;
    speechRecognition.interimResults = false;
    speechRecognition.maxAlternatives = 1;

    const micBtn = document.getElementById('btn-mic');
    const speechStatus = document.getElementById('speech-status');

    speechRecognition.onstart = function() {
        isRecognizing = true;
        micBtn.classList.add('btn-danger', 'text-white');
        micBtn.classList.remove('btn-outline-secondary');
        speechStatus.classList.remove('d-none');
    };

    speechRecognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        const promptInput = document.getElementById('prompt-input');
        promptInput.value = (promptInput.value ? promptInput.value + " " : "") + transcript;
    };

    speechRecognition.onerror = function(event) {
        console.warn("Speech recognition error:", event.error);
    };

    speechRecognition.onend = function() {
        isRecognizing = false;
        micBtn.classList.remove('btn-danger', 'text-white');
        micBtn.classList.add('btn-outline-secondary');
        speechStatus.classList.add('d-none');
    };

    speechRecognition.start();
}

// Text to speech (TTS)
function speakText(text, langName) {
    if (!('speechSynthesis' in window)) {
        alert("Text-to-Speech is not supported by your browser.");
        return;
    }

    window.speechSynthesis.cancel(); // Stop any ongoing speech
    
    // Strip markdown formatting symbols for clean speech
    const cleanText = text.replace(/[#*_`>\-]/g, ' ').replace(/\n+/g, '. ');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    const langCode = langCodeMap[langName] || 'en-US';
    utterance.lang = langCode;
    utterance.rate = 0.95; // Clear natural pace

    window.speechSynthesis.speak(utterance);
}

// Append message to chat container
function appendChatMessage(role, content, extra = {}) {
    const container = document.getElementById('chat-messages-container');
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${role}`;

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    if (role === 'user') {
        let userHtml = `<div>${content}</div>`;
        if (extra.imageSrc) {
            userHtml = `<div class="mb-2"><img src="${extra.imageSrc}" style="max-height: 180px; max-width: 100%; border-radius: 8px; border: 2px solid #ffffff;"></div>` + userHtml;
        }
        bubble.innerHTML = userHtml;
    } else {
        // Parse Markdown with Marked
        const parsedHtml = (typeof marked !== 'undefined') ? marked.parse(content) : content;
        
        let headerHtml = `
            <div class="d-flex flex-wrap align-items-center justify-content-between mb-2 pb-2 border-bottom">
                <div>
                    <span class="badge bg-success me-1">🌿 ${extra.condition || 'Ayurvedic Guidance'}</span>
                    <span class="badge bg-light text-dark border small">${extra.language || 'English'}</span>
                </div>
                <div class="d-flex gap-1 mt-1 mt-sm-0">
                    <button class="btn btn-sm btn-outline-success py-0 px-2 rounded-pill small" onclick="speakText(\`${escapeHtml(content)}\`, '${extra.language || 'English'}')">
                        <i class="fa-solid fa-volume-high me-1"></i> Listen
                    </button>
                    <button class="btn btn-sm btn-outline-secondary py-0 px-2 rounded-pill small" onclick="copyToClipboard(\`${escapeHtml(content)}\`)">
                        <i class="fa-regular fa-copy me-1"></i> Copy
                    </button>
                </div>
            </div>
        `;

        let sourcesHtml = '';
        if (extra.rag_sources && extra.rag_sources.length > 0) {
            sourcesHtml = `
                <div class="p-2 bg-light rounded-3 mt-3 border small">
                    <div class="fw-bold text-success mb-1" style="font-size: 0.8rem;">
                        <i class="fa-solid fa-book-medical me-1"></i> RAG Grounded References:
                    </div>
                    <div class="d-flex flex-wrap gap-1">
                        ${extra.rag_sources.map(s => `<span class="badge bg-white text-secondary border">${s.condition_name} (${s.ayurvedic_name || ''})</span>`).join('')}
                    </div>
                </div>
            `;
        }

        bubble.innerHTML = headerHtml + `<div>${parsedHtml}</div>` + sourcesHtml;
    }

    msgDiv.appendChild(bubble);
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/`/g, '\\`').replace(/\$/g, '\\$');
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert("Remedies copied to clipboard!");
    });
}

function clearChat() {
    const container = document.getElementById('chat-messages-container');
    container.innerHTML = `
        <div class="chat-message bot">
            <div class="chat-bubble">
                <span class="badge bg-success me-2">Session Reset</span>
                <p class="mb-0 mt-2">Ready for your new health query. Please describe your symptoms or upload an image.</p>
            </div>
        </div>
    `;
    clearSelectedImage();
}

// Handle submit
function handleConsultationSubmit(event) {
    event.preventDefault();
    const promptInput = document.getElementById('prompt-input');
    const promptText = promptInput.value.trim();
    const langSelect = document.getElementById('consult-language');
    const language = langSelect.value;

    if (!promptText && !selectedImageFile) {
        alert("Please enter a symptom description or attach an image.");
        return;
    }

    // Display user message in chat
    let userImgSrc = null;
    if (selectedImageFile) {
        const previewEl = document.getElementById('image-preview-element');
        userImgSrc = previewEl.src;
    }
    appendChatMessage('user', promptText || "Health Image Diagnosis", { imageSrc: userImgSrc });

    // Prepare FormData
    const formData = new FormData();
    formData.append('prompt', promptText);
    formData.append('language', language);
    if (selectedImageFile) {
        formData.append('image', selectedImageFile);
    }

    // Clear inputs and show spinner
    promptInput.value = '';
    const cachedImage = selectedImageFile;
    clearSelectedImage();

    const submitBtn = document.getElementById('btn-submit-consult');
    const spinner = document.getElementById('submit-btn-spinner');
    const btnText = document.getElementById('submit-btn-text');
    submitBtn.disabled = true;
    spinner.classList.remove('d-none');
    btnText.classList.add('d-none');

    // Loading placeholder bubble
    const container = document.getElementById('chat-messages-container');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-message bot loading-placeholder';
    loadingDiv.innerHTML = `
        <div class="chat-bubble">
            <div class="d-flex align-items-center text-success">
                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                <span>Analyzing symptoms with Gemini 3.8 Flash & Grounding RAG Knowledge...</span>
            </div>
        </div>
    `;
    container.appendChild(loadingDiv);
    container.scrollTop = container.scrollHeight;

    // Send API Request
    fetch('/api/copilot/consult', {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        // Remove loading placeholder
        loadingDiv.remove();

        if (data.status === 'success') {
            appendChatMessage('bot', data.response, {
                condition: data.condition,
                language: data.language,
                rag_sources: data.rag_sources
            });
        } else {
            appendChatMessage('bot', `⚠️ Error: ${data.error || 'Failed to process consultation.'}`);
        }
    })
    .catch(err => {
        loadingDiv.remove();
        console.error(err);
        appendChatMessage('bot', `⚠️ Network error: Could not reach AyurCare service. Please check your internet connection.`);
    })
    .finally(() => {
        submitBtn.disabled = false;
        spinner.classList.add('d-none');
        btnText.classList.remove('d-none');
    });
}
