-- Add table to track user difficulty progress per language
CREATE TABLE IF NOT EXISTS user_difficulty_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    language VARCHAR(10) NOT NULL,
    easy_completed INT DEFAULT 0,
    medium_completed INT DEFAULT 0,
    hard_completed INT DEFAULT 0,
    current_difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'easy',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_patient_language (patient_id, language),
    FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_patient_language (patient_id, language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
