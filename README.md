# Personalized-Helathcare

> **A user-friendly platform where users get authentic Ayurvedic suggestions in their native language from minor health issues to critical emergency situations.**

Powered by **Google Gemini 3.8 Flash**, featuring a multimodal **RAG (Retrieval-Augmented Generation)** framework, multilingual step-by-step natural curing guidance, and a real-time **Leaflet.js Emergency SOS radar** with an intelligent 3-tier cascading dispatch engine.

---

## 🌟 Key Features

### 1. Step-by-Step Ayurvedic Guidance (Powered by Gemini 3.8 Flash)
- **Natural Curing Techniques**: For conditions such as **Fever (Jwara)**, **Common Cold & Cough (Kasa)**, **Indigestion & Acidity (Ajirna & Amlapitta)**, **Joint Pain & Arthritis (Sandhivata)**, **Stress & Insomnia (Anidra)**, **Skin Rashes (Kandu)**, and more.
- **Structured Protocols**:
  1. Condition Overview & Dosha Analysis (*Vata, Pitta, Kapha*)
  2. Step-by-Step Remedies (exact preparation, decoctions/churna, dosage, timing)
  3. Pathya & Apathya Diet (foods to consume vs. foods to avoid)
  4. Yoga, Pranayama & Lifestyle Practices
  5. Critical Hospital Red-Flag Warnings

### 2. Multilingual Support
- Respects the user's preferred language configured at registration or dynamically selected:
  - **हिन्दी (Hindi)**, **తెలుగు (Telugu)**, **தமிழ் (Tamil)**, **मराठी (Marathi)**, **বাংলা (Bengali)**, **ಕನ್ನಡ (Kannada)**, **മലയാളം (Malayalam)**, **ગુજરાતી (Gujarati)**, **English**, **Español**, **Français**.
- Includes **Web Speech API** integration:
  - **Voice Input (STT)**: Speak symptoms directly in your native tongue.
  - **Voice Output (TTS)**: Listen to remedies read aloud.

### 3. Multimodal RAG Framework
- **Dual Input Modes**: Users can describe symptoms via text OR upload images (medicinal herb, tongue coating, skin rash, thermometer reading, lab report).
- **Vision Extraction**: Gemini 3.8 Flash multimodal inspects image features, extracts clinical observations, and queries the RAG vector store.
- **Semantic Grounding**: Embeddings generated via `gemini-embedding-001` (3,072 dimensions) with cosine similarity matching against classical texts (*Charaka Samhita*, *Sushruta Samhita*) and registered doctor contributions.

### 4. Smart Emergency SOS & Leaflet.js Radar
- **Live Location Tracking**: Uses browser GPS permission (`navigator.geolocation`) and displays user coordinates on a live **Leaflet.js** map with OpenStreetMap tiles.
- **Sudden Action & Fall Detection**: Listens to device motion sensors (`devicemotion`) to detect sudden acceleration spikes, impacts, or manual distress clicks.
- **Custom Response Timeout**: Users configure an emergency time range (e.g. 15s, 30s, 60s) during registration.
- **Interactive Alarm Modal**: Audio siren and countdown timer. If user does not press *"I Am Safe"* before the timer expires, the SOS auto-dispatches.
- **3-Tier Cascading Dispatch**:
  - **Priority 1**: Nearest **Hospital** (scanned via Overpass / Maps API).
  - **Priority 2**: Nearest **Police Station** (if no hospital is reachable).
  - **Priority 3**: Nearest **Registered / Retired Doctor** on the AyurCare platform.
  - **Emergency Contact**: Immediate notification dispatched with live coordinates and a **Gemini AI Responder Triage Briefing**.

### 5. Doctor Portal & RAG Expansion
- **Doctor Registration Option**: Radio button during registration (`Are you a Doctor / Retired Doctor? -> Yes / No`).
- **Retired Doctor Volunteers**: Option for retired physicians to volunteer for Priority-3 emergency calls.
- **RAG Knowledge Contribution**: Registered doctors can submit clinical formulations, which immediately augment the AI Copilot's RAG retrieval pool.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.14 / 3.15)
- Active Internet connection for Gemini API & OpenStreetMap tiles

### Environment Setup (`.env`)
Store your Gemini API key in a `.env` file (never commit secrets to GitHub):
```env
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=ayur-care-healthcare-copilot-secret-key-2026-secure
FLASK_ENV=development
PORT=5050
```

### Running the Application
```bash
python app.py
```
Open your browser and navigate to:
👉 **[http://127.0.0.1:5050](http://127.0.0.1:5050)**

---

## 🧪 Demo Accounts for Testing

| Role | Email | Password | Features to Test |
|------|-------|----------|------------------|
| **Retired Doctor** | `dr.rajesh@ayurcare.org` | `doctor123` | Doctor Portal, Emergency SOS responder view, Add RAG formulations |
| **BAMS Physician** | `dr.vikram@ayurcare.org` | `doctor123` | Doctor Portal, Clinical wisdom contributor |
| **New Patient** | Register on `/register` | Custom | Language choice (Hindi/Telugu/English), SOS timeout setting, AI Copilot, Image diagnosis, Leaflet map |

---

## 📂 Project Architecture

```
personalized healthcare/
├── .env                          # Secure GEMINI_API_KEY & SECRET_KEY
├── .gitignore                    # Git safeguards for credentials & databases
├── app.py                        # Flask server, authentication & REST APIs
├── config.py                     # Configuration & environment variables
├── database.py                   # SQLite persistence & sample seed data
├── gemini_service.py             # Gemini 3.8 Flash & Gemini Embedding APIs
├── rag_engine.py                 # Hybrid vector + keyword RAG engine
├── emergency_service.py          # Cascading SOS (Hospital -> Police -> Doctor)
├── test_app.py                   # End-to-end integration test suite
├── data/
│   ├── ayurveda_knowledge.json   # Classical Ayurvedic treatments & formulas
│   └── embeddings_cache.json     # Cached vector embeddings
├── static/
│   ├── css/style.css             # Healthcare UI styling & animations
│   ├── js/main.js                # Global motion sensor, audio alarm & modal
│   ├── js/copilot.js             # Chat, image preview, Web Speech STT/TTS
│   └── js/sos.js                 # Leaflet.js map, geolocation & radar pins
└── templates/
    ├── base.html                 # Navigation, emergency modal & layouts
    ├── index.html                # Hero landing & feature presentation
    ├── login.html                # Login view with demo account shortcuts
    ├── register.html             # Register view with language & doctor radio
    ├── copilot.html              # AI Copilot chat & multimodal diagnosis
    ├── sos.html                  # Leaflet.js live map & cascading radar
    ├── doctor_dashboard.html     # Doctor portal & RAG contributor form
    └── profile.html              # Health profile & emergency timeout settings
```
