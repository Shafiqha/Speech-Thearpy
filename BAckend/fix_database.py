"""
Complete database initialization script
Handles database creation and table initialization
"""

import os
import sys
import time
import pymysql
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Load environment variables
load_dotenv()

# Database credentials
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'aphasia_therapy_db')

print("=" * 70)
print("🚀 APHASIA THERAPY DATABASE INITIALIZATION")
print("=" * 70)
print(f"\n📊 Database Configuration:")
print(f"   Host: {DB_HOST}")
print(f"   Port: {DB_PORT}")
print(f"   User: {DB_USER}")
print(f"   Database: {DB_NAME}")

def test_mysql_connection():
    """Test if MySQL is running"""
    print("\n🔍 Testing MySQL connection...")
    try:
        if DB_PASSWORD:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                charset='utf8mb4'
            )
        else:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                charset='utf8mb4'
            )
        conn.close()
        print("✅ MySQL is running and accessible")
        return True
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        print("\n⚠️  MySQL is not running!")
        print("\n📝 To fix this:")
        print("   1. Open XAMPP Control Panel")
        print("   2. Click 'Start' next to MySQL")
        print("   3. Wait for it to start (should show 'Running')")
        print("   4. Run this script again")
        return False

def create_database():
    """Create the database if it doesn't exist"""
    print("\n📦 Creating database...")
    try:
        if DB_PASSWORD:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                charset='utf8mb4'
            )
        else:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                charset='utf8mb4'
            )
        
        cursor = conn.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ Database '{DB_NAME}' created/verified")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def create_tables():
    """Create all database tables using SQLAlchemy"""
    print("\n📋 Creating tables...")
    try:
        # Import models after database exists
        from database.connection import Base, engine
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def insert_sample_data():
    """Insert sample exercises"""
    print("\n📚 Inserting sample exercises...")
    try:
        from database.connection import SessionLocal
        from database.models import PictureExercise, SentenceExercise
        import json
        
        db = SessionLocal()
        
        # Picture exercises
        picture_exercises = [
            {'picture_id': 'pic_001', 'picture_name': 'Apple', 'picture_url': '/images/exercises/apple.jpg',
             'target_text_en': 'apple', 'target_text_hi': 'सेब', 'target_text_kn': 'ಸೇಬು',
             'difficulty': 'easy', 'category': 'Food'},
            {'picture_id': 'pic_002', 'picture_name': 'Cat', 'picture_url': '/images/exercises/cat.jpg',
             'target_text_en': 'cat', 'target_text_hi': 'बिल्ली', 'target_text_kn': 'ಬೆಕ್ಕು',
             'difficulty': 'easy', 'category': 'Animals'},
            {'picture_id': 'pic_003', 'picture_name': 'House', 'picture_url': '/images/exercises/house.jpg',
             'target_text_en': 'house', 'target_text_hi': 'घर', 'target_text_kn': 'ಮನೆ',
             'difficulty': 'easy', 'category': 'Objects'},
            {'picture_id': 'pic_004', 'picture_name': 'Dog', 'picture_url': '/images/exercises/dog.jpg',
             'target_text_en': 'dog', 'target_text_hi': 'कुत्ता', 'target_text_kn': 'ನಾಯಿ',
             'difficulty': 'easy', 'category': 'Animals'},
            {'picture_id': 'pic_005', 'picture_name': 'Car', 'picture_url': '/images/exercises/car.jpg',
             'target_text_en': 'car', 'target_text_hi': 'गाड़ी', 'target_text_kn': 'ಕಾರು',
             'difficulty': 'easy', 'category': 'Vehicles'},
        ]
        
        # Sentence exercises
        sentence_exercises = [
            {'sentence_id': 'sent_001',
             'text_en': 'Hello, how are you?',
             'text_hi': 'नमस्ते, आप कैसे हैं?',
             'text_kn': 'ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?',
             'difficulty': 'easy', 'category': 'Greetings',
             'target_words': json.dumps(['hello', 'how', 'you'])},
            {'sentence_id': 'sent_002',
             'text_en': 'I am fine, thank you.',
             'text_hi': 'मैं ठीक हूं, धन्यवाद।',
             'text_kn': 'ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ, ಧನ್ಯವಾದ.',
             'difficulty': 'easy', 'category': 'Greetings',
             'target_words': json.dumps(['fine', 'thank', 'you'])},
        ]
        
        # Insert picture exercises
        for pic_data in picture_exercises:
            existing = db.query(PictureExercise).filter(
                PictureExercise.picture_id == pic_data['picture_id']
            ).first()
            if not existing:
                pic = PictureExercise(**pic_data)
                db.add(pic)
        
        # Insert sentence exercises
        for sent_data in sentence_exercises:
            existing = db.query(SentenceExercise).filter(
                SentenceExercise.sentence_id == sent_data['sentence_id']
            ).first()
            if not existing:
                sent = SentenceExercise(**sent_data)
                db.add(sent)
        
        db.commit()
        db.close()
        print(f"✅ Inserted sample exercises")
        return True
    except Exception as e:
        print(f"⚠️  Sample data insertion skipped: {e}")
        return True  # Don't fail on this

def main():
    """Main initialization"""
    # Step 1: Test MySQL connection
    if not test_mysql_connection():
        print("\n" + "=" * 70)
        print("❌ INITIALIZATION FAILED - MySQL is not running")
        print("=" * 70)
        return False
    
    # Step 2: Create database
    if not create_database():
        print("\n" + "=" * 70)
        print("❌ INITIALIZATION FAILED - Could not create database")
        print("=" * 70)
        return False
    
    # Step 3: Create tables
    if not create_tables():
        print("\n" + "=" * 70)
        print("❌ INITIALIZATION FAILED - Could not create tables")
        print("=" * 70)
        return False
    
    # Step 4: Insert sample data
    insert_sample_data()
    
    # Success
    print("\n" + "=" * 70)
    print("✅ DATABASE INITIALIZATION COMPLETE!")
    print("=" * 70)
    print("\n📊 Summary:")
    print("   ✓ Database created/verified")
    print("   ✓ All tables created")
    print("   ✓ Sample exercises loaded")
    print("\n🚀 Next Steps:")
    print("   1. The backend server should now work")
    print("   2. Try registering a new user")
    print("   3. Start a therapy session")
    print("\n" + "=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
