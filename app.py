import os
import json
import uuid
from functools import wraps
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for, flash, 
    session, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename

from config import Config
from database import (
    init_db, seed_sample_data, get_user_by_email, get_user_by_id, 
    create_user, update_user_profile, verify_user, save_consultation, 
    get_user_consultations, add_doctor_contribution, get_all_doctor_contributions,
    create_sos_alert, update_sos_alert, get_sos_alert, 
    get_active_sos_alerts_for_doctor, get_user_sos_history, get_registered_doctors
)
from gemini_service import GeminiService
from rag_engine import rag_engine
from emergency_service import EmergencyService

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = get_user_by_id(session['user_id'])
        if not user or not user.get('is_doctor'):
            flash('This section is reserved for verified Doctors and Medical Specialists.', 'danger')
            return redirect(url_for('copilot_view'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_current_user():
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    return {'current_user': user}

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('copilot_view'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        preferred_language = request.form.get('preferred_language', 'English')
        sos_timeout_seconds = int(request.form.get('sos_timeout_seconds', 30))
        emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
        emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()
        emergency_contact_email = request.form.get('emergency_contact_email', '').strip()
        
        # Doctor Radio Selection
        is_doctor_val = request.form.get('is_doctor', 'no')
        is_doctor = 1 if is_doctor_val == 'yes' else 0
        doctor_specialization = request.form.get('doctor_specialization', '').strip() if is_doctor else ''
        doctor_license_id = request.form.get('doctor_license_id', '').strip() if is_doctor else ''
        is_retired = 1 if request.form.get('is_retired') == '1' else 0
        doctor_clinic_city = request.form.get('doctor_clinic_city', '').strip() if is_doctor else ''

        if not name or not email or not password:
            flash('Name, email, and password are required.', 'danger')
            return render_template('register.html')
            
        existing = get_user_by_email(email)
        if existing:
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        try:
            user_id = create_user(
                name=name, email=email, password=password,
                preferred_language=preferred_language,
                sos_timeout_seconds=sos_timeout_seconds,
                emergency_contact_name=emergency_contact_name,
                emergency_contact_phone=emergency_contact_phone,
                emergency_contact_email=emergency_contact_email,
                is_doctor=is_doctor,
                doctor_specialization=doctor_specialization,
                doctor_license_id=doctor_license_id,
                is_retired=is_retired,
                doctor_clinic_city=doctor_clinic_city
            )
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_lang'] = preferred_language
            flash(f'Welcome to AyurCare, {name}! Your healthcare copilot is ready.', 'success')
            return redirect(url_for('copilot_view'))
        except Exception as e:
            flash(f'Registration error: {str(e)}', 'danger')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('copilot_view'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = verify_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_lang'] = user['preferred_language']
            flash(f'Welcome back, {user["name"]}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('copilot_view'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_user_by_id(session['user_id'])
    if request.method == 'POST':
        preferred_language = request.form.get('preferred_language', user['preferred_language'])
        sos_timeout_seconds = int(request.form.get('sos_timeout_seconds', user['sos_timeout_seconds']))
        emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
        emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()
        emergency_contact_email = request.form.get('emergency_contact_email', '').strip()
        
        is_doctor_val = request.form.get('is_doctor', 'no')
        is_doctor = 1 if is_doctor_val == 'yes' else 0
        doctor_specialization = request.form.get('doctor_specialization', '').strip()
        doctor_license_id = request.form.get('doctor_license_id', '').strip()
        is_retired = 1 if request.form.get('is_retired') == '1' else 0
        doctor_clinic_city = request.form.get('doctor_clinic_city', '').strip()

        update_user_profile(
            session['user_id'],
            preferred_language=preferred_language,
            sos_timeout_seconds=sos_timeout_seconds,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            emergency_contact_email=emergency_contact_email,
            is_doctor=is_doctor,
            doctor_specialization=doctor_specialization,
            doctor_license_id=doctor_license_id,
            is_retired=is_retired,
            doctor_clinic_city=doctor_clinic_city
        )
        session['user_lang'] = preferred_language
        flash('Profile settings updated successfully!', 'success')
        return redirect(url_for('profile'))
        
    history = get_user_consultations(session['user_id'], limit=5)
    sos_history = get_user_sos_history(session['user_id'], limit=5)
    return render_template('profile.html', user=user, history=history, sos_history=sos_history)

# ==========================================
# CORE VIEWS
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/copilot')
@login_required
def copilot_view():
    user = get_user_by_id(session['user_id'])
    history = get_user_consultations(session['user_id'], limit=10)
    return render_template('copilot.html', user=user, history=history)

@app.route('/sos')
@login_required
def sos_view():
    user = get_user_by_id(session['user_id'])
    history = get_user_sos_history(session['user_id'], limit=10)
    return render_template('sos.html', user=user, history=history)

@app.route('/doctor/dashboard')
@doctor_required
def doctor_dashboard():
    user = get_user_by_id(session['user_id'])
    active_alerts = get_active_sos_alerts_for_doctor()
    contributions = get_all_doctor_contributions()
    return render_template('doctor_dashboard.html', user=user, active_alerts=active_alerts, contributions=contributions)

# ==========================================
# COPILOT & RAG API ENDPOINTS
# ==========================================

@app.route('/api/copilot/consult', methods=['POST'])
@login_required
def api_copilot_consult():
    user = get_user_by_id(session['user_id'])
    user_lang = request.form.get('language') or user.get('preferred_language') or 'English'
    prompt_text = request.form.get('prompt', '').strip()
    
    # Process optional uploaded image
    image_file = request.files.get('image')
    image_filename = None
    image_analysis = None
    
    if image_file and image_file.filename != '':
        ext = image_file.filename.rsplit('.', 1)[-1].lower()
        if ext in Config.ALLOWED_EXTENSIONS:
            safe_name = f"{uuid.uuid4().hex}_{secure_filename(image_file.filename)}"
            file_path = Config.UPLOAD_FOLDER / safe_name
            image_file.save(file_path)
            image_filename = safe_name
            
            # Read bytes for multimodal Gemini inspection
            with open(file_path, 'rb') as f:
                img_bytes = f.read()
            mime = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"
            image_analysis = GeminiService.analyze_image_and_extract_symptoms(
                img_bytes, mime_type=mime, user_prompt=prompt_text
            )

    if not prompt_text and not image_analysis:
        return jsonify({'error': 'Please provide a health symptom description or upload an image.'}), 400

    # Determine query for RAG vector retrieval
    search_query = prompt_text
    if image_analysis and image_analysis.get('search_query'):
        search_query = f"{prompt_text} {image_analysis.get('search_query')}"

    # Execute RAG Retrieval
    retrieved_docs, doctor_insights = rag_engine.retrieve(search_query, top_k=3)
    
    detected_condition = "Holistic Ayurvedic Consultation"
    if retrieved_docs:
        detected_condition = retrieved_docs[0].get('condition_name', detected_condition)
    elif image_analysis and image_analysis.get('likely_ayurvedic_condition'):
        detected_condition = image_analysis.get('likely_ayurvedic_condition')

    # Generate step-by-step Ayurvedic suggestions via Gemini
    ai_response = GeminiService.generate_rag_remedy(
        user_prompt=prompt_text or (image_analysis.get('visual_observations') if image_analysis else 'General Consultation'),
        retrieved_docs=retrieved_docs,
        preferred_language=user_lang,
        image_analysis=image_analysis,
        doctor_insights=doctor_insights
    )

    # Save to history database
    save_consultation(
        user_id=user['id'],
        prompt_text=prompt_text,
        image_filename=image_filename,
        detected_condition=detected_condition,
        rag_sources=[d.get('condition_name') for d in retrieved_docs],
        ai_response=ai_response,
        language_used=user_lang
    )

    return jsonify({
        'status': 'success',
        'condition': detected_condition,
        'response': ai_response,
        'language': user_lang,
        'image_url': f"/uploads/{image_filename}" if image_filename else None,
        'image_analysis': image_analysis,
        'rag_sources': [
            {
                'condition_name': d.get('condition_name'),
                'ayurvedic_name': d.get('ayurvedic_name'),
                'dosha': d.get('dosha_involved', '')
            } for d in retrieved_docs
        ],
        'doctor_contributions_count': len(doctor_insights)
    })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

@app.route('/api/copilot/history')
@login_required
def api_copilot_history():
    history = get_user_consultations(session['user_id'], limit=15)
    return jsonify({'history': history})

# ==========================================
# EMERGENCY SOS API ENDPOINTS
# ==========================================

@app.route('/api/sos/create', methods=['POST'])
@login_required
def api_sos_create():
    user = get_user_by_id(session['user_id'])
    data = request.get_json() or {}
    lat = float(data.get('latitude', Config.DEFAULT_LAT))
    lng = float(data.get('longitude', Config.DEFAULT_LNG))
    trigger_type = data.get('trigger_type', 'sudden_motion')
    address = data.get('address', 'Current Live GPS Location')
    countdown = user.get('sos_timeout_seconds') or 30

    alert_id = create_sos_alert(
        user_id=user['id'],
        trigger_type=trigger_type,
        latitude=lat,
        longitude=lng,
        address=address,
        countdown_seconds=countdown
    )

    return jsonify({
        'status': 'pending',
        'alert_id': alert_id,
        'countdown_seconds': countdown,
        'message': f"Emergency countdown initiated ({countdown}s). Press 'I Am Safe' to cancel."
    })

@app.route('/api/sos/cancel', methods=['POST'])
@login_required
def api_sos_cancel():
    data = request.get_json() or {}
    alert_id = data.get('alert_id')
    if alert_id:
        update_sos_alert(alert_id, status='CANCELLED_SAFE', notes="User confirmed safety before timeout.")
    return jsonify({'status': 'cancelled', 'message': 'SOS alert has been safely cancelled.'})

@app.route('/api/sos/dispatch', methods=['POST'])
@login_required
def api_sos_dispatch():
    user = get_user_by_id(session['user_id'])
    data = request.get_json() or {}
    alert_id = data.get('alert_id')
    lat = float(data.get('latitude', Config.DEFAULT_LAT))
    lng = float(data.get('longitude', Config.DEFAULT_LNG))
    trigger_reason = data.get('reason', 'User did not respond within emergency time range')

    if not alert_id:
        alert_id = create_sos_alert(
            user_id=user['id'],
            trigger_type='timeout_inactivity',
            latitude=lat,
            longitude=lng,
            address="Live GPS Coordinates",
            countdown_seconds=user.get('sos_timeout_seconds') or 30
        )

    # Execute Cascading SOS Priority: Hospital -> Police -> Registered Doctors
    result = EmergencyService.execute_cascading_sos(
        alert_id=alert_id,
        user_id=user['id'],
        lat=lat,
        lng=lng,
        trigger_reason=trigger_reason
    )

    return jsonify(result)

@app.route('/api/sos/nearby', methods=['GET', 'POST'])
@login_required
def api_sos_nearby():
    if request.method == 'POST':
        data = request.get_json() or {}
        lat = float(data.get('latitude', Config.DEFAULT_LAT))
        lng = float(data.get('longitude', Config.DEFAULT_LNG))
    else:
        lat = float(request.args.get('lat', Config.DEFAULT_LAT))
        lng = float(request.args.get('lng', Config.DEFAULT_LNG))

    hospitals = EmergencyService.find_nearby_hospitals(lat, lng)
    police = EmergencyService.find_nearby_police_stations(lat, lng)
    doctors = EmergencyService.get_app_registered_doctors(lat, lng)

    return jsonify({
        'latitude': lat,
        'longitude': lng,
        'hospitals': hospitals,
        'police_stations': police,
        'registered_doctors': doctors
    })

# ==========================================
# DOCTOR CONTRIBUTION ENDPOINTS
# ==========================================

@app.route('/api/doctor/contribute', methods=['POST'])
@doctor_required
def api_doctor_contribute():
    user = get_user_by_id(session['user_id'])
    data = request.get_json() or request.form
    
    condition_name = data.get('condition_name', '').strip()
    ayurvedic_name = data.get('ayurvedic_name', '').strip()
    dosha_type = data.get('dosha_type', 'Tridoshic')
    symptoms = data.get('symptoms', '').strip()
    step_by_step_cure = data.get('step_by_step_cure', '').strip()
    herbs_used = data.get('herbs_used', '').strip()
    dietary_guidelines = data.get('dietary_guidelines', '').strip()
    contraindications = data.get('contraindications', '').strip()

    if not condition_name or not step_by_step_cure:
        return jsonify({'error': 'Condition Name and Step-by-Step Cure are required.'}), 400

    contribution_id = add_doctor_contribution(
        doctor_id=user['id'],
        condition_name=condition_name,
        ayurvedic_name=ayurvedic_name,
        dosha_type=dosha_type,
        symptoms=symptoms,
        step_by_step_cure=step_by_step_cure,
        herbs_used=herbs_used,
        dietary_guidelines=dietary_guidelines,
        contraindications=contraindications
    )

    return jsonify({
        'status': 'success',
        'contribution_id': contribution_id,
        'message': 'Your clinical contribution has been added to the RAG knowledge base.'
    })

# Initialize application database & precompute warmups
init_db()
seed_sample_data()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting AyurCare Copilot server on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
