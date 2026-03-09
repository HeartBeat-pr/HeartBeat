# ==========================================
# HEARTBEAT - Main Application (v2)
# ==========================================

import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
import mysql.connector
import bcrypt
from datetime import datetime, timedelta, date

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ===== APP SETUP =====
app = Flask(
    __name__,
    static_folder='../frontend',
    static_url_path='',
    template_folder='../frontend/pages'
)

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key')


# ===== DATABASE CONNECTION =====
def get_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'heartbeat_db')
    )


# ===== AUTH HELPER =====
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# AUTH ROUTES
# ==========================================

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (name, email, hashed_password.decode('utf-8'))
            )
            db.commit()
            cursor.close()
            db.close()

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))

        except mysql.connector.IntegrityError:
            flash('An account with that email already exists.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash('Welcome back, ' + user['name'] + '!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# ==========================================
# DASHBOARD
# ==========================================

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get most recent completed appointment for Recent Activity
    cursor.execute("""
        SELECT a.*, d.name as doc_name, d.specialty, d.medical_centre, d.location, d.rating, d.image_url
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.user_id = %s
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
        LIMIT 1
    """, (session['user_id'],))
    recent_appointment = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template('dashboard.html', recent_appointment=recent_appointment)


# ==========================================
# APPOINTMENTS
# ==========================================

@app.route('/appointments')
@login_required
def appointments():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get all doctors
    cursor.execute("SELECT * FROM doctors ORDER BY name")
    doctors = cursor.fetchall()

    # Upcoming appointments
    cursor.execute("""
        SELECT a.*, d.name as doc_name, d.specialty, d.medical_centre, d.location, d.rating
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.user_id = %s AND a.status = 'upcoming'
        ORDER BY a.appointment_date, a.appointment_time
    """, (session['user_id'],))
    upcoming = cursor.fetchall()

    # Past appointments
    cursor.execute("""
        SELECT a.*, d.name as doc_name, d.specialty, d.medical_centre, d.location, d.rating
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.user_id = %s AND a.status IN ('completed', 'cancelled')
        ORDER BY a.appointment_date DESC
    """, (session['user_id'],))
    past = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('appointments.html', doctors=doctors, upcoming=upcoming, past=past)


@app.route('/api/doctor-availability/<int:doctor_id>')
@login_required
def doctor_availability(doctor_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get doctor's availability
    cursor.execute("""
        SELECT * FROM doctor_availability WHERE doctor_id = %s ORDER BY FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
    """, (doctor_id,))
    availability = cursor.fetchall()

    # Get doctor info
    cursor.execute("SELECT * FROM doctors WHERE id = %s", (doctor_id,))
    doctor = cursor.fetchone()

    # Get existing appointments for this doctor (to block taken slots)
    cursor.execute("""
        SELECT appointment_date, appointment_time FROM appointments
        WHERE doctor_id = %s AND status = 'upcoming'
    """, (doctor_id,))
    booked_raw = cursor.fetchall()

    booked = []
    for b in booked_raw:
        booked.append({
            'date': b['appointment_date'].isoformat(),
            'time': str(b['appointment_time'])
        })

    cursor.close()
    db.close()

    # Convert availability for JSON
    avail_data = []
    for a in availability:
        avail_data.append({
            'day': a['day_of_week'],
            'start': str(a['start_time']),
            'end': str(a['end_time']),
            'slot_duration': a['slot_duration']
        })

    return jsonify({
        'doctor': {
            'id': doctor['id'],
            'name': doctor['name'],
            'specialty': doctor['specialty'],
            'medical_centre': doctor['medical_centre'],
            'location': doctor['location'],
            'rating': float(doctor['rating'])
        },
        'availability': avail_data,
        'booked': booked
    })


@app.route('/appointments/book', methods=['POST'])
@login_required
def book_appointment():
    doctor_id = request.form.get('doctor_id', '')
    appointment_date = request.form.get('appointment_date', '')
    appointment_time = request.form.get('appointment_time', '')
    notes = request.form.get('notes', '').strip()

    if not doctor_id or not appointment_date or not appointment_time:
        flash('Please select a doctor, date, and time.', 'error')
        return redirect(url_for('appointments'))

    # Check the slot isn't already taken
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id FROM appointments
        WHERE doctor_id = %s AND appointment_date = %s AND appointment_time = %s AND status = 'upcoming'
    """, (doctor_id, appointment_date, appointment_time))
    existing = cursor.fetchone()

    if existing:
        flash('That time slot is already booked. Please choose another.', 'error')
        cursor.close()
        db.close()
        return redirect(url_for('appointments'))

    # Get doctor details for the appointment record
    cursor.execute("SELECT name, specialty FROM doctors WHERE id = %s", (doctor_id,))
    doctor = cursor.fetchone()

    cursor.execute("""
        INSERT INTO appointments (user_id, doctor_id, doctor_name, specialty, appointment_date, appointment_time, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (session['user_id'], doctor_id, doctor['name'], doctor['specialty'], appointment_date, appointment_time, notes))

    db.commit()
    cursor.close()
    db.close()

    flash('Appointment booked with ' + doctor['name'] + '!', 'success')
    return redirect(url_for('appointments'))


@app.route('/appointments/cancel/<int:appointment_id>')
@login_required
def cancel_appointment(appointment_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE appointments SET status = 'cancelled' WHERE id = %s AND user_id = %s",
        (appointment_id, session['user_id'])
    )
    db.commit()
    cursor.close()
    db.close()

    flash('Appointment cancelled.', 'success')
    return redirect(url_for('appointments'))


# ==========================================
# PRESCRIPTIONS
# ==========================================

@app.route('/prescriptions')
@login_required
def prescriptions():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Doctor-prescribed medications
    cursor.execute("""
        SELECT * FROM prescriptions WHERE user_id = %s AND status = 'active' ORDER BY start_date DESC
    """, (session['user_id'],))
    prescribed = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM prescriptions WHERE user_id = %s AND status IN ('completed', 'cancelled') ORDER BY start_date DESC
    """, (session['user_id'],))
    past_prescribed = cursor.fetchall()

    # OTC medications available
    cursor.execute("SELECT * FROM otc_medications ORDER BY category, name")
    otc_meds = cursor.fetchall()

    # User's OTC orders
    cursor.execute("""
        SELECT o.*, m.name as med_name, m.dosage, m.category, m.price
        FROM otc_orders o
        JOIN otc_medications m ON o.medication_id = m.id
        WHERE o.user_id = %s
        ORDER BY o.ordered_at DESC
    """, (session['user_id'],))
    otc_orders = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('prescriptions.html',
        prescribed=prescribed,
        past_prescribed=past_prescribed,
        otc_meds=otc_meds,
        otc_orders=otc_orders
    )


@app.route('/prescriptions/order-otc', methods=['POST'])
@login_required
def order_otc():
    medication_id = request.form.get('medication_id', '')
    quantity = request.form.get('quantity', '1')

    if not medication_id:
        flash('Please select a medication.', 'error')
        return redirect(url_for('prescriptions'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT name FROM otc_medications WHERE id = %s", (medication_id,))
    med = cursor.fetchone()

    cursor.execute(
        "INSERT INTO otc_orders (user_id, medication_id, quantity) VALUES (%s, %s, %s)",
        (session['user_id'], medication_id, quantity)
    )
    db.commit()
    cursor.close()
    db.close()

    flash(med['name'] + ' ordered successfully! Collect from your pharmacy.', 'success')
    return redirect(url_for('prescriptions'))


# ==========================================
# MEDICAL HISTORY
# ==========================================

@app.route('/medical-history')
@login_required
def medical_history():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM medical_records WHERE user_id = %s AND record_type NOT IN ('allergy', 'condition') ORDER BY record_date DESC",
        (session['user_id'],)
    )
    records = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM medical_records WHERE user_id = %s AND record_type IN ('allergy', 'condition') ORDER BY record_date DESC",
        (session['user_id'],)
    )
    allergies = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('medical-history.html', records=records, allergies=allergies)


@app.route('/medical-history/add', methods=['POST'])
@login_required
def add_medical_record():
    record_type = request.form.get('record_type', '')
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    record_date = request.form.get('record_date', '')
    doctor_name = request.form.get('doctor_name', '').strip()

    if not record_type or not title or not record_date:
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('medical_history'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO medical_records (user_id, record_type, title, description, record_date, doctor_name) VALUES (%s, %s, %s, %s, %s, %s)",
        (session['user_id'], record_type, title, description, record_date, doctor_name)
    )
    db.commit()
    cursor.close()
    db.close()

    flash('Medical record added successfully!', 'success')
    return redirect(url_for('medical_history'))


# ==========================================
# MENTAL HEALTH
# ==========================================

@app.route('/mental-health')
@login_required
def mental_health():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM mood_logs WHERE user_id = %s ORDER BY logged_at DESC LIMIT 30",
        (session['user_id'],)
    )
    mood_logs = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('mental-health.html', mood_logs=mood_logs)


@app.route('/mental-health/log', methods=['POST'])
@login_required
def log_mood():
    mood = request.form.get('mood', '')
    notes = request.form.get('mood_notes', '').strip()

    valid_moods = ['great', 'good', 'okay', 'not_great', 'struggling']
    if mood not in valid_moods:
        flash('Please select a valid mood.', 'error')
        return redirect(url_for('mental_health'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO mood_logs (user_id, mood, notes) VALUES (%s, %s, %s)",
        (session['user_id'], mood, notes)
    )
    db.commit()
    cursor.close()
    db.close()

    mood_messages = {
        'great': "That's wonderful! Keep up the positive energy! &#127775;",
        'good': "Glad to hear you're doing well! &#128522;",
        'okay': "It's okay to have neutral days. Take it easy. &#128153;",
        'not_great': "Sorry to hear that. Remember, it's okay to ask for help. &#128155;",
        'struggling': "We're here for you. Please reach out to someone you trust. &#128154;"
    }

    flash(mood_messages.get(mood, 'Mood logged successfully!'), 'success')
    return redirect(url_for('mental_health'))


# ==========================================
# ACCOUNT
# ==========================================

@app.route('/account')
@login_required
def account():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('account.html', user=user)


@app.route('/account/update', methods=['POST'])
@login_required
def update_account():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()

    if not name or not email:
        flash('Name and email are required.', 'error')
        return redirect(url_for('account'))

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET name = %s, email = %s WHERE id = %s",
            (name, email, session['user_id'])
        )
        db.commit()
        cursor.close()
        db.close()

        session['user_name'] = name
        session['user_email'] = email

        flash('Profile updated successfully!', 'success')

    except mysql.connector.IntegrityError:
        flash('That email is already in use.', 'error')

    return redirect(url_for('account'))


@app.route('/account/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not current_password or not new_password or not confirm_password:
        flash('All password fields are required.', 'error')
        return redirect(url_for('account'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('account'))

    if len(new_password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('account'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT password FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()

    if not bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
        flash('Current password is incorrect.', 'error')
        cursor.close()
        db.close()
        return redirect(url_for('account'))

    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute(
        "UPDATE users SET password = %s WHERE id = %s",
        (hashed.decode('utf-8'), session['user_id'])
    )
    db.commit()
    cursor.close()
    db.close()

    flash('Password changed successfully!', 'success')
    return redirect(url_for('account'))


# ==========================================
# MESSAGES
# ==========================================

@app.route('/messages')
@login_required
def messages():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM messages WHERE user_id = %s ORDER BY created_at DESC",
        (session['user_id'],)
    )
    inbox = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('messages.html', inbox=inbox)


# ==========================================
# RUN APP
# ==========================================

if __name__ == '__main__':
    app.run(debug=True, port=5000)