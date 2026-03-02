# ==========================================
# HEARTBEAT - Main Application
# ==========================================

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import bcrypt
import os
from dotenv import load_dotenv

# Load environment variables — look for .env in project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialise Flask app
app = Flask(
    __name__,
    template_folder='../frontend/pages',
    static_folder='../frontend',
    static_url_path=''
)

# Secret key for sessions
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key')

# ===== MySQL Configuration =====
app.config['MYSQL_HOST'] = os.getenv('DB_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('DB_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('DB_NAME', 'heartbeat_db')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialise MySQL
mysql = MySQL(app)


# ===== ROUTES =====

# --- Landing Page ---
@app.route('/')
def home():
    # If user is already logged in, go to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# --- Sign Up ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Validation
        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('register'))

        # Check if email already exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            flash('Email already registered. Please log in.', 'error')
            cur.close()
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert new user
        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password.decode('utf-8'))
        )
        mysql.connection.commit()
        cur.close()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Validation
        if not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('login'))

        # Find user by email
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # Login successful — store user in session
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


# --- Dashboard (after login) ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=5000)