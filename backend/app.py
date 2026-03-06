# ==========================================
# HEARTBEAT - Main Application
# ==========================================

import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import mysql.connector
import bcrypt
from datetime import datetime

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
    return render_template('dashboard.html')


# ==========================================
# APPOINTMENTS
# ==========================================

@app.route('/appointments')
@login_required
def appointments():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Upcoming appointments
    cursor.execute(
        "SELECT * FROM appointments WHERE user_id = %s AND status = 'upcoming' ORDER BY appointment_date, appointment_time",
        (session['user_id'],)
    )
    upcoming = cursor.fetchall()

    # Past appointments
    cursor.execute(
        "SELECT * FROM appointments WHERE user_id = %s AND status IN ('completed', 'cancelled') ORDER BY appointment_date DESC",
        (session['user_id'],)
    )
    past = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('appointments.html', upcoming=upcoming, past=past)


@app.route('/appointments/book', methods=['POST'])
@login_required
def book_appointment():
    doctor_name = request.form.get('doctor_name', '').strip()
    specialty = request.form.get('specialty', '').strip()
    appointment_date = request.form.get('appointment_date', '')
    appointment_time = request.form.get('appointment_time', '')
    location = request.form.get('location', '').strip()
    notes = request.form.get('notes', '').strip()

    if not doctor_name or not specialty or not appointment_date or not appointment_time:
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('appointments'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO appointments (user_id, doctor_name, specialty, appointment_date, appointment_time, location, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (session['user_id'], doctor_name, specialty, appointment_date, appointment_time, location, notes)
    )
    db.commit()
    cursor.close()
    db.close()

    flash('Appointment booked successfully!', 'success')
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

    cursor.execute(
        "SELECT * FROM prescriptions WHERE user_id = %s AND status = 'active' ORDER BY start_date DESC",
        (session['user_id'],)
    )
    active = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM prescriptions WHERE user_id = %s AND status IN ('completed', 'cancelled') ORDER BY start_date DESC",
        (session['user_id'],)
    )
    past = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('prescriptions.html', active=active, past=past)


@app.route('/prescriptions/order', methods=['POST'])
@login_required
def order_prescription():
    medication_name = request.form.get('medication_name', '').strip()
    dosage = request.form.get('dosage', '').strip()
    frequency = request.form.get('frequency', '').strip()
    prescribed_by = request.form.get('prescribed_by', '').strip()
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '') or None
    notes = request.form.get('notes', '').strip()

    if not medication_name or not dosage or not frequency or not start_date:
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('prescriptions'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO prescriptions (user_id, medication_name, dosage, frequency, prescribed_by, start_date, end_date, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (session['user_id'], medication_name, dosage, frequency, prescribed_by, start_date, end_date, notes)
    )
    db.commit()
    cursor.close()
    db.close()

    flash('Prescription added successfully!', 'success')
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
        'great': "That's wonderful! Keep up the positive energy! 🌟",
        'good': "Glad to hear you're doing well! 😊",
        'okay': "It's okay to have neutral days. Take it easy. 💙",
        'not_great': "Sorry to hear that. Remember, it's okay to ask for help. 💛",
        'struggling': "We're here for you. Please reach out to someone you trust. 💚"
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