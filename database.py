import sqlite3
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not Config.UPLOAD_FOLDER.exists():
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                preferred_language TEXT NOT NULL DEFAULT 'English',
                sos_timeout_seconds INTEGER NOT NULL DEFAULT 30,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                emergency_contact_email TEXT,
                is_doctor INTEGER NOT NULL DEFAULT 0,
                doctor_specialization TEXT,
                doctor_license_id TEXT,
                is_retired INTEGER DEFAULT 0,
                is_available_for_sos INTEGER DEFAULT 1,
                doctor_clinic_city TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Health consultations / AI history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                prompt_text TEXT,
                image_filename TEXT,
                detected_condition TEXT,
                rag_sources TEXT,
                ai_response TEXT NOT NULL,
                language_used TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Doctor contributions to RAG
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctor_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER NOT NULL,
                condition_name TEXT NOT NULL,
                ayurvedic_name TEXT,
                dosha_type TEXT,
                symptoms TEXT,
                step_by_step_cure TEXT NOT NULL,
                herbs_used TEXT,
                dietary_guidelines TEXT,
                contraindications TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # SOS Alerts log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sos_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                trigger_type TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                address TEXT,
                status TEXT NOT NULL,
                dispatched_to_type TEXT,
                dispatched_target_name TEXT,
                dispatched_target_contact TEXT,
                countdown_seconds INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dispatched_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()

# --- User Model Helpers ---
def create_user(name, email, password, preferred_language='English', 
                sos_timeout_seconds=30, emergency_contact_name='', 
                emergency_contact_phone='', emergency_contact_email='',
                is_doctor=0, doctor_specialization='', doctor_license_id='',
                is_retired=0, is_available_for_sos=1, doctor_clinic_city=''):
    pwd_hash = generate_password_hash(password)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (
                name, email, password_hash, preferred_language,
                sos_timeout_seconds, emergency_contact_name,
                emergency_contact_phone, emergency_contact_email,
                is_doctor, doctor_specialization, doctor_license_id,
                is_retired, is_available_for_sos, doctor_clinic_city
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, email, pwd_hash, preferred_language,
            sos_timeout_seconds, emergency_contact_name,
            emergency_contact_phone, emergency_contact_email,
            is_doctor, doctor_specialization, doctor_license_id,
            is_retired, is_available_for_sos, doctor_clinic_city
        ))
        conn.commit()
        return cursor.lastrowid

def get_user_by_email(email):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_user_profile(user_id, **kwargs):
    fields = []
    values = []
    for k, v in kwargs.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(user_id)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", tuple(values))
        conn.commit()

def verify_user(email, password):
    user = get_user_by_email(email)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

def get_registered_doctors(available_only=True):
    with get_db() as conn:
        cursor = conn.cursor()
        if available_only:
            cursor.execute('SELECT * FROM users WHERE is_doctor = 1 AND is_available_for_sos = 1')
        else:
            cursor.execute('SELECT * FROM users WHERE is_doctor = 1')
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

# --- Consultations Helpers ---
def save_consultation(user_id, prompt_text, image_filename, detected_condition, rag_sources, ai_response, language_used):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO consultations (
                user_id, prompt_text, image_filename,
                detected_condition, rag_sources, ai_response, language_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, prompt_text, image_filename,
            detected_condition, json.dumps(rag_sources) if rag_sources else '[]',
            ai_response, language_used
        ))
        conn.commit()
        return cursor.lastrowid

def get_user_consultations(user_id, limit=20):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM consultations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        ''', (user_id, limit))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

# --- Doctor Contributions Helpers ---
def add_doctor_contribution(doctor_id, condition_name, ayurvedic_name, dosha_type, symptoms, step_by_step_cure, herbs_used, dietary_guidelines, contraindications):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO doctor_contributions (
                doctor_id, condition_name, ayurvedic_name, dosha_type,
                symptoms, step_by_step_cure, herbs_used,
                dietary_guidelines, contraindications
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            doctor_id, condition_name, ayurvedic_name, dosha_type,
            symptoms, step_by_step_cure, herbs_used,
            dietary_guidelines, contraindications
        ))
        conn.commit()
        return cursor.lastrowid

def get_all_doctor_contributions():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dc.*, u.name as doctor_name, u.doctor_specialization, u.is_retired
            FROM doctor_contributions dc
            JOIN users u ON dc.doctor_id = u.id
            ORDER BY dc.created_at DESC
        ''')
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

# --- SOS Helpers ---
def create_sos_alert(user_id, trigger_type, latitude, longitude, address, countdown_seconds):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sos_alerts (
                user_id, trigger_type, latitude, longitude, address,
                status, countdown_seconds
            ) VALUES (?, ?, ?, ?, ?, 'PENDING_CONFIRMATION', ?)
        ''', (user_id, trigger_type, latitude, longitude, address, countdown_seconds))
        conn.commit()
        return cursor.lastrowid

def update_sos_alert(alert_id, status, dispatched_to_type=None, dispatched_target_name=None, dispatched_target_contact=None, notes=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE sos_alerts SET
                status = ?,
                dispatched_to_type = COALESCE(?, dispatched_to_type),
                dispatched_target_name = COALESCE(?, dispatched_target_name),
                dispatched_target_contact = COALESCE(?, dispatched_target_contact),
                notes = COALESCE(?, notes),
                dispatched_at = CASE WHEN ? LIKE 'DISPATCHED%' THEN CURRENT_TIMESTAMP ELSE dispatched_at END
            WHERE id = ?
        ''', (status, dispatched_to_type, dispatched_target_name, dispatched_target_contact, notes, status, alert_id))
        conn.commit()

def get_sos_alert(alert_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sos_alerts WHERE id = ?', (alert_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_active_sos_alerts_for_doctor():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT sa.*, u.name as user_name, u.emergency_contact_phone, u.emergency_contact_name
            FROM sos_alerts sa
            JOIN users u ON sa.user_id = u.id
            WHERE sa.status LIKE 'DISPATCHED%'
            ORDER BY sa.created_at DESC LIMIT 30
        ''')
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_user_sos_history(user_id, limit=10):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM sos_alerts WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        ''', (user_id, limit))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def seed_sample_data():
    """Seed initial registered retired and active doctors with Ayurvedic clinical contributions"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE is_doctor = 1")
        count = cursor.fetchone()['cnt']
        if count == 0:
            # Seed Doctor 1: Retired Chief Ayurvedic Physician
            d1_pwd = generate_password_hash("doctor123")
            cursor.execute('''
                INSERT INTO users (
                    name, email, password_hash, preferred_language,
                    sos_timeout_seconds, emergency_contact_name,
                    emergency_contact_phone, emergency_contact_email,
                    is_doctor, doctor_specialization, doctor_license_id,
                    is_retired, is_available_for_sos, doctor_clinic_city
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                "Dr. Rajesh Sharma, MD (Ayu)", "dr.rajesh@ayurcare.org", d1_pwd, "Hindi",
                30, "Dr. Sunita Sharma", "+91-9848011223", "sunita@ayurcare.org",
                1, "Senior Ayurvedic Physician & Panchakarma", "AYUR-TEL-10492",
                1, 1, "Hyderabad Central"
            ))
            d1_id = cursor.lastrowid
            
            # Seed Doctor 2: Retired Emergency Medicine Consultant
            cursor.execute('''
                INSERT INTO users (
                    name, email, password_hash, preferred_language,
                    sos_timeout_seconds, emergency_contact_name,
                    emergency_contact_phone, emergency_contact_email,
                    is_doctor, doctor_specialization, doctor_license_id,
                    is_retired, is_available_for_sos, doctor_clinic_city
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                "Dr. Meenakshi Sundaram, MBBS, MS", "dr.meenakshi@ayurcare.org", d1_pwd, "Tamil",
                30, "R. Sundaram", "+91-9444088991", "meena@ayurcare.org",
                1, "Retired Emergency & Trauma Consultant", "TN-MED-38821",
                1, 1, "South Zone Trauma Circle"
            ))
            d2_id = cursor.lastrowid

            # Seed Doctor 3: Integrative Medicine & Ayurvedic Practitioner
            cursor.execute('''
                INSERT INTO users (
                    name, email, password_hash, preferred_language,
                    sos_timeout_seconds, emergency_contact_name,
                    emergency_contact_phone, emergency_contact_email,
                    is_doctor, doctor_specialization, doctor_license_id,
                    is_retired, is_available_for_sos, doctor_clinic_city
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                "Dr. Vikram Rao, BAMS", "dr.vikram@ayurcare.org", d1_pwd, "Telugu",
                30, "Kavita Rao", "+91-9988776655", "kavita@ayurcare.org",
                1, "Ayurvedic Internal Medicine", "AP-AYUR-89914",
                0, 1, "Banjara Hills"
            ))
            d3_id = cursor.lastrowid

            # Add clinical insights into RAG
            cursor.execute('''
                INSERT INTO doctor_contributions (
                    doctor_id, condition_name, ayurvedic_name, dosha_type,
                    symptoms, step_by_step_cure, herbs_used,
                    dietary_guidelines, contraindications
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                d1_id, "Acute High Fever & Viral Malaise", "Teevra Vata-Pitta Jwara", "Vata-Pitta",
                "Temperature spike > 101F, severe headache, bitter tongue coating, loss of appetite",
                "1. Administer Giloy (Guduchi) Kwath 40ml warm with 1 pinch pippali twice daily.\n2. Apply wet sandalwood forehead wrap.\n3. Drink shadanga paniya (water boiled with musta, parpataka, ushira, chandana, shunti).\n4. Fast from grains for 24 hours.",
                "Giloy Ghanvati, Maha Sudarshan Vati, Musta, Ushira",
                "Warm rice water gruel with roasted cumin; no dairy, no oily curries.",
                "Never expose body to chilled air or cold showers during active shivering."
            ))

            cursor.execute('''
                INSERT INTO doctor_contributions (
                    doctor_id, condition_name, ayurvedic_name, dosha_type,
                    symptoms, step_by_step_cure, herbs_used,
                    dietary_guidelines, contraindications
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                d3_id, "Severe Bronchial Congestion & Chest Cough", "Kaphaja Kasa", "Kapha",
                "Sticky chest phlegm, wheezing sound, throat tickle, morning heaviness",
                "1. Fresh ginger juice (1 tsp) + raw honey (1 tsp) + black pepper (pinch) 3 times a day.\n2. Inhale ajwain steam for 10 minutes.\n3. Sitopaladi Churna 3g with warm water after food.",
                "Sitopaladi, Talisadi, Mulethi, Ajwain, Black Pepper",
                "Warm clear vegetable broth with garlic; absolutely avoid bananas, curd, and ice cream.",
                "Do not suppress the urge to cough."
            ))

            conn.commit()

