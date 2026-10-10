// AyurCare Leaflet SOS Radar Script

let map = null;
let userMarker = null;
let userAccuracyCircle = null;
let hospitalMarkersGroup = null;
let policeMarkersGroup = null;
let doctorMarkersGroup = null;

// Custom Icons
const hospitalIcon = L.divIcon({
    html: '<div style="background-color: #d32f2f; color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><i class="fa-solid fa-hospital" style="font-size: 16px;"></i></div>',
    className: '',
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -17]
});

const policeIcon = L.divIcon({
    html: '<div style="background-color: #1565c0; color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><i class="fa-solid fa-shield" style="font-size: 16px;"></i></div>',
    className: '',
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -17]
});

const doctorIcon = L.divIcon({
    html: '<div style="background-color: #2e7d32; color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><i class="fa-solid fa-user-doctor" style="font-size: 16px;"></i></div>',
    className: '',
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -17]
});

const userIcon = L.divIcon({
    html: '<div style="background-color: #0288d1; color: white; width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 0 15px rgba(2, 136, 209, 0.7); animation: pulse-sos 2s infinite;"><i class="fa-solid fa-person-rays" style="font-size: 18px;"></i></div>',
    className: '',
    iconSize: [38, 38],
    iconAnchor: [19, 19],
    popupAnchor: [0, -19]
});

function initMap(lat, lng) {
    if (map) return;

    map = L.map('sos-map').setView([lat, lng], 14);

    // OpenStreetMap standard tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | AyurCare SOS',
        maxZoom: 19
    }).addTo(map);

    hospitalMarkersGroup = L.layerGroup().addTo(map);
    policeMarkersGroup = L.layerGroup().addTo(map);
    doctorMarkersGroup = L.layerGroup().addTo(map);

    // Add user marker
    userMarker = L.marker([lat, lng], { icon: userIcon }).addTo(map);
    userMarker.bindPopup(`
        <div class="text-center p-2">
            <h6 class="fw-bold mb-1 text-primary"><i class="fa-solid fa-location-dot me-1"></i> You are here</h6>
            <div class="small text-muted">Live Geolocation Monitored</div>
        </div>
    `).openPopup();

    userAccuracyCircle = L.circle([lat, lng], {
        radius: 400,
        color: '#0288d1',
        fillColor: '#b3e5fc',
        fillOpacity: 0.25,
        weight: 1
    }).addTo(map);

    fetchNearbyEmergencyFacilities(lat, lng);
}

function updateCoordinates(lat, lng) {
    currentCoords.lat = lat;
    currentCoords.lng = lng;

    const coordsDisplay = document.getElementById('coordinates-display');
    if (coordsDisplay) {
        coordsDisplay.innerText = `Lat: ${lat.toFixed(4)} | Lng: ${lng.toFixed(4)}`;
    }

    if (map && userMarker) {
        userMarker.setLatLng([lat, lng]);
        if (userAccuracyCircle) userAccuracyCircle.setLatLng([lat, lng]);
        map.setView([lat, lng], 14);
        fetchNearbyEmergencyFacilities(lat, lng);
    }
}

function centerMapOnUser() {
    if (map && currentCoords) {
        map.setView([currentCoords.lat, currentCoords.lng], 15);
        if (userMarker) userMarker.openPopup();
    }
}

function requestGpsPermission() {
    const statusText = document.getElementById('gps-status-text');
    if (!navigator.geolocation) {
        if (statusText) statusText.innerText = "Geolocation is not supported by your browser. Using default city coordinates.";
        initMap(currentCoords.lat, currentCoords.lng);
        return;
    }

    if (statusText) statusText.innerText = "Requesting live GPS permission from device...";

    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;
            if (statusText) {
                statusText.innerHTML = `<span class="text-success fw-bold"><i class="fa-solid fa-circle-check me-1"></i> Live GPS Permission Granted! Accurate to ${Math.round(pos.coords.accuracy)}m.</span>`;
            }
            if (!map) {
                initMap(lat, lng);
            } else {
                updateCoordinates(lat, lng);
            }
        },
        (err) => {
            if (statusText) {
                statusText.innerHTML = `<span class="text-warning fw-bold"><i class="fa-solid fa-triangle-exclamation me-1"></i> GPS permission was denied or timed out (${err.message}). Using safe regional coordinates.</span>`;
            }
            if (!map) initMap(currentCoords.lat, currentCoords.lng);
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
}

function fetchNearbyEmergencyFacilities(lat, lng) {
    fetch(`/api/sos/nearby?lat=${lat}&lng=${lng}`)
        .then(r => r.json())
        .then(data => {
            renderMapFacilities(data);
        })
        .catch(err => console.error("Error fetching nearby facilities:", err));
}

function renderMapFacilities(data) {
    if (!map) return;

    // Clear existing layer groups
    hospitalMarkersGroup.clearLayers();
    policeMarkersGroup.clearLayers();
    doctorMarkersGroup.clearLayers();

    // Render Hospitals
    const hospitals = data.hospitals || [];
    if (hospitals.length > 0) {
        const topHospital = hospitals[0];
        document.getElementById('p1-hospital-name').innerHTML = `
            <span class="text-danger fw-bold"><i class="fa-solid fa-hospital me-1"></i> ${topHospital.name}</span><br>
            <span class="text-muted">${topHospital.distance_km} km away | 📞 ${topHospital.phone}</span>
        `;

        hospitals.forEach(h => {
            const marker = L.marker([h.lat, h.lng], { icon: hospitalIcon }).addTo(hospitalMarkersGroup);
            marker.bindPopup(`
                <div class="p-1">
                    <span class="badge bg-danger mb-1">Priority 1: Nearest Hospital</span>
                    <h6 class="fw-bold mb-1">${h.name}</h6>
                    <div class="small text-muted mb-1"><i class="fa-solid fa-location-dot me-1"></i> ${h.address}</div>
                    <div class="small fw-semibold text-danger mb-2">Distance: ${h.distance_km} km</div>
                    <a href="tel:${h.phone}" class="btn btn-sm btn-outline-danger w-100 py-1"><i class="fa-solid fa-phone me-1"></i> Call ${h.phone}</a>
                </div>
            `);
        });
    }

    // Render Police Stations
    const policeStations = data.police_stations || [];
    if (policeStations.length > 0) {
        const topPolice = policeStations[0];
        document.getElementById('p2-police-name').innerHTML = `
            <span class="text-primary fw-bold"><i class="fa-solid fa-shield me-1"></i> ${topPolice.name}</span><br>
            <span class="text-muted">${topPolice.distance_km} km away | 📞 ${topPolice.phone}</span>
        `;

        policeStations.forEach(p => {
            const marker = L.marker([p.lat, p.lng], { icon: policeIcon }).addTo(policeMarkersGroup);
            marker.bindPopup(`
                <div class="p-1">
                    <span class="badge bg-primary mb-1">Priority 2: Police Fallback</span>
                    <h6 class="fw-bold mb-1">${p.name}</h6>
                    <div class="small text-muted mb-1"><i class="fa-solid fa-location-dot me-1"></i> ${p.address}</div>
                    <div class="small fw-semibold text-primary mb-2">Distance: ${p.distance_km} km</div>
                    <a href="tel:${p.phone}" class="btn btn-sm btn-outline-primary w-100 py-1"><i class="fa-solid fa-phone me-1"></i> Call ${p.phone}</a>
                </div>
            `);
        });
    }

    // Render Registered Doctors
    const doctors = data.registered_doctors || [];
    if (doctors.length > 0) {
        const topDoctor = doctors[0];
        document.getElementById('p3-doctor-name').innerHTML = `
            <span class="text-success fw-bold"><i class="fa-solid fa-stethoscope me-1"></i> ${topDoctor.name}</span><br>
            <span class="text-muted">${topDoctor.specialization} ${topDoctor.is_retired ? '(Retired)' : ''} | 📞 ${topDoctor.phone}</span>
        `;

        doctors.forEach(d => {
            const marker = L.marker([d.lat, d.lng], { icon: doctorIcon }).addTo(doctorMarkersGroup);
            marker.bindPopup(`
                <div class="p-1">
                    <span class="badge bg-success mb-1">Priority 3: Registered Doctor Safety Net</span>
                    <h6 class="fw-bold mb-1">${d.name}</h6>
                    <div class="small text-muted mb-1"><i class="fa-solid fa-award me-1"></i> ${d.specialization}</div>
                    ${d.is_retired ? '<span class="badge bg-warning text-dark mb-1">Retired Volunteer</span><br>' : ''}
                    <div class="small fw-semibold text-success mb-2">Approx. ${d.distance_km} km</div>
                    <a href="tel:${d.phone}" class="btn btn-sm btn-outline-success w-100 py-1"><i class="fa-solid fa-phone me-1"></i> Contact ${d.phone}</a>
                </div>
            `);
        });
    }
}

// Render emergency dispatch result (after countdown or instant trigger)
window.renderDispatchResult = function(res) {
    const triageCard = document.getElementById('ai-triage-card');
    const triageText = document.getElementById('ai-triage-text');
    const triageTarget = document.getElementById('ai-triage-target');

    if (triageCard) triageCard.style.display = 'block';
    if (triageText) triageText.innerText = res.ai_briefing || "Emergency dispatch notification broadcasted to responders.";

    if (triageTarget && res.target) {
        triageTarget.innerHTML = `
            <div class="fw-bold text-danger mb-1">${res.cascade_stage}</div>
            <div><strong>Dispatched To:</strong> ${res.target.name}</div>
            <div><strong>Contact:</strong> ${res.target.phone}</div>
            <div class="mt-1 text-success fw-semibold"><i class="fa-solid fa-check-double me-1"></i> Live coordinates and patient profile transmitted.</div>
        `;
    }
};

function simulateSuddenFall() {
    triggerEmergencyCountdown("Sudden fall impact detected by motion sensor");
}

document.addEventListener('DOMContentLoaded', () => {
    requestGpsPermission();

    // Check query params if arrived from auto-dispatch
    const params = new URLSearchParams(window.location.search);
    if (params.get('dispatched')) {
        setTimeout(() => {
            executeDispatchedEmergency("Cascaded auto-dispatch from earlier session");
        }, 800);
    }
});
