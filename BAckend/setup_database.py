"""
Database Setup Script for XAMPP MySQL
Creates database and all tables for Aphasia Therapy System
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymysql
from sqlalchemy import create_engine, text
from database.config import DB_CONFIG
from database.connection import Base, engine, test_connection, init_db
from database.models import (
    User, PatientProfile, TherapySession, ExerciseAttempt,
    PictureExercise, SentenceExercise, PatientProgress,
    ClinicianNote, AssessmentResult, LipAnimationExercise,
    LipAnimationAttempt
)

def create_database():
    """Create the database if it doesn't exist"""
    print("\n" + "="*70)
    print("🔧 SETTING UP DATABASE FOR XAMPP MYSQL")
    print("="*70 + "\n")
    
    # Connect to MySQL without database
    connection_string = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
    
    try:
        temp_engine = create_engine(connection_string)
        with temp_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SHOW DATABASES LIKE '{DB_CONFIG['database']}'"))
            exists = result.fetchone() is not None
            
            if not exists:
                print(f"📦 Creating database: {DB_CONFIG['database']}")
                conn.execute(text(f"CREATE DATABASE {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                conn.commit()
                print(f"✅ Database '{DB_CONFIG['database']}' created successfully")
            else:
                print(f"✅ Database '{DB_CONFIG['database']}' already exists")
        
        temp_engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        print(f"\n⚠️ Make sure XAMPP MySQL is running!")
        print(f"   - Start XAMPP Control Panel")
        print(f"   - Click 'Start' for MySQL")
        print(f"   - Check that MySQL is running on port {DB_CONFIG['port']}")
        return False

def create_tables():
    """Create all tables"""
    print(f"\n📋 Creating tables...")
    
    try:
        # Test connection first
        if not test_connection():
            print("❌ Cannot connect to database")
            return False
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            
            print(f"\n✅ Successfully created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def insert_sample_data():
    """Insert sample data for testing"""
    print(f"\n📝 Inserting sample data...")
    
    try:
        from database.connection import SessionLocal
        from datetime import datetime, date
        import uuid
        
        db = SessionLocal()
        
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"✅ Sample data already exists ({existing_users} users)")
            db.close()
            return True
        
        # Create sample patient
        patient = User(
            user_id=f"patient_{uuid.uuid4().hex[:8]}",
            email="patient@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6q0OXm",  # password: demo123
            name="John Doe",
            user_type="patient",
            phone="+91-9876543210",
            date_of_birth=date(1980, 1, 1),
            gender="male",
            is_active=True
        )
        db.add(patient)
        db.flush()
        
        # Create patient profile
        profile = PatientProfile(
            user_id=patient.user_id,
            wab_score=65.50,
            severity_level="Moderate",
            aphasia_type="Broca's Aphasia",
            preferred_language="en",
            therapy_start_date=date.today(),
            notes="Sample patient for testing"
        )
        db.add(profile)
        
        # Create sample clinician
        clinician = User(
            user_id=f"clinician_{uuid.uuid4().hex[:8]}",
            email="clinician@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6q0OXm",  # password: demo123
            name="Dr. Sarah Smith",
            user_type="clinician",
            phone="+91-9876543211",
            is_active=True
        )
        db.add(clinician)
        
        # Create sample exercises
        exercises = [
            SentenceExercise(
                sentence_id=f"sent_{uuid.uuid4().hex[:8]}",
                text_en="The cat is on the mat",
                text_hi="बिल्ली चटाई पर है",
                text_kn="ಬೆಕ್ಕು ಚಾಪೆಯ ಮೇಲಿದೆ",
                difficulty="easy",
                category="animals",
                is_active=True
            ),
            SentenceExercise(
                sentence_id=f"sent_{uuid.uuid4().hex[:8]}",
                text_en="I want to drink water",
                text_hi="मुझे पानी पीना है",
                text_kn="ನನಗೆ ನೀರು ಕುಡಿಯಬೇಕು",
                difficulty="easy",
                category="daily_needs",
                is_active=True
            ),
            SentenceExercise(
                sentence_id=f"sent_{uuid.uuid4().hex[:8]}",
                text_en="Good morning, how are you?",
                text_hi="सुप्रभात, आप कैसे हैं?",
                text_kn="ಶುಭೋದಯ, ನೀವು ಹೇಗಿದ್ದೀರಿ?",
                difficulty="medium",
                category="greetings",
                is_active=True
            )
        ]
        
        for exercise in exercises:
            db.add(exercise)
        
        # Create sample picture exercises
        pictures = [
            PictureExercise(
                picture_id=f"pic_{uuid.uuid4().hex[:8]}",
                picture_name="Apple",
                picture_url="/images/apple.jpg",
                target_text_en="apple",
                target_text_hi="सेब",
                target_text_kn="ಸೇಬು",
                difficulty="easy",
                category="fruits",
                is_active=True
            ),
            PictureExercise(
                picture_id=f"pic_{uuid.uuid4().hex[:8]}",
                picture_name="Water",
                picture_url="/images/water.jpg",
                target_text_en="water",
                target_text_hi="पानी",
                target_text_kn="ನೀರು",
                difficulty="easy",
                category="daily_items",
                is_active=True
            )
        ]
        
        for picture in pictures:
            db.add(picture)
        
        # Create sample lip animation exercises
        lip_exercises = [
            LipAnimationExercise(
                exercise_id=f"lip_{uuid.uuid4().hex[:8]}",
                word_en="hello",
                word_hi="नमस्ते",
                word_kn="ನಮಸ್ಕಾರ",
                difficulty="easy",
                category="greetings",
                is_active=True
            ),
            LipAnimationExercise(
                exercise_id=f"lip_{uuid.uuid4().hex[:8]}",
                word_en="water",
                word_hi="पानी",
                word_kn="ನೀರು",
                difficulty="easy",
                category="daily_needs",
                is_active=True
            )
        ]
        
        for lip_ex in lip_exercises:
            db.add(lip_ex)
        
        db.commit()
        print(f"✅ Sample data inserted successfully")
        print(f"   - 2 users (1 patient, 1 clinician)")
        print(f"   - 3 sentence exercises")
        print(f"   - 2 picture exercises")
        print(f"   - 2 lip animation exercises")
        print(f"\n📧 Login credentials:")
        print(f"   Patient: patient@example.com / demo123")
        print(f"   Clinician: clinician@example.com / demo123")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error inserting sample data: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_setup():
    """Verify database setup"""
    print(f"\n🔍 Verifying database setup...")
    
    try:
        from database.connection import SessionLocal
        
        db = SessionLocal()
        
        # Count records
        user_count = db.query(User).count()
        session_count = db.query(TherapySession).count()
        exercise_count = db.query(SentenceExercise).count()
        picture_count = db.query(PictureExercise).count()
        lip_count = db.query(LipAnimationExercise).count()
        
        print(f"\n✅ Database verification successful:")
        print(f"   - Users: {user_count}")
        print(f"   - Therapy Sessions: {session_count}")
        print(f"   - Sentence Exercises: {exercise_count}")
        print(f"   - Picture Exercises: {picture_count}")
        print(f"   - Lip Animation Exercises: {lip_count}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main setup function"""
    print("\n" + "="*70)
    print("🚀 XAMPP MySQL DATABASE SETUP")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Host: {DB_CONFIG['host']}")
    print(f"  Port: {DB_CONFIG['port']}")
    print(f"  User: {DB_CONFIG['user']}")
    print(f"  Database: {DB_CONFIG['database']}")
    print("="*70)
    
    # Step 1: Create database
    if not create_database():
        print("\n❌ Setup failed at database creation")
        return False
    
    # Step 2: Create tables
    if not create_tables():
        print("\n❌ Setup failed at table creation")
        return False
    
    # Step 3: Insert sample data
    if not insert_sample_data():
        print("\n⚠️ Warning: Sample data insertion failed (optional)")
    
    # Step 4: Verify setup
    if not verify_setup():
        print("\n⚠️ Warning: Verification failed")
    
    print("\n" + "="*70)
    print("✅ DATABASE SETUP COMPLETE!")
    print("="*70)
    print(f"\n📊 Access phpMyAdmin at: http://localhost/phpmyadmin")
    print(f"   Database: {DB_CONFIG['database']}")
    print(f"\n🌐 Your website can now connect to the database")
    print(f"   Connection string: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
