import io
import json
from PIL import Image
from app import app
from database import get_db, get_user_by_email, get_registered_doctors

def test_full_system():
    client = app.test_client()
    print("=== Step 1: Testing Database & Sample Seed Data ===")
    doctors = get_registered_doctors(available_only=True)
    print(f"Sample registered doctors in system: {len(doctors)}")
    for d in doctors:
        print(f" - {d['name']} ({d.get('doctor_specialization')}), Retired: {d.get('is_retired')}")
    assert len(doctors) >= 2, "Should have at least 2 seeded doctors"

    print("\n=== Step 2: Testing User Registration with Preferred Language & SOS Timeout ===")
    reg_response = client.post('/register', data={
        'name': 'Test Patient',
        'email': 'patient@test.com',
        'password': 'password123',
        'preferred_language': 'Hindi',
        'sos_timeout_seconds': '30',
        'emergency_contact_name': 'Guardian Test',
        'emergency_contact_phone': '+91-9876543210',
        'is_doctor': 'no'
    }, follow_redirects=True)
    assert reg_response.status_code == 200
    user = get_user_by_email('patient@test.com')
    assert user is not None, "User should be registered in SQLite"
    assert user['preferred_language'] == 'Hindi'
    assert user['sos_timeout_seconds'] == 30
    assert user['is_doctor'] == 0
    print("User registered successfully with Hindi language and 30s SOS timeout.")

    print("\n=== Step 3: Testing Login ===")
    client.get('/logout')
    login_resp = client.post('/login', data={
        'email': 'patient@test.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    print("Login successful and session active.")

    print("\n=== Step 4: Testing Ayurvedic AI Copilot with RAG (Fever in Hindi) ===")
    consult_resp = client.post('/api/copilot/consult', data={
        'prompt': 'I have a high fever with chills and headache. Please suggest natural Ayurvedic cure step by step.',
        'language': 'Hindi'
    })
    print(f"Consultation HTTP status: {consult_resp.status_code}")
    assert consult_resp.status_code == 200
    consult_data = consult_resp.get_json()
    assert consult_data['status'] == 'success'
    print(f"Detected Condition: {consult_data.get('condition')}")
    print(f"Language Used: {consult_data.get('language')}")
    print(f"RAG Sources: {[s['condition_name'] for s in consult_data.get('rag_sources', [])]}")
    print("\n--- Sample AI Response Preview (Hindi) ---")
    print(consult_data.get('response')[:400] + "...\n")

    print("\n=== Step 5: Testing Multimodal Image Upload & Extraction ===")
    # Create sample image
    img = Image.new('RGB', (120, 120), color=(144, 238, 144)) # Light green leaf image
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    
    img_resp = client.post('/api/copilot/consult', data={
        'prompt': 'Identify this herb and give Ayurvedic remedies for digestion.',
        'language': 'English',
        'image': (buf, 'herb_sample.jpg')
    })
    print(f"Multimodal Consult status: {img_resp.status_code}")
    assert img_resp.status_code == 200
    img_data = img_resp.get_json()
    assert img_data['status'] == 'success'
    print(f"Image Analysis: {img_data.get('image_analysis')}")

    print("\n=== Step 6: Testing SOS Radar & Cascading Dispatch ===")
    # Test nearby facility scanning
    nearby_resp = client.get('/api/sos/nearby?lat=17.3850&lng=78.4867')
    assert nearby_resp.status_code == 200
    nearby_data = nearby_resp.get_json()
    print(f"Nearby Hospitals found: {len(nearby_data.get('hospitals', []))}")
    print(f"Nearby Police Stations found: {len(nearby_data.get('police_stations', []))}")
    print(f"Nearby Registered Doctors found: {len(nearby_data.get('registered_doctors', []))}")

    # Test SOS Creation
    create_sos_resp = client.post('/api/sos/create', json={
        'latitude': 17.3850,
        'longitude': 78.4867,
        'trigger_type': 'sudden_motion'
    })
    assert create_sos_resp.status_code == 200
    sos_create_data = create_sos_resp.get_json()
    alert_id = sos_create_data['alert_id']
    print(f"Pending SOS Alert created with ID: {alert_id}, countdown: {sos_create_data['countdown_seconds']}s")

    # Test Cascading Dispatch
    dispatch_resp = client.post('/api/sos/dispatch', json={
        'alert_id': alert_id,
        'latitude': 17.3850,
        'longitude': 78.4867,
        'reason': 'Timeout expired without user response'
    })
    assert dispatch_resp.status_code == 200
    dispatch_data = dispatch_resp.get_json()
    print(f"Cascade Dispatch Result: {dispatch_data.get('cascade_stage')}")
    print(f"Dispatched Target: {dispatch_data.get('target', {}).get('name')}")
    print(f"Gemini AI Responder Briefing: {dispatch_data.get('ai_briefing')}")

    print("\n=== Step 7: Testing Doctor Registration with Radio Button & Contribution to RAG ===")
    client.get('/logout')
    doc_reg_resp = client.post('/register', data={
        'name': 'Dr. Kavita Verma, BAMS',
        'email': 'dr.kavita@ayurcare.org',
        'password': 'password123',
        'preferred_language': 'English',
        'sos_timeout_seconds': '45',
        'is_doctor': 'yes',
        'doctor_specialization': 'Ayurvedic Consultant & Herbalist',
        'doctor_license_id': 'BAMS-DEL-4412',
        'is_retired': '1',
        'doctor_clinic_city': 'Connaught Place, Delhi'
    }, follow_redirects=True)
    assert doc_reg_resp.status_code == 200
    doc_user = get_user_by_email('dr.kavita@ayurcare.org')
    assert doc_user['is_doctor'] == 1
    assert doc_user['is_retired'] == 1
    print("Doctor registered successfully with is_doctor=1, is_retired=1.")

    # Doctor adds contribution to RAG
    contrib_resp = client.post('/api/doctor/contribute', json={
        'condition_name': 'Acute Pitta Acidity',
        'ayurvedic_name': 'Teekshna Amlapitta',
        'dosha_type': 'Pitta',
        'symptoms': 'Severe acid reflux and sour regurgitation',
        'step_by_step_cure': '1. Drink coconut water with roasted cumin. 2. Take Avipattikar Churna 3g before meals.',
        'herbs_used': 'Avipattikar, Amalaki, Shatavari',
        'dietary_guidelines': 'Strictly avoid chillies, pickles, and late meals',
        'contraindications': 'Consult emergency if vomit contains blood'
    })
    assert contrib_resp.status_code == 200
    print("Doctor clinical advice added to RAG repository successfully.")

    print("\n ALL SYSTEM TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_full_system()
