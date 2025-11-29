-- Aphasia Therapy Database Schema
-- MySQL Database for Patient Management and Progress Tracking

-- Create Database
CREATE DATABASE IF NOT EXISTS aphasia_therapy_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE aphasia_therapy_db;

-- ============================================
-- 1. USERS TABLE (Patients and Clinicians)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    user_type ENUM('patient', 'clinician') NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    gender ENUM('male', 'female', 'other'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_email (email),
    INDEX idx_user_type (user_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2. PATIENT PROFILES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS patient_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    wab_score DECIMAL(5,2) DEFAULT 0.00,
    severity_level ENUM('Mild', 'Moderate', 'Severe', 'Very Severe') DEFAULT 'Moderate',
    aphasia_type VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'en',
    assigned_clinician_id VARCHAR(50),
    medical_history TEXT,
    therapy_start_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_clinician_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_severity (severity_level),
    INDEX idx_clinician (assigned_clinician_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3. THERAPY SESSIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS therapy_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    patient_id VARCHAR(50) NOT NULL,
    session_type ENUM('sentence', 'picture', 'assessment') NOT NULL,
    language VARCHAR(10) NOT NULL,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'easy',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    duration_seconds INT,
    total_exercises INT DEFAULT 0,
    completed_exercises INT DEFAULT 0,
    average_accuracy DECIMAL(5,2) DEFAULT 0.00,
    wab_score DECIMAL(5,2),
    session_notes TEXT,
    FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_patient (patient_id),
    INDEX idx_session_type (session_type),
    INDEX idx_date (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. EXERCISE ATTEMPTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS exercise_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attempt_id VARCHAR(50) UNIQUE NOT NULL,
    session_id VARCHAR(50) NOT NULL,
    patient_id VARCHAR(50) NOT NULL,
    exercise_type ENUM('sentence', 'picture') NOT NULL,
    target_text TEXT NOT NULL,
    transcription TEXT,
    accuracy DECIMAL(5,2) DEFAULT 0.00,
    wab_score DECIMAL(5,2),
    severity_level VARCHAR(50),
    feedback TEXT,
    word_corrections JSON,
    practice_suggestions JSON,
    audio_file_path VARCHAR(500),
    attempt_number INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES therapy_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_session (session_id),
    INDEX idx_patient (patient_id),
    INDEX idx_accuracy (accuracy),
    INDEX idx_date (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. PICTURE EXERCISES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS picture_exercises (
    id INT AUTO_INCREMENT PRIMARY KEY,
    picture_id VARCHAR(50) UNIQUE NOT NULL,
    picture_name VARCHAR(255) NOT NULL,
    picture_url VARCHAR(500) NOT NULL,
    target_text_en VARCHAR(255),
    target_text_hi VARCHAR(255),
    target_text_kn VARCHAR(255),
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'easy',
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_difficulty (difficulty),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 6. SENTENCE EXERCISES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS sentence_exercises (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sentence_id VARCHAR(50) UNIQUE NOT NULL,
    text_en TEXT,
    text_hi TEXT,
    text_kn TEXT,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'easy',
    category VARCHAR(100),
    target_words JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_difficulty (difficulty),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 7. PROGRESS TRACKING TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS patient_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    sessions_completed INT DEFAULT 0,
    total_exercises INT DEFAULT 0,
    average_accuracy DECIMAL(5,2) DEFAULT 0.00,
    wab_score DECIMAL(5,2),
    severity_level VARCHAR(50),
    streak_days INT DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_patient_date (patient_id, date),
    INDEX idx_patient (patient_id),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 8. CLINICIAN NOTES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS clinician_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id VARCHAR(50) UNIQUE NOT NULL,
    patient_id VARCHAR(50) NOT NULL,
    clinician_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(50),
    note_type ENUM('assessment', 'progress', 'recommendation', 'other') DEFAULT 'other',
    title VARCHAR(255),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (clinician_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES therapy_sessions(session_id) ON DELETE SET NULL,
    INDEX idx_patient (patient_id),
    INDEX idx_clinician (clinician_id),
    INDEX idx_date (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 9. INITIAL ASSESSMENT RESULTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS assessment_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id VARCHAR(50) UNIQUE NOT NULL,
    patient_id VARCHAR(50) NOT NULL,
    wab_score DECIMAL(5,2) NOT NULL,
    severity_level VARCHAR(50) NOT NULL,
    detailed_scores JSON,
    recommendations TEXT,
    assessed_by VARCHAR(50),
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (assessed_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_patient (patient_id),
    INDEX idx_date (assessment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- INSERT SAMPLE PICTURE EXERCISES
-- ============================================
INSERT INTO picture_exercises (picture_id, picture_name, picture_url, target_text_en, target_text_hi, target_text_kn, difficulty, category) VALUES
('pic_001', 'Apple', '/images/exercises/apple.jpg', 'apple', 'सेब', 'ಸೇಬು', 'easy', 'Food'),
('pic_002', 'Cat', '/images/exercises/cat.jpg', 'cat', 'बिल्ली', 'ಬೆಕ್ಕು', 'easy', 'Animals'),
('pic_003', 'House', '/images/exercises/house.jpg', 'house', 'घर', 'ಮನೆ', 'easy', 'Objects'),
('pic_004', 'Dog', '/images/exercises/dog.jpg', 'dog', 'कुत्ता', 'ನಾಯಿ', 'easy', 'Animals'),
('pic_005', 'Car', '/images/exercises/car.jpg', 'car', 'गाड़ी', 'ಕಾರು', 'easy', 'Vehicles'),
('pic_006', 'Book', '/images/exercises/book.jpg', 'book', 'किताब', 'ಪುಸ್ತಕ', 'easy', 'Objects'),
('pic_007', 'Chair', '/images/exercises/chair.jpg', 'chair', 'कुर्सी', 'ಕುರ್ಚಿ', 'medium', 'Furniture'),
('pic_008', 'Table', '/images/exercises/table.jpg', 'table', 'मेज़', 'ಮೇಜು', 'medium', 'Furniture'),
('pic_009', 'Flower', '/images/exercises/flower.jpg', 'flower', 'फूल', 'ಹೂವು', 'medium', 'Nature'),
('pic_010', 'Tree', '/images/exercises/tree.jpg', 'tree', 'पेड़', 'ಮರ', 'medium', 'Nature');

-- ============================================
-- INSERT SAMPLE SENTENCE EXERCISES
-- ============================================
INSERT INTO sentence_exercises (sentence_id, text_en, text_hi, text_kn, difficulty, category, target_words) VALUES
('sent_001', 'Hello, how are you?', 'नमस्ते, आप कैसे हैं?', 'ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?', 'easy', 'Greetings', '["hello", "how", "you"]'),
('sent_002', 'I am fine, thank you.', 'मैं ठीक हूं, धन्यवाद।', 'ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ, ಧನ್ಯವಾದ.', 'easy', 'Greetings', '["fine", "thank", "you"]'),
('sent_003', 'What is your name?', 'आपका नाम क्या है?', 'ನಿಮ್ಮ ಹೆಸರೇನು?', 'easy', 'Greetings', '["what", "name"]'),
('sent_004', 'I need water.', 'मुझे पानी चाहिए।', 'ನನಗೆ ನೀರು ಬೇಕು.', 'easy', 'Daily Needs', '["need", "water"]'),
('sent_005', 'Please help me.', 'कृपया मेरी मदद करें।', 'ದಯವಿಟ್ಟು ನನಗೆ ಸಹಾಯ ಮಾಡಿ.', 'easy', 'Daily Needs', '["please", "help"]');

-- ============================================
-- CREATE VIEWS FOR ANALYTICS
-- ============================================

-- Patient Progress Summary View
CREATE OR REPLACE VIEW patient_progress_summary AS
SELECT 
    u.user_id,
    u.name,
    u.email,
    pp.wab_score,
    pp.severity_level,
    pp.preferred_language,
    COUNT(DISTINCT ts.session_id) as total_sessions,
    AVG(ts.average_accuracy) as overall_accuracy,
    MAX(ts.start_time) as last_session_date,
    DATEDIFF(CURDATE(), MAX(ts.start_time)) as days_since_last_session
FROM users u
LEFT JOIN patient_profiles pp ON u.user_id = pp.user_id
LEFT JOIN therapy_sessions ts ON u.user_id = ts.patient_id
WHERE u.user_type = 'patient'
GROUP BY u.user_id, u.name, u.email, pp.wab_score, pp.severity_level, pp.preferred_language;

-- Session Performance View
CREATE OR REPLACE VIEW session_performance AS
SELECT 
    ts.session_id,
    ts.patient_id,
    u.name as patient_name,
    ts.session_type,
    ts.language,
    ts.difficulty,
    ts.start_time,
    ts.duration_seconds,
    ts.completed_exercises,
    ts.average_accuracy,
    ts.wab_score,
    COUNT(ea.id) as total_attempts,
    AVG(ea.accuracy) as avg_attempt_accuracy
FROM therapy_sessions ts
JOIN users u ON ts.patient_id = u.user_id
LEFT JOIN exercise_attempts ea ON ts.session_id = ea.session_id
GROUP BY ts.session_id, ts.patient_id, u.name, ts.session_type, ts.language, 
         ts.difficulty, ts.start_time, ts.duration_seconds, ts.completed_exercises, 
         ts.average_accuracy, ts.wab_score;

-- ============================================
-- STORED PROCEDURES
-- ============================================

DELIMITER //

-- Procedure to update patient progress
CREATE PROCEDURE update_patient_progress(
    IN p_patient_id VARCHAR(50),
    IN p_date DATE,
    IN p_wab_score DECIMAL(5,2),
    IN p_severity VARCHAR(50)
)
BEGIN
    INSERT INTO patient_progress (patient_id, date, sessions_completed, wab_score, severity_level)
    VALUES (p_patient_id, p_date, 1, p_wab_score, p_severity)
    ON DUPLICATE KEY UPDATE
        sessions_completed = sessions_completed + 1,
        wab_score = p_wab_score,
        severity_level = p_severity;
END //

-- Procedure to calculate streak
CREATE PROCEDURE calculate_streak(IN p_patient_id VARCHAR(50))
BEGIN
    DECLARE current_streak INT DEFAULT 0;
    DECLARE last_date DATE;
    
    SELECT MAX(date) INTO last_date
    FROM patient_progress
    WHERE patient_id = p_patient_id;
    
    IF last_date = CURDATE() THEN
        SELECT streak_days INTO current_streak
        FROM patient_progress
        WHERE patient_id = p_patient_id AND date = last_date;
        
        SET current_streak = current_streak + 1;
        
        UPDATE patient_progress
        SET streak_days = current_streak
        WHERE patient_id = p_patient_id AND date = last_date;
    END IF;
END //

DELIMITER ;

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX idx_session_patient_date ON therapy_sessions(patient_id, start_time);
CREATE INDEX idx_attempt_session_date ON exercise_attempts(session_id, created_at);
CREATE INDEX idx_progress_patient_date ON patient_progress(patient_id, date DESC);
