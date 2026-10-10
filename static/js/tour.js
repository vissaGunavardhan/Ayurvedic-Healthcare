// AyurCare Interactive Guided Onboarding Tour Controller

(function() {
    let currentStepIndex = 0;
    let tourActive = false;
    let speechEnabled = true;

    // Tour Steps Definition mapped to live DOM element selectors
    const tourSteps = [
        {
            selector: '.navbar-brand',
            title: '🌿 Welcome to AyurCare Copilot!',
            description: 'Your personal AI Ayurvedic Healthcare Copilot & Emergency SOS network. If you are new or not sure what to do, this quick 1-minute interactive tour will guide you through each tool!',
            position: 'bottom'
        },
        {
            selector: '#consult-language',
            fallbackSelector: '#nav-user-lang',
            title: '🌍 1. Choose Your Comfortable Language',
            description: 'You can switch between 10+ languages anytime: Hindi (हिन्दी), Telugu (తెలుగు), Tamil (தமிழ்), Marathi (मराठी), Bengali, English, etc. All step-by-step cures and audio voices adapt to your selection.',
            position: 'bottom'
        },
        {
            selector: '#prompt-input',
            title: '💬 2. Type Your Symptoms Here',
            description: 'Type any symptoms in plain words (e.g., "I have fever and chills", "dry cough", "stomach pain"). No complicated medical terms needed!',
            position: 'top'
        },
        {
            selector: '#btn-mic',
            title: '🎙️ 3. Speak in Your Own Voice',
            description: 'Can\'t type? Tap this microphone button and speak your symptoms directly into your phone or laptop in your chosen native language!',
            position: 'top'
        },
        {
            selector: 'button[title*="Upload Image"]',
            title: '📷 4. Camera & Image Diagnosis (Vision RAG)',
            description: 'Have a medicinal leaf/herb, skin rash, tongue symptom, thermometer reading, or prescription? Click here to upload a photo. Gemini AI will inspect the image and find natural cures!',
            position: 'top'
        },
        {
            selector: '.symptom-chip',
            title: '⚡ 5. One-Click Quick Conditions',
            description: 'Tap any of these popular tags (High Fever, Cold & Cough, Acidity, Joint Pain, Stress) for instant step-by-step Ayurvedic guidance.',
            position: 'top'
        },
        {
            selector: 'a[href*="sos"]',
            title: '🚨 6. Emergency SOS Radar (Leaflet.js)',
            description: 'Need urgent help? This radar tracks your live location and detects sudden falls. If you don\'t respond within your set time, it auto-alerts Nearest Hospital → Police Station → Registered Retired Doctors!',
            position: 'bottom'
        },
        {
            selector: null, // Modal / Center final settings step
            title: '⚙️ 7. Language Settings & You Are Ready!',
            description: 'Select your preferred language right now below and click "Save & Finish" to start your first Ayurvedic consultation.',
            position: 'center',
            isSettingsStep: true
        }
    ];

    // Create DOM elements for tour
    function createTourElements() {
        if (document.getElementById('tour-backdrop')) return;

        // Backdrop
        const backdrop = document.createElement('div');
        backdrop.id = 'tour-backdrop';
        backdrop.className = 'tour-backdrop-overlay';
        backdrop.onclick = (e) => {
            // click outside to skip optionally
        };
        document.body.appendChild(backdrop);

        // Spotlight cut-out box
        const spotlight = document.createElement('div');
        spotlight.id = 'tour-spotlight';
        spotlight.className = 'tour-spotlight-box';
        spotlight.style.display = 'none';
        document.body.appendChild(spotlight);

        // Popover Card
        const popover = document.createElement('div');
        popover.id = 'tour-popover';
        popover.className = 'tour-popover-card';
        document.body.appendChild(popover);
    }

    // Position spotlight and popover relative to DOM target
    function updateTourStepUI() {
        const step = tourSteps[currentStepIndex];
        const spotlight = document.getElementById('tour-spotlight');
        const popover = document.getElementById('tour-popover');
        const backdrop = document.getElementById('tour-backdrop');

        backdrop.classList.add('active');

        let targetEl = null;
        if (step.selector) {
            targetEl = document.querySelector(step.selector);
        }
        if (!targetEl && step.fallbackSelector) {
            targetEl = document.querySelector(step.fallbackSelector);
        }

        // Voice read out the step
        if (speechEnabled && 'speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const speechText = `${step.title}. ${step.description}`;
            const utt = new SpeechSynthesisUtterance(speechText);
            utt.rate = 1.0;
            window.speechSynthesis.speak(utt);
        }

        if (targetEl && !step.isSettingsStep) {
            targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            setTimeout(() => {
                const rect = targetEl.getBoundingClientRect();
                const padding = 8;

                spotlight.style.display = 'block';
                spotlight.style.top = `${rect.top - padding}px`;
                spotlight.style.left = `${rect.left - padding}px`;
                spotlight.style.width = `${rect.width + padding * 2}px`;
                spotlight.style.height = `${rect.height + padding * 2}px`;

                // Calculate Popover Position
                let popTop = 0;
                let popLeft = 0;

                const popWidth = 360;
                const popHeight = 240;

                if (step.position === 'bottom') {
                    popTop = rect.bottom + 16;
                    popLeft = Math.max(16, Math.min(window.innerWidth - popWidth - 16, rect.left + rect.width / 2 - popWidth / 2));
                    if (popTop + popHeight > window.innerHeight) {
                        popTop = Math.max(16, rect.top - popHeight - 16);
                    }
                } else {
                    popTop = Math.max(16, rect.top - popHeight - 16);
                    popLeft = Math.max(16, Math.min(window.innerWidth - popWidth - 16, rect.left + rect.width / 2 - popWidth / 2));
                    if (popTop < 16) {
                        popTop = rect.bottom + 16;
                    }
                }

                popover.style.top = `${popTop}px`;
                popover.style.left = `${popLeft}px`;
                renderPopoverContent(step);
            }, 300);

        } else {
            // Center position for final settings step
            spotlight.style.display = 'none';
            const popWidth = 380;
            popover.style.top = '50%';
            popover.style.left = '50%';
            popover.style.transform = 'translate(-50%, -50%)';
            renderPopoverContent(step, true);
        }
    }

    // Render HTML content inside popover
    function renderPopoverContent(step, isCenter = false) {
        const popover = document.getElementById('tour-popover');
        
        let settingsHtml = '';
        if (step.isSettingsStep) {
            const currentLang = (window.CURRENT_USER && window.CURRENT_USER.language) ? window.CURRENT_USER.language : 'Hindi';
            settingsHtml = `
                <div class="p-3 bg-light rounded-3 border mb-3">
                    <label class="form-label fw-bold small text-success mb-1">
                        <i class="fa-solid fa-language me-1"></i> Choose Your Language:
                    </label>
                    <select id="tour-lang-select" class="form-select form-select-sm mb-2" onchange="window.tourChangeLanguage(this.value)">
                        <option value="Hindi" ${currentLang === 'Hindi' ? 'selected' : ''}>हिन्दी (Hindi)</option>
                        <option value="English" ${currentLang === 'English' ? 'selected' : ''}>English</option>
                        <option value="Telugu" ${currentLang === 'Telugu' ? 'selected' : ''}>తెలుగు (Telugu)</option>
                        <option value="Tamil" ${currentLang === 'Tamil' ? 'selected' : ''}>தமிழ் (Tamil)</option>
                        <option value="Marathi" ${currentLang === 'Marathi' ? 'selected' : ''}>मराठी (Marathi)</option>
                        <option value="Bengali" ${currentLang === 'Bengali' ? 'selected' : ''}>বাংলা (Bengali)</option>
                        <option value="Kannada" ${currentLang === 'Kannada' ? 'selected' : ''}>ಕನ್ನಡ (Kannada)</option>
                        <option value="Malayalam" ${currentLang === 'Malayalam' ? 'selected' : ''}>മലയാളം (Malayalam)</option>
                        <option value="Gujarati" ${currentLang === 'Gujarati' ? 'selected' : ''}>ગુજરાતી (Gujarati)</option>
                    </select>
                    <small class="text-muted d-block" style="font-size: 0.76rem;">All Ayurvedic advice and voice reading will appear in this language.</small>
                </div>
            `;
        }

        // Progress dots
        let dotsHtml = '';
        for (let i = 0; i < tourSteps.length; i++) {
            dotsHtml += `<div class="tour-dot ${i === currentStepIndex ? 'active' : ''}"></div>`;
        }

        popover.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="tour-badge-step">Step ${currentStepIndex + 1} of ${tourSteps.length}</span>
                <button type="button" class="btn-close btn-sm" onclick="window.endAyurCareTour()" title="Skip Tour"></button>
            </div>
            
            <div class="tour-title">${step.title}</div>
            <div class="tour-description">${step.description}</div>
            
            ${settingsHtml}

            <div class="tour-footer">
                <div class="tour-progress-dots">
                    ${dotsHtml}
                </div>
                
                <div class="d-flex gap-2">
                    ${currentStepIndex > 0 ? `
                        <button type="button" class="btn btn-sm btn-outline-secondary rounded-pill px-3" onclick="window.prevAyurCareStep()">
                            <i class="fa-solid fa-chevron-left me-1"></i> Back
                        </button>
                    ` : `
                        <button type="button" class="btn btn-sm btn-outline-secondary rounded-pill px-3" onclick="window.endAyurCareTour()">
                            Skip
                        </button>
                    `}
                    
                    ${currentStepIndex < tourSteps.length - 1 ? `
                        <button type="button" class="btn btn-sm btn-success rounded-pill px-3 fw-bold shadow-sm" onclick="window.nextAyurCareStep()">
                            Next <i class="fa-solid fa-chevron-right ms-1"></i>
                        </button>
                    ` : `
                        <button type="button" class="btn btn-sm btn-success rounded-pill px-4 fw-bold shadow-sm" onclick="window.endAyurCareTour(true)">
                            <i class="fa-solid fa-check-circle me-1"></i> Save & Finish
                        </button>
                    `}
                </div>
            </div>
        `;

        popover.classList.add('active');
    }

    // Navigation methods exposed on window
    window.startAyurCareTour = function() {
        createTourElements();
        currentStepIndex = 0;
        tourActive = true;
        updateTourStepUI();
    };

    window.nextAyurCareStep = function() {
        if (currentStepIndex < tourSteps.length - 1) {
            currentStepIndex++;
            updateTourStepUI();
        } else {
            window.endAyurCareTour(true);
        }
    };

    window.prevAyurCareStep = function() {
        if (currentStepIndex > 0) {
            currentStepIndex--;
            updateTourStepUI();
        }
    };

    window.endAyurCareTour = function(completed = false) {
        tourActive = false;
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();

        const backdrop = document.getElementById('tour-backdrop');
        const spotlight = document.getElementById('tour-spotlight');
        const popover = document.getElementById('tour-popover');

        if (backdrop) backdrop.classList.remove('active');
        if (popover) popover.classList.remove('active');
        if (spotlight) spotlight.style.display = 'none';

        if (completed) {
            localStorage.setItem('ayurcare_tour_completed', 'true');
        }
    };

    window.tourChangeLanguage = function(newLang) {
        const langDropdown = document.getElementById('consult-language');
        if (langDropdown) {
            langDropdown.value = newLang;
        }
        const navLang = document.getElementById('nav-user-lang');
        if (navLang) {
            navLang.innerText = newLang;
        }
        if (window.CURRENT_USER) {
            window.CURRENT_USER.language = newLang;
        }
    };

    // Auto-prompt on first visit or setup trigger
    document.addEventListener('DOMContentLoaded', () => {
        // Add Floating Tour Button to the bottom right of the page
        const floatingBtn = document.createElement('button');
        floatingBtn.className = 'floating-tour-btn';
        floatingBtn.innerHTML = `
            <span class="floating-tour-beacon"></span>
            <i class="fa-solid fa-compass fa-spin" style="--fa-animation-duration: 15s;"></i>
            <span>Interactive Tour / Guide</span>
        `;
        floatingBtn.title = "New here? Click for an interactive guide explaining every tool!";
        floatingBtn.onclick = () => window.startAyurCareTour();
        document.body.appendChild(floatingBtn);

        // If tour never taken, show auto-start prompt after 1.5 seconds
        if (!localStorage.getItem('ayurcare_tour_completed')) {
            setTimeout(() => {
                const startConfirm = confirm("Namaste! Welcome to AyurCare Healthcare Copilot.\n\nWould you like a quick interactive step-by-step tour explaining all the tools (Language, Symptoms, Camera, Voice, and SOS)?");
                if (startConfirm) {
                    window.startAyurCareTour();
                } else {
                    localStorage.setItem('ayurcare_tour_completed', 'true');
                }
            }, 1200);
        }
    });

    // Handle screen resize
    window.addEventListener('resize', () => {
        if (tourActive) {
            updateTourStepUI();
        }
    });
})();
