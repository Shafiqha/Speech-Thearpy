"""
Initialize Database with SQLAlchemy
Alternative to running schema.sql manually
"""

import sys
from database import Base, engine, get_db_context, init_db
from database.models import PictureExercise, SentenceExercise
import json

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def insert_sample_exercises():
    """Insert sample picture and sentence exercises"""
    print("\nInserting sample exercises...")
    
    # Picture exercises data
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
        {'picture_id': 'pic_006', 'picture_name': 'Book', 'picture_url': '/images/exercises/book.jpg',
         'target_text_en': 'book', 'target_text_hi': 'किताब', 'target_text_kn': 'ಪುಸ್ತಕ',
         'difficulty': 'easy', 'category': 'Objects'},
        {'picture_id': 'pic_007', 'picture_name': 'Chair', 'picture_url': '/images/exercises/chair.jpg',
         'target_text_en': 'chair', 'target_text_hi': 'कुर्सी', 'target_text_kn': 'ಕುರ್ಚಿ',
         'difficulty': 'medium', 'category': 'Furniture'},
        {'picture_id': 'pic_008', 'picture_name': 'Table', 'picture_url': '/images/exercises/table.jpg',
         'target_text_en': 'table', 'target_text_hi': 'मेज़', 'target_text_kn': 'ಮೇಜು',
         'difficulty': 'medium', 'category': 'Furniture'},
        {'picture_id': 'pic_009', 'picture_name': 'Flower', 'picture_url': '/images/exercises/flower.jpg',
         'target_text_en': 'flower', 'target_text_hi': 'फूल', 'target_text_kn': 'ಹೂವು',
         'difficulty': 'medium', 'category': 'Nature'},
        {'picture_id': 'pic_010', 'picture_name': 'Tree', 'picture_url': '/images/exercises/tree.jpg',
         'target_text_en': 'tree', 'target_text_hi': 'पेड़', 'target_text_kn': 'ಮರ',
         'difficulty': 'medium', 'category': 'Nature'},
    ]
    
    # Sentence exercises data
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
        {'sentence_id': 'sent_003',
         'text_en': 'What is your name?',
         'text_hi': 'आपका नाम क्या है?',
         'text_kn': 'ನಿಮ್ಮ ಹೆಸರೇನು?',
         'difficulty': 'easy', 'category': 'Greetings',
         'target_words': json.dumps(['what', 'name'])},
        {'sentence_id': 'sent_004',
         'text_en': 'I need water.',
         'text_hi': 'मुझे पानी चाहिए।',
         'text_kn': 'ನನಗೆ ನೀರು ಬೇಕು.',
         'difficulty': 'easy', 'category': 'Daily Needs',
         'target_words': json.dumps(['need', 'water'])},
        {'sentence_id': 'sent_005',
         'text_en': 'Please help me.',
         'text_hi': 'कृपया मेरी मदद करें।',
         'text_kn': 'ದಯವಿಟ್ಟು ನನಗೆ ಸಹಾಯ ಮಾಡಿ.',
         'difficulty': 'easy', 'category': 'Daily Needs',
         'target_words': json.dumps(['please', 'help'])},
    ]
    
    try:
        with get_db_context() as db:
            # Insert picture exercises
            for pic_data in picture_exercises:
                pic = PictureExercise(**pic_data)
                db.add(pic)
            
            # Insert sentence exercises
            for sent_data in sentence_exercises:
                sent = SentenceExercise(**sent_data)
                db.add(sent)
            
            db.commit()
            print(f"✅ Inserted {len(picture_exercises)} picture exercises")
            print(f"✅ Inserted {len(sentence_exercises)} sentence exercises")
            return True
            
    except Exception as e:
        print(f"❌ Error inserting sample data: {e}")
        return False

def main():
    """Main initialization function"""
    print("=" * 60)
    print("🚀 Initializing Aphasia Therapy Database")
    print("=" * 60)
    
    # Step 1: Create tables
    if not create_tables():
        print("\n❌ Failed to create tables")
        return False
    
    # Step 2: Insert sample data
    if not insert_sample_exercises():
        print("\n❌ Failed to insert sample data")
        return False
    
    # Success
    print("\n" + "=" * 60)
    print("✅ DATABASE INITIALIZATION COMPLETE!")
    print("=" * 60)
    print("\n📊 Database Summary:")
    print("   • All tables created")
    print("   • 10 picture exercises loaded")
    print("   • 5 sentence exercises loaded")
    print("   • Ready for patient registration")
    print("\n🚀 Next Steps:")
    print("   1. Run: python test_db_connection.py")
    print("   2. Start backend: python api/main.py")
    print("   3. Start frontend: cd frontend && npm start")
    print("\n" + "=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("\nMake sure:")
        print("1. MySQL is running")
        print("2. .env file exists with correct credentials")
        print("3. Database 'aphasia_therapy_db' exists")
        sys.exit(1)
