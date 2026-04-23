-- ==========================================
-- HEARTBEAT DATABASE SCHEMA
-- ==========================================

CREATE DATABASE IF NOT EXISTS heartbeat_db;
USE heartbeat_db;

-- ===== USERS =====
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== DOCTORS =====
CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    medical_centre VARCHAR(200) NOT NULL,
    location VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    rating DECIMAL(2,1) DEFAULT 4.5,
    image_url VARCHAR(255) DEFAULT '/images/doctor-default.png',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== DOCTOR AVAILABILITY =====
CREATE TABLE IF NOT EXISTS doctor_availability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id INT NOT NULL,
    day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday') NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    slot_duration INT DEFAULT 30,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

-- ===== APPOINTMENTS =====
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    doctor_id INT,
    doctor_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    location VARCHAR(255),
    notes TEXT,
    status ENUM('upcoming', 'completed', 'cancelled') DEFAULT 'upcoming',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

-- ===== PRESCRIPTIONS =====
CREATE TABLE IF NOT EXISTS prescriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    doctor_id INT,
    medication_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    prescribed_by VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE,
    status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

-- ===== MEDICAL HISTORY =====
CREATE TABLE IF NOT EXISTS medical_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    record_type ENUM('diagnosis', 'test_result', 'allergy', 'condition', 'surgery', 'other') NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    record_date DATE NOT NULL,
    doctor_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ===== MOOD LOGS (Mental Health) =====
CREATE TABLE IF NOT EXISTS mood_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    mood ENUM('great', 'good', 'okay', 'not_great', 'struggling') NOT NULL,
    notes TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ===== MESSAGES =====
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_type ENUM('patient', 'user', 'doctor') NOT NULL DEFAULT 'patient',
    sender_id INT NOT NULL,
    receiver_type ENUM('patient', 'user', 'doctor') NOT NULL DEFAULT 'doctor',
    receiver_id INT NOT NULL,
    subject VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== OTC MEDICATIONS =====
CREATE TABLE IF NOT EXISTS otc_medications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(5,2) DEFAULT 0.00
);

-- ===== OTC ORDERS =====
CREATE TABLE IF NOT EXISTS otc_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    medication_id INT NOT NULL,
    quantity INT DEFAULT 1,
    status ENUM('pending', 'confirmed', 'collected', 'cancelled') DEFAULT 'pending',
    ordered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (medication_id) REFERENCES otc_medications(id)
);

-- ==========================================
-- SEED DATA — Doctors
-- ==========================================

INSERT INTO doctors (name, email, password, specialty, medical_centre, location, phone, rating) VALUES
('Dr. Sarah Johnson', 'sarah.johnson@heartbeat.com', 'doctor123', 'General Practitioner', 'Huddersfield Health Centre', 'Huddersfield, England', '01484 123456', 4.8),
('Dr. James Patel', 'james.patel@heartbeat.com', 'doctor123', 'Dentist', 'Lindley Dental Practice', 'Huddersfield, England', '01484 234567', 4.7),
('Dr. Emily Chen', 'emily.chen@heartbeat.com', 'doctor123', 'Cardiologist', 'Calderdale Royal Hospital', 'Halifax, England', '01422 345678', 4.9),
('Dr. Michael Obi', 'michael.obi@heartbeat.com', 'doctor123', 'Dermatologist', 'Kirkburton Health Centre', 'Huddersfield, England', '01484 456789', 4.5),
('Dr. Amara Williams', 'amara.williams@heartbeat.com', 'doctor123', 'Psychiatrist', 'Folly Hall Medical Centre', 'Huddersfield, England', '01484 567890', 4.6);

-- ==========================================
-- SEED DATA — Doctor Availability
-- ==========================================

-- Dr. Sarah Johnson (GP) — Mon-Fri
INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, slot_duration) VALUES
(1, 'Monday', '09:00', '17:00', 30),
(1, 'Tuesday', '09:00', '17:00', 30),
(1, 'Wednesday', '09:00', '13:00', 30),
(1, 'Thursday', '09:00', '17:00', 30),
(1, 'Friday', '09:00', '15:00', 30);

-- Dr. James Patel (Dentist) — Mon, Wed, Fri
INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, slot_duration) VALUES
(2, 'Monday', '08:30', '16:30', 30),
(2, 'Wednesday', '08:30', '16:30', 30),
(2, 'Friday', '08:30', '14:00', 30);

-- Dr. Emily Chen (Cardiologist) — Tue, Thu
INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, slot_duration) VALUES
(3, 'Tuesday', '10:00', '16:00', 45),
(3, 'Thursday', '10:00', '16:00', 45);

-- Dr. Michael Obi (Dermatologist) — Mon, Tue, Thu, Fri
INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, slot_duration) VALUES
(4, 'Monday', '09:00', '17:00', 30),
(4, 'Tuesday', '09:00', '17:00', 30),
(4, 'Thursday', '09:00', '17:00', 30),
(4, 'Friday', '09:00', '13:00', 30);

-- Dr. Amara Williams (Psychiatrist) — Wed, Thu, Fri
INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, slot_duration) VALUES
(5, 'Wednesday', '10:00', '18:00', 60),
(5, 'Thursday', '10:00', '18:00', 60),
(5, 'Friday', '10:00', '16:00', 60);

-- ==========================================
-- SEED DATA — OTC Medications
-- ==========================================

INSERT INTO otc_medications (name, category, dosage, description, price) VALUES
('Paracetamol', 'Pain Relief', '500mg tablets (16 pack)', 'For mild to moderate pain and fever relief.', 1.50),
('Ibuprofen', 'Pain Relief', '200mg tablets (16 pack)', 'Anti-inflammatory painkiller for headaches, muscle pain, and fever.', 2.00),
('Cough Mixture (Dry)', 'Cough & Cold', '150ml bottle', 'Soothes dry, tickly coughs.', 3.50),
('Cough Mixture (Chesty)', 'Cough & Cold', '150ml bottle', 'Helps loosen and clear mucus from chesty coughs.', 3.50),
('Antihistamine (Cetirizine)', 'Allergy Relief', '10mg tablets (14 pack)', 'For hayfever and allergy symptoms.', 2.50),
('Throat Lozenges', 'Cough & Cold', '24 lozenges', 'Soothes sore throats and provides mild pain relief.', 2.00),
('Antacid Tablets', 'Digestive Health', '24 chewable tablets', 'Relieves heartburn, indigestion, and acid reflux.', 2.50),
('Rehydration Sachets', 'Digestive Health', '6 sachets', 'Replaces lost fluids and salts after diarrhoea or vomiting.', 3.00);