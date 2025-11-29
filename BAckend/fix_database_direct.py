"""
Direct database initialization using raw SQL
Bypasses SQLAlchemy reflection issues
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'aphasia_therapy_db')

print("=" * 70)
print("🚀 APHASIA THERAPY DATABASE INITIALIZATION (Direct SQL)")
print("=" * 70)

def get_connection(database=None):
    """Get MySQL connection"""
    if DB_PASSWORD:
        return pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=database,
            charset='utf8mb4',
            autocommit=True
        )
    else:
        return pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            database=database,
            charset='utf8mb4',
            autocommit=True
        )

def create_database():
    """Create database"""
    print("\n📦 Creating database...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        conn.close()
        print(f"✅ Database '{DB_NAME}' ready")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_tables():
    """Create all tables using raw SQL"""
    print("\n📋 Creating tables...")
    
    sql_statements = [
        # Users table
        """
        CREATE TABLE IF NOT EXISTS `users` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `user_id` VARCHAR(50) UNIQUE NOT NULL,
            `email` VARCHAR(255) UNIQUE NOT NULL,
            `password_hash` VARCHAR(255) NOT NULL,
            `name` VARCHAR(255) NOT NULL,
            `user_type` ENUM('patient', 'clinician') NOT NULL,
            `phone` VARCHAR(20),
            `date_of_birth` DATE,
            `gender` ENUM('male', 'female', 'other'),
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            `last_login` TIMESTAMP NULL,
            `is_active` BOOLEAN DEFAULT TRUE,
            INDEX `idx_email` (`email`),
            INDEX `idx_user_id` (`user_id`),
            INDEX `idx_user_type` (`user_type`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # Patient profiles table
        """
        CREATE TABLE IF NOT EXISTS `patient_profiles` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `user_id` VARCHAR(50) UNIQUE NOT NULL,
            `wab_score` DECIMAL(5,2) DEFAULT 0.00,
            `severity_level` ENUM('Mild', 'Moderate', 'Severe', 'Very Severe') DEFAULT 'Moderate',
            `aphasia_type` VARCHAR(100),
            `preferred_language` VARCHAR(10) DEFAULT 'en',
            `assigned_clinician_id` VARCHAR(50),
            `medical_history` TEXT,
            `therapy_start_date` DATE,
            `notes` TEXT,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
            FOREIGN KEY (`assigned_clinician_id`) REFERENCES `users`(`user_id`) ON DELETE SET NULL,
            INDEX `idx_severity` (`severity_level`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # Therapy sessions table
        """
        CREATE TABLE IF NOT EXISTS `therapy_sessions` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `session_id` VARCHAR(50) UNIQUE NOT NULL,
            `patient_id` VARCHAR(50) NOT NULL,
            `session_type` ENUM('sentence', 'picture', 'assessment') NOT NULL,
            `language` VARCHAR(10) NOT NULL,
            `difficulty` ENUM('easy', 'medium', 'hard') DEFAULT 'easy',
            `start_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `end_time` TIMESTAMP NULL,
            `duration_seconds` INT,
            `total_exercises` INT DEFAULT 0,
            `completed_exercises` INT DEFAULT 0,
            `average_accuracy` DECIMAL(5,2) DEFAULT 0.00,
            `wab_score` DECIMAL(5,2),
            `session_notes` TEXT,
            FOREIGN KEY (`patient_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
            INDEX `idx_session_id` (`session_id`),
            INDEX `idx_patient_id` (`patient_id`),
            INDEX `idx_session_type` (`session_type`),
            INDEX `idx_start_time` (`start_time`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # Exercise attempts table
        """
        CREATE TABLE IF NOT EXISTS `exercise_attempts` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `attempt_id` VARCHAR(50) UNIQUE NOT NULL,
            `session_id` VARCHAR(50) NOT NULL,
            `patient_id` VARCHAR(50) NOT NULL,
            `exercise_type` ENUM('sentence', 'picture') NOT NULL,
            `target_text` TEXT NOT NULL,
            `transcription` TEXT,
            `accuracy` DECIMAL(5,2) DEFAULT 0.00,
            `wab_score` DECIMAL(5,2),
            `severity_level` VARCHAR(50),
            `feedback` TEXT,
            `word_corrections` JSON,
            `practice_suggestions` JSON,
            `audio_file_path` VARCHAR(500),
            `attempt_number` INT DEFAULT 1,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (`session_id`) REFERENCES `therapy_sessions`(`session_id`) ON DELETE CASCADE,
            FOREIGN KEY (`patient_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
            INDEX `idx_attempt_id` (`attempt_id`),
            INDEX `idx_session_id` (`session_id`),
            INDEX `idx_patient_id` (`patient_id`),
            INDEX `idx_accuracy` (`accuracy`),
            INDEX `idx_created_at` (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # Picture exercises table
        """
        CREATE TABLE IF NOT EXISTS `picture_exercises` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `picture_id` VARCHAR(50) UNIQUE NOT NULL,
            `picture_name` VARCHAR(255) NOT NULL,
            `picture_url` VARCHAR(500) NOT NULL,
            `target_text_en` VARCHAR(255),
            `target_text_hi` VARCHAR(255),
            `target_text_kn` VARCHAR(255),
            `difficulty` ENUM('easy', 'medium', 'hard') DEFAULT 'easy',
            `category` VARCHAR(100),
            `is_active` BOOLEAN DEFAULT TRUE,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX `idx_picture_id` (`picture_id`),
            INDEX `idx_difficulty` (`difficulty`),
            INDEX `idx_category` (`category`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # Sentence exercises table
        """
        CREATE TABLE IF NOT EXISTS `sentence_exercises` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `sentence_id` VARCHAR(50) UNIQUE NOT NULL,
            `text_en` TEXT,
            `text_hi` TEXT,
            `text_kn` TEXT,
            `difficulty` ENUM('easy', 'medium', 'hard') DEFAULT 'easy',
            `category` VARCHAR(100),
            `target_words` JSON,
            `is_active` BOOLEAN DEFAULT TRUE,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX `idx_sentence_id` (`sentence_id`),
            INDEX `idx_difficulty` (`difficulty`),
            INDEX `idx_category` (`category`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # Patient progress table
        """
        CREATE TABLE IF NOT EXISTS `patient_progress` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `patient_id` VARCHAR(50) NOT NULL,
            `date` DATE NOT NULL,
            `sessions_completed` INT DEFAULT 0,
            `total_exercises` INT DEFAULT 0,
            `average_accuracy` DECIMAL(5,2) DEFAULT 0.00,
            `wab_score` DECIMAL(5,2),
            `severity_level` VARCHAR(50),
            `streak_days` INT DEFAULT 0,
            `notes` TEXT,
            FOREIGN KEY (`patient_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
            INDEX `idx_patient_id` (`patient_id`),
            INDEX `idx_date` (`date`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # User difficulty progress table
        """
        CREATE TABLE IF NOT EXISTS `user_difficulty_progress` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `patient_id` VARCHAR(50) NOT NULL,
            `language` VARCHAR(10) NOT NULL,
            `easy_completed` INT DEFAULT 0,
            `medium_completed` INT DEFAULT 0,
            `hard_completed` INT DEFAULT 0,
            `current_difficulty` ENUM('easy', 'medium', 'hard') DEFAULT 'easy',
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (`patient_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
            INDEX `idx_patient_id` (`patient_id`),
            INDEX `idx_language` (`language`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # Clinician notes table
        """
        CREATE TABLE IF NOT EXISTS `clinician_notes` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `note_id` VARCHAR(50) UNIQUE NOT NULL,
            `patient_id` VARCHAR(50) NOT NULL,
            `clinician_id` VARCHAR(50) NOT NULL,
            `session_id` VARCHAR(50),
            `note_type` ENUM('assessment', 'progress', 'recommendation', 'other') DEFAULT 'other',
            `title` VARCHAR(255),
            `content` TEXT NOT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (`patient_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
            FOREIGN KEY (`clinician_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
            FOREIGN KEY (`session_id`) REFERENCES `therapy_sessions`(`session_id`) ON DELETE SET NULL,
            INDEX `idx_note_id` (`note_id`),
            INDEX `idx_patient_id` (`patient_id`),
            INDEX `idx_created_at` (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # Assessment results table
        """
        CREATE TABLE IF NOT EXISTS `assessment_results` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `assessment_id` VARCHAR(50) UNIQUE NOT NULL,
            `patient_id` VARCHAR(50) NOT NULL,
            `wab_score` DECIMAL(5,2) NOT NULL,
            `severity_level` VARCHAR(50) NOT NULL,
            `detailed_scores` JSON,
            `recommendations` TEXT,
            `assessed_by` VARCHAR(50),
            `assessment_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (`patient_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
            FOREIGN KEY (`assessed_by`) REFERENCES `users`(`user_id`) ON DELETE SET NULL,
            INDEX `idx_assessment_id` (`assessment_id`),
            INDEX `idx_patient_id` (`patient_id`),
            INDEX `idx_assessment_date` (`assessment_date`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # Lip animation exercises table
        """
        CREATE TABLE IF NOT EXISTS `lip_animation_exercises` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `exercise_id` VARCHAR(50) UNIQUE NOT NULL,
            `word_en` VARCHAR(255),
            `word_hi` VARCHAR(255),
            `word_kn` VARCHAR(255),
            `phonemes_en` JSON,
            `phonemes_hi` JSON,
            `phonemes_kn` JSON,
            `visemes_en` JSON,
            `visemes_hi` JSON,
            `visemes_kn` JSON,
            `difficulty` ENUM('easy', 'medium', 'hard') DEFAULT 'easy',
            `category` VARCHAR(100),
            `video_path_en` VARCHAR(500),
            `video_path_hi` VARCHAR(500),
            `video_path_kn` VARCHAR(500),
            `audio_path_en` VARCHAR(500),
            `audio_path_hi` VARCHAR(500),
            `audio_path_kn` VARCHAR(500),
            `is_active` BOOLEAN DEFAULT TRUE,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX `idx_exercise_id` (`exercise_id`),
            INDEX `idx_difficulty` (`difficulty`),
            INDEX `idx_category` (`category`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # Lip animation attempts table
        """
        CREATE TABLE IF NOT EXISTS `lip_animation_attempts` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `attempt_id` VARCHAR(50) UNIQUE NOT NULL,
            `exercise_id` VARCHAR(50) NOT NULL,
            `patient_id` VARCHAR(50) NOT NULL,
            `session_id` VARCHAR(50),
            `language` VARCHAR(10) NOT NULL,
            `target_word` VARCHAR(255) NOT NULL,
            `transcription` TEXT,
            `accuracy` DECIMAL(5,2) DEFAULT 0.00,
            `lip_sync_score` DECIMAL(5,2) DEFAULT 0.00,
            `mouth_tracking_data` JSON,
            `phoneme_accuracy` JSON,
            `viseme_accuracy` JSON,
            `errors_detected` JSON,
            `feedback` TEXT,
            `video_recording_path` VARCHAR(500),
            `audio_recording_path` VARCHAR(500),
            `attempt_number` INT DEFAULT 1,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (`exercise_id`) REFERENCES `lip_animation_exercises`(`exercise_id`) ON DELETE CASCADE,
            FOREIGN KEY (`patient_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
            FOREIGN KEY (`session_id`) REFERENCES `therapy_sessions`(`session_id`) ON DELETE CASCADE,
            INDEX `idx_attempt_id` (`attempt_id`),
            INDEX `idx_exercise_id` (`exercise_id`),
            INDEX `idx_patient_id` (`patient_id`),
            INDEX `idx_created_at` (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    ]
    
    try:
        conn = get_connection(DB_NAME)
        cursor = conn.cursor()
        
        for i, sql in enumerate(sql_statements, 1):
            cursor.execute(sql)
            print(f"   ✓ Table {i}/{len(sql_statements)} created")
        
        cursor.close()
        conn.close()
        print("✅ All tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main initialization"""
    try:
        # Create database
        if not create_database():
            return False
        
        # Create tables
        if not create_tables():
            return False
        
        print("\n" + "=" * 70)
        print("✅ DATABASE INITIALIZATION COMPLETE!")
        print("=" * 70)
        print("\n📊 Summary:")
        print("   ✓ Database created/verified")
        print("   ✓ All 11 tables created")
        print("   ✓ Ready for use")
        print("\n🚀 Next Steps:")
        print("   1. Restart the backend server")
        print("   2. Try registering a new user")
        print("\n" + "=" * 70)
        return True
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
