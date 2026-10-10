// AyurCare Global Client Controller

let globalAlertId = null;
let globalCountdownInterval = null;
let currentCoords = { lat: 17.3850, lng: 78.4867 }; // Default coords
let isEmergencyActive = false;

// Request browser geolocation
function initializeUserGeolocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                currentCoords.lat = pos.coords.latitude;
                currentCoords.lng = pos.coords.longitude;
                console.log("Live GPS locked:", currentCoords);
            },
            (err) => {
                console.warn("Geolocation permission note:", err.message);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }
}

// Play alert tone
function playEmergencyAlarm() {
    const audio = document.getElementById('emergency-audio-tone');
    if (audio) {
        audio.currentTime = 0;
        audio.play().catch(e => console.log("Audio autoplay prevented by browser:", e));
    }
}

function stopEmergencyAlarm() {
    const audio = document.getElementById('emergency-audio-tone');
    if (audio) {
        audio.pause();
        audio.currentTime = 0;
    }
}

// Trigger Emergency Countdown Modal
function triggerEmergencyCountdown(reason = "Sudden movement or distress detected") {
    if (isEmergencyActive) return;
    isEmergencyActive = true;
    playEmergencyAlarm();

    const titleEl = document.getElementById('global-sos-reason-title');
    if (titleEl) titleEl.innerText = reason;

    const timeoutSeconds = (window.CURRENT_USER && window.CURRENT_USER.sos_timeout) ? window.CURRENT_USER.sos_timeout : 30;
    let remaining = timeoutSeconds;

    const countEl = document.getElementById('global-countdown-val');
    if (countEl) countEl.innerText = remaining;

    // Open Modal
    const modalEl = document.getElementById('globalEmergencyModal');
    let modalInstance = null;
    if (modalEl) {
        modalInstance = new bootstrap.Modal(modalEl);
        modalInstance.show();
    }

    // Call backend to create pending alert
    if (window.CURRENT_USER && window.CURRENT_USER.id) {
        fetch('/api/sos/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                latitude: currentCoords.lat,
                longitude: currentCoords.lng,
                trigger_type: reason.includes('motion') ? 'sudden_motion' : 'manual_sos',
                address: `GPS: ${currentCoords.lat.toFixed(4)}, ${currentCoords.lng.toFixed(4)}`
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data.alert_id) globalAlertId = data.alert_id;
        })
        .catch(err => console.error("Error creating pending alert:", err));
    }

    // Start Countdown Interval
    if (globalCountdownInterval) clearInterval(globalCountdownInterval);
    globalCountdownInterval = setInterval(() => {
        remaining -= 1;
        if (countEl) countEl.innerText = remaining;

        if (remaining <= 0) {
            clearInterval(globalCountdownInterval);
            stopEmergencyAlarm();
            executeDispatchedEmergency(reason);
        }
    }, 1000);
}

// Execute Cascading Dispatch when time range expires
function executeDispatchedEmergency(reason) {
    if (!isEmergencyActive) return;

    fetch('/api/sos/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            alert_id: globalAlertId,
            latitude: currentCoords.lat,
            longitude: currentCoords.lng,
            reason: reason
        })
    })
    .then(r => r.json())
    .then(res => {
        console.log("Cascading SOS response:", res);
        // Redirect or show dispatched notification
        if (window.location.pathname !== '/sos') {
            window.location.href = '/sos?dispatched=1';
        } else {
            const modalEl = document.getElementById('globalEmergencyModal');
            if (modalEl) {
                const modalInstance = bootstrap.Modal.getInstance(modalEl);
                if (modalInstance) modalInstance.hide();
            }
            if (window.renderDispatchResult) {
                window.renderDispatchResult(res);
            }
        }
    })
    .catch(err => console.error("Dispatch failed:", err))
    .finally(() => {
        isEmergencyActive = false;
    });
}

// Cancel Emergency
function cancelEmergency() {
    isEmergencyActive = false;
    stopEmergencyAlarm();
    if (globalCountdownInterval) clearInterval(globalCountdownInterval);

    if (globalAlertId) {
        fetch('/api/sos/cancel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ alert_id: globalAlertId })
        }).catch(e => console.error(e));
        globalAlertId = null;
    }

    const modalEl = document.getElementById('globalEmergencyModal');
    if (modalEl) {
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) modalInstance.hide();
    }
}

// Sudden Action / Device Motion Tracker
function setupMotionDetection() {
    let lastAcceleration = { x: null, y: null, z: null };
    const THRESHOLD = 25.0; // Acceleration delta threshold for sudden jerk / impact

    if (window.DeviceMotionEvent) {
        window.addEventListener('devicemotion', (e) => {
            const acc = e.accelerationIncludingGravity;
            if (!acc || acc.x === null) return;

            if (lastAcceleration.x !== null) {
                const deltaX = Math.abs(acc.x - lastAcceleration.x);
                const deltaY = Math.abs(acc.y - lastAcceleration.y);
                const deltaZ = Math.abs(acc.z - lastAcceleration.z);

                const magnitude = Math.sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
                if (magnitude > THRESHOLD && !isEmergencyActive) {
                    console.warn("Sudden high-impact motion detected!", magnitude);
                    triggerEmergencyCountdown("Sudden physical impact / fall detected");
                }
            }

            lastAcceleration = { x: acc.x, y: acc.y, z: acc.z };
        });
    }
}

// DOM Ready initialization
document.addEventListener('DOMContentLoaded', () => {
    initializeUserGeolocation();
    setupMotionDetection();

    // Button event listeners
    const btnSafe = document.getElementById('btn-global-safe');
    if (btnSafe) {
        btnSafe.addEventListener('click', cancelEmergency);
    }

    const btnDispatchNow = document.getElementById('btn-global-dispatch-now');
    if (btnDispatchNow) {
        btnDispatchNow.addEventListener('click', () => {
            stopEmergencyAlarm();
            if (globalCountdownInterval) clearInterval(globalCountdownInterval);
            executeDispatchedEmergency("Manual emergency confirmation by user");
        });
    }
});
