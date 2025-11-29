#!/usr/bin/env python3
"""
New FastAPI Backend using exact interactive_therapy.py functions
Supports multilingual (English, Hindi, Kannada) speech therapy
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from fastapi.responses import StreamingResponse
import os
import sys
import tempfile
import shutil
from datetime import datetime
import uuid
import librosa
import torch
import io
import base64


# Add parent directory to path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.interactive_therapy import InteractiveSpeechTherapy, TherapySentence
from core.initial_assessment import initial_assessment, SeverityLevel, AssessmentResult
from services.advanced_asr import get_advanced_asr_service

# Import lip animation routes
from api.lip_animation_routes import router as lip_animation_router

# Import database routes
from api.database_routes import router as database_router

# Import database models and connection
from database import get_db
from database.models import UserDifficultyProgress, TherapySession as DBTherapySession, ExerciseAttempt as DBExerciseAttempt, PatientProgress as DBPatientProgress
from sqlalchemy.orm import Session

# Define WordCorrection class early for type hints
class WordCorrection(BaseModel):
    word: str
    position: int
    issue: str
    correction: str
    pronunciation_tip: str

# TTS imports
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title="Multilingual Speech Therapy API",
    description="Complete speech therapy system using interactive_therapy.py functions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static media files FIRST (before routes)
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Get the correct media directory path (relative to where files are actually saved)
current_dir = Path(__file__).parent
media_dir = current_dir / "media"

# Create media directories if they don't exist
os.makedirs(str(media_dir / "lip_animations"), exist_ok=True)
os.makedirs(str(media_dir / "lip_audio"), exist_ok=True)
os.makedirs(str(media_dir / "mouth_shapes"), exist_ok=True)

print(f"📁 Serving media files from: {media_dir}")
print(f"📁 Absolute path: {media_dir.absolute()}")

# NOTE: Using direct file serving routes instead of mount
# app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

# IMPORTANT: Define direct file serving routes BEFORE including router
from fastapi.responses import FileResponse

@app.get("/media/lip_animations/{filename}")
async def serve_video_direct(filename: str):
    """Serve video files directly"""
    file_path = media_dir / "lip_animations" / filename
    print(f"🎬 Video request: {filename}")
    print(f"📁 Looking for: {file_path}")
    print(f"✅ Exists: {file_path.exists()}")
    
    if file_path.exists():
        print(f"✅ Serving video: {file_path}")
        return FileResponse(
            path=str(file_path),
            media_type="video/mp4",
            filename=filename,
            headers={
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*"
            }
        )
    print(f"❌ Video not found: {file_path}")
    return {"error": "File not found", "path": str(file_path), "exists": False}

@app.get("/media/lip_audio/{filename}")
async def serve_audio_direct(filename: str):
    """Serve audio files directly"""
    file_path = media_dir / "lip_audio" / filename
    print(f"🔊 Audio request: {filename}")
    print(f"📁 Looking for: {file_path}")
    
    if file_path.exists():
        print(f"✅ Serving audio: {file_path}")
        return FileResponse(
            path=str(file_path),
            media_type="audio/mpeg",
            filename=filename
        )
    print(f"❌ Audio not found: {file_path}")
    return {"error": "File not found", "path": str(file_path), "exists": False}

# Include lip animation routes AFTER defining media routes
app.include_router(lip_animation_router)

# Include database routes
app.include_router(database_router)

# Add a test endpoint to verify media serving
@app.get("/test-media")
async def test_media():
    """Test if media directory is accessible"""
    import os
    video_files = []
    audio_files = []
    
    video_dir = media_dir / "lip_animations"
    audio_dir = media_dir / "lip_audio"
    
    if video_dir.exists():
        video_files = [f.name for f in video_dir.glob("*.mp4")]
    if audio_dir.exists():
        audio_files = [f.name for f in audio_dir.glob("*.mp3")]
    
    return {
        "media_dir": str(media_dir.absolute()),
        "video_dir": str(video_dir.absolute()),
        "audio_dir": str(audio_dir.absolute()),
        "video_files": video_files[:5],  # First 5
        "audio_files": audio_files[:5],
        "total_videos": len(video_files),
        "total_audios": len(audio_files)
    }

# Duplicate routes removed - using the ones defined above

# Global therapy system instance
therapy_system = None
advanced_asr = None

# Configuration
USE_ADVANCED_ASR = True  # Set to True to use your trained model
ADVANCED_ASR_MODEL_PATH = "models/trained_asr_model.pth"  # Path to your trained model

def romanize_hindi(hindi_text: str) -> str:
    """Convert Hindi text to romanized (English) equivalent"""
    
    # Common Hindi to Roman mappings
    hindi_to_roman = {
        'नमस्ते': 'namaste',
        'धन्यवाद': 'dhanyawad', 
        'हाँ': 'haan',
        'नहीं': 'nahin',
        'पानी': 'paani',
        'खाना': 'khaana',
        'अच्छा': 'accha',
        'बुरा': 'bura',
        'घर': 'ghar',
        'काम': 'kaam',
        'समय': 'samay',
        'दिन': 'din',
        'रात': 'raat',
        'सुबह': 'subah',
        'शाम': 'shaam',
        'मैं': 'main',
        'तुम': 'tum',
        'वह': 'vah',
        'यह': 'yah',
        'कहाँ': 'kahan',
        'कब': 'kab',
        'क्यों': 'kyon',
        'कैसे': 'kaise',
        'क्या': 'kya'
    }
    
    # Direct mapping if available
    if hindi_text in hindi_to_roman:
        return hindi_to_roman[hindi_text]
    
    # For words not in mapping, try basic transliteration
    return hindi_text.lower()

def romanize_kannada(kannada_text: str) -> str:
    """Convert Kannada text to romanized (English) equivalent"""
    
    # Common Kannada to Roman mappings
    kannada_to_roman = {
        'ನಮಸ್ಕಾರ': 'namaskara',
        'ಧನ್ಯವಾದ': 'dhanyavaada',
        'ಹೌದು': 'haudu',
        'ಇಲ್ಲ': 'illa',
        'ನೀರು': 'neeru',
        'ಅನ್ನ': 'anna',
        'ಮನೆ': 'mane',
        'ಕೆಲಸ': 'kelasa',
        'ಸಮಯ': 'samaya',
        'ದಿನ': 'dina',
        'ರಾತ್ರಿ': 'raatri',
        'ಬೆಳಿಗ್ಗೆ': 'beligge',
        'ಸಂಜೆ': 'sanje',
        'ನಾನು': 'naanu',
        'ನೀನು': 'neenu',
        'ಅವನು': 'avanu',
        'ಅವಳು': 'avalu',
        'ಇದು': 'idu',
        'ಅದು': 'adu',
        'ಎಲ್ಲಿ': 'elli',
        'ಯಾವಾಗ': 'yaavaaga',
        'ಏಕೆ': 'yeke',
        'ಹೇಗೆ': 'hege',
        'ಏನು': 'yenu',
        'ಒಳ್ಳೆಯದು': 'olleyadu',
        'ಕೆಟ್ಟದು': 'kettadu'
    }
    
    # Direct mapping if available
    if kannada_text in kannada_to_roman:
        return kannada_to_roman[kannada_text]
    
    # For words not in mapping, try basic transliteration
    return kannada_text.lower()

def generate_language_feedback(accuracy: float, language: str, target: str, transcription: str) -> str:
    """Generate feedback in the target language"""
    
    if language == "hi":
        # Hindi feedback
        if accuracy >= 90:
            return "बहुत अच्छा! उच्चारण बिल्कुल सही है।"  # Very good! Pronunciation is perfect
        elif accuracy >= 70:
            return "अच्छा! थोड़ा और अभ्यास करें।"  # Good! Practice a little more
        elif accuracy >= 50:
            return "ठीक है। और अभ्यास की जरूरत है।"  # Okay. More practice needed
        else:
            return "अभ्यास जारी रखें। आप बेहतर कर सकते हैं।"  # Keep practicing. You can do better
    
    elif language == "kn":
        # Kannada feedback  
        if accuracy >= 90:
            return "ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ! ಉಚ್ಚಾರಣೆ ಸರಿಯಾಗಿದೆ।"  # Very good! Pronunciation is correct
        elif accuracy >= 70:
            return "ಚೆನ್ನಾಗಿದೆ! ಇನ್ನೂ ಸ್ವಲ್ಪ ಅಭ್ಯಾಸ ಮಾಡಿ।"  # Good! Practice a little more
        elif accuracy >= 50:
            return "ಸರಿ. ಇನ್ನೂ ಅಭ್ಯಾಸದ ಅವಶ್ಯಕತೆ ಇದೆ।"  # Okay. More practice needed
        else:
            return "ಅಭ್ಯಾಸ ಮುಂದುವರಿಸಿ. ನೀವು ಉತ್ತಮವಾಗಿ ಮಾಡಬಹುದು।"  # Keep practicing. You can do better
    
    else:
        # English feedback
        if accuracy >= 90:
            return "Excellent pronunciation!"
        elif accuracy >= 70:
            return "Good job! Minor improvements needed."
        elif accuracy >= 50:
            return "Fair attempt. More practice needed."
        else:
            return "Keep practicing. You can do better."

def generate_word_corrections(target: str, transcription: str, language: str) -> List[WordCorrection]:
    """Generate detailed word-level corrections"""
    
    corrections = []
    
    if not transcription.strip():
        # No transcription - provide guidance for each word
        target_words = target.split()
        for i, word in enumerate(target_words):
            corrections.append(WordCorrection(
                word=word,
                position=i,
                issue="Not detected",
                correction=f"Say '{word}' clearly",
                pronunciation_tip=get_pronunciation_tip(word, language)
            ))
        return corrections
    
    # Split into words for comparison
    target_words = target.split()
    transcribed_words = transcription.split()
    
    # Use simple word alignment
    max_len = max(len(target_words), len(transcribed_words))
    
    for i in range(max_len):
        target_word = target_words[i] if i < len(target_words) else ""
        transcribed_word = transcribed_words[i] if i < len(transcribed_words) else ""
        
        if not target_word:
            continue
            
        # Check if word needs correction
        if not transcribed_word:
            corrections.append(WordCorrection(
                word=target_word,
                position=i,
                issue="Missing word",
                correction=f"Add '{target_word}'",
                pronunciation_tip=get_pronunciation_tip(target_word, language)
            ))
        elif target_word.lower() != transcribed_word.lower():
            # For Hindi and Kannada, also check romanized version
            if language == "hi":
                romanized_target = romanize_hindi(target_word)
                # Check both exact and fuzzy matches
                transcribed_lower = transcribed_word.lower()
                romanized_lower = romanized_target.lower()
                
                # Check if they're close enough (for NAMASTE vs namaste)
                if (romanized_lower not in transcribed_lower and 
                    transcribed_lower not in romanized_lower and
                    not are_similar_words(romanized_lower, transcribed_lower)):
                    corrections.append(WordCorrection(
                        word=target_word,
                        position=i,
                        issue=f"Pronounced as '{transcribed_word}'",
                        correction=f"Say '{target_word}' ({romanized_target})",
                        pronunciation_tip=get_pronunciation_tip(target_word, language)
                    ))
            elif language == "kn":
                romanized_target = romanize_kannada(target_word)
                # Check both exact and fuzzy matches
                transcribed_lower = transcribed_word.lower()
                romanized_lower = romanized_target.lower()
                
                # Check if they're close enough (for NAMASKARA vs namaskara)
                if (romanized_lower not in transcribed_lower and 
                    transcribed_lower not in romanized_lower and
                    not are_similar_words(romanized_lower, transcribed_lower)):
                    corrections.append(WordCorrection(
                        word=target_word,
                        position=i,
                        issue=f"Pronounced as '{transcribed_word}'",
                        correction=f"Say '{target_word}' ({romanized_target})",
                        pronunciation_tip=get_pronunciation_tip(target_word, language)
                    ))
            else:
                corrections.append(WordCorrection(
                    word=target_word,
                    position=i,
                    issue=f"Pronounced as '{transcribed_word}'",
                    correction=f"Say '{target_word}'",
                    pronunciation_tip=get_pronunciation_tip(target_word, language)
                ))
    
    return corrections

def are_similar_words(word1: str, word2: str, threshold: float = 0.7) -> bool:
    """Check if two words are similar enough (for fuzzy matching)"""
    
    # Simple similarity check
    if word1 == word2:
        return True
    
    # Check if one contains the other
    if word1 in word2 or word2 in word1:
        return True
    
    # Check character overlap
    set1, set2 = set(word1), set(word2)
    overlap = len(set1 & set2)
    total = len(set1 | set2)
    
    if total == 0:
        return False
    
    similarity = overlap / total
    return similarity >= threshold

def calculate_fuzzy_accuracy(target: str, transcription: str) -> float:
    """Calculate fuzzy accuracy for cross-language matching"""
    
    if not target or not transcription:
        return 0.0
    
    target_words = target.lower().split()
    transcribed_words = transcription.lower().split()
    
    if not target_words or not transcribed_words:
        return 0.0
    
    total_matches = 0
    total_words = len(target_words)
    
    for target_word in target_words:
        best_match = 0
        for transcribed_word in transcribed_words:
            if are_similar_words(target_word, transcribed_word, threshold=0.6):
                # Calculate character-level similarity
                set1, set2 = set(target_word), set(transcribed_word)
                overlap = len(set1 & set2)
                total_chars = len(set1 | set2)
                if total_chars > 0:
                    similarity = overlap / total_chars
                    best_match = max(best_match, similarity)
        
        total_matches += best_match
    
    return (total_matches / total_words) * 100

def get_pronunciation_tip(word: str, language: str) -> str:
    """Get pronunciation tips for specific words"""
    
    if language == "hi":
        # Hindi pronunciation tips
        tips = {
            'नमस्ते': 'Break it down: ना-मस्-ते (na-mas-te)',
            'धन्यवाद': 'Break it down: धन्-य-वाद (dhan-ya-waad)',
            'हाँ': 'Short sound: हाँ (haan) with nasal ending',
            'नहीं': 'Break it down: न-हीं (na-heen)',
            'पानी': 'Break it down: पा-नी (paa-nee)',
            'खाना': 'Break it down: खा-ना (khaa-na)',
        }
        return tips.get(word, f'Practice saying {word} slowly, syllable by syllable')
    
    elif language == "kn":
        # Kannada pronunciation tips
        tips = {
            'ನಮಸ್ಕಾರ': 'Break it down: ನ-ಮಸ್-ಕಾ-ರ (na-mas-kaa-ra)',
            'ಧನ್ಯವಾದ': 'Break it down: ಧನ್-ಯ-ವಾ-ದ (dhan-ya-vaa-da)',
            'ಹೌದು': 'Short sound: ಹೌ-ದು (hau-du)',
            'ಇಲ್ಲ': 'Break it down: ಇಲ್-ಲ (il-la)',
            'ನೀರು': 'Break it down: ನೀ-ರು (nee-ru)',
            'ಅನ್ನ': 'Short sound: ಅನ್-ನ (an-na)',
            'ಮನೆ': 'Break it down: ಮ-ನೆ (ma-ne)',
            'ಕೆಲಸ': 'Break it down: ಕೆ-ಲ-ಸ (ke-la-sa)',
            'ನಾನು': 'Break it down: ನಾ-ನು (naa-nu)',
            'ನೀನು': 'Break it down: ನೀ-ನು (nee-nu)',
            'ಒಳ್ಳೆಯದು': 'Break it down: ಒಳ್-ಳೆ-ಯ-ದು (ol-le-ya-du)',
        }
        return tips.get(word, f'Practice saying {word} slowly, syllable by syllable')
    
    else:
        # English pronunciation tips
        tips = {
            'hello': 'Emphasize the H sound: HEL-lo',
            'thank': 'TH sound with tongue between teeth: th-ank',
            'you': 'Long U sound: yooo',
            'good': 'Double O sound: g-ood',
            'morning': 'MOR-ning with clear R sound',
        }
        return tips.get(word.lower(), f'Practice saying {word} clearly, emphasizing each syllable')

def text_to_speech(text: str, language: str = "en") -> bytes:
    """Convert text to speech audio bytes"""
    
    if not text.strip():
        return b""
    
    print(f"🔊 Converting to speech: '{text}' (language: {language})")
    print(f"🔍 TTS Available: gTTS={GTTS_AVAILABLE}, pyttsx3={TTS_AVAILABLE}")
    
    # Try Google TTS first (better multilingual support)
    if GTTS_AVAILABLE:
        try:
            # Language mapping for gTTS
            lang_map = {
                "en": "en",
                "hi": "hi", 
                "kn": "kn"  # Kannada
            }
            
            tts_lang = lang_map.get(language, "en")
            print(f"🌐 Using gTTS with language: {tts_lang}")
            
            # Create TTS object
            tts = gTTS(text=text, lang=tts_lang, slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                print(f"📁 Saving TTS to: {tmp_path}")
                
            tts.save(tmp_path)
            print(f"✅ TTS file saved")
            
            # Read the audio file
            with open(tmp_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
            
            # Clean up
            os.unlink(tmp_path)
            
            print(f"✅ gTTS generated: {len(audio_bytes)} bytes")
            return audio_bytes
                
        except Exception as e:
            print(f"⚠️ gTTS failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to simple text response if TTS fails
    print("🔄 TTS failed, creating simple audio response")
    
    # Create a simple beep sound as fallback
    try:
        import numpy as np
        import soundfile as sf
        
        # Generate a simple tone
        sample_rate = 22050
        duration = 0.5
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_signal = np.sin(2 * np.pi * frequency * t) * 0.3
        
        # Save as WAV
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_signal, sample_rate)
            
            with open(tmp_file.name, 'rb') as audio_file:
                audio_bytes = audio_file.read()
            
            os.unlink(tmp_file.name)
            
        print(f"✅ Fallback audio generated: {len(audio_bytes)} bytes")
        return audio_bytes
        
    except Exception as e:
        print(f"❌ All TTS methods failed: {e}")
        return b""

def get_therapy_system(language: str = "en"):
    """Get or create the therapy system instance with language-specific models"""
    global therapy_system
    if therapy_system is None:
        therapy_system = InteractiveSpeechTherapy()
        therapy_system.load_models(language)
    elif therapy_system.asr_model is None or therapy_system.asr_processor is None:
        # Reload models if not loaded or if language changed
        therapy_system.load_models(language)
    return therapy_system

def get_advanced_asr():
    """Get or create the advanced ASR service"""
    global advanced_asr
    if advanced_asr is None and USE_ADVANCED_ASR:
        try:
            print("🚀 Initializing Advanced ASR Service...")
            advanced_asr = get_advanced_asr_service(ADVANCED_ASR_MODEL_PATH)
            if advanced_asr and advanced_asr.load_model():
                print("✅ Advanced ASR Service ready")
            else:
                print("⚠️ Advanced ASR failed to load, will use fallback")
                advanced_asr = None
        except Exception as e:
            print(f"❌ Advanced ASR initialization failed: {e}")
            import traceback
            traceback.print_exc()
            advanced_asr = None
    return advanced_asr

# Pydantic models for API responses
class SessionStartRequest(BaseModel):
    language: str = "en"
    difficulty: str = "easy"
    patient_id: Optional[str] = None

class AudioProcessingResult(BaseModel):
    transcription: str
    accuracy: float
    wab_score: float
    severity: str
    feedback: str
    detailed_errors: List[str] = []
    practice_suggestions: List[str] = []
    strengths: List[str] = []
    feedback_audio_url: Optional[str] = None  # URL to get TTS audio
    word_corrections: List[WordCorrection] = []  # Detailed word-level corrections

# New models for assessment
class AssessmentWordResponse(BaseModel):
    word: str
    language: str
    difficulty: str
    category: str
    attempt: int
    instructions: str

class AssessmentSubmission(BaseModel):
    word: str
    language: str
    attempt: int
    session_id: Optional[str] = None

class AssessmentResultResponse(BaseModel):
    word: str
    transcription: str
    accuracy: float
    pronunciation_score: float
    estimated_wab: float
    severity_level: str
    confidence: float
    is_assessment_complete: bool
    next_word: Optional[AssessmentWordResponse] = None
    final_assessment: Optional[Dict] = None

# Session storage (in production, use a database)
sessions_db = {}

# User progress tracking (tracks difficulty progression per user)
user_progress_db = {}  # Format: {patient_id: {language: {difficulty: sentences_completed}}}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    therapy = get_therapy_system()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "models_loaded": {
            "asr_model": therapy.asr_model is not None,
            "asr_processor": therapy.asr_processor is not None,
            "severity_model": therapy.severity_model is not None
        }
    }

@app.post("/api/session/start")
async def start_session(request: SessionStartRequest, db: Session = Depends(get_db)):
    """Start a new therapy session"""
    
    # Generate session ID
    session_id = f"session_{datetime.utcnow().timestamp()}"
    
    patient_id = request.patient_id or "default"
    
    # Get or create user difficulty progress from database
    progress = db.query(UserDifficultyProgress).filter(
        UserDifficultyProgress.patient_id == patient_id,
        UserDifficultyProgress.language == request.language
    ).first()
    
    if not progress:
        # Create new progress record
        progress = UserDifficultyProgress(
            patient_id=patient_id,
            language=request.language,
            easy_completed=0,
            medium_completed=0,
            hard_completed=0,
            current_difficulty='easy'
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    # Get current difficulty from database
    current_difficulty = progress.current_difficulty
    user_lang_progress = {
        "easy": progress.easy_completed,
        "medium": progress.medium_completed,
        "hard": progress.hard_completed,
        "current_difficulty": current_difficulty
    }
    
    # Store session data
    sessions_db[session_id] = {
        "session_id": session_id,
        "language": request.language,
        "difficulty": current_difficulty,
        "patient_id": patient_id,
        "started_at": datetime.utcnow().isoformat(),
        "sentences_completed": 0,
        "total_accuracy": 0,
        "results": [],
        "assessment_results": [],  # Store assessment results
        "assessment_complete": False,
        "severity_level": None,
        "estimated_wab": None,
        "category_performance": {}  # Track performance by category
    }
    
    return {
        "session_id": session_id, 
        "status": "started",
        "current_difficulty": current_difficulty,
        "progress": user_lang_progress
    }

@app.get("/api/assessment/start")
async def start_assessment(language: str = "en", session_id: Optional[str] = None):
    """Start initial assessment - get first assessment word"""
    
    print(f"🎯 Starting assessment for language: {language}")
    
    # Get first assessment word
    assessment_word = initial_assessment.get_assessment_word(language, attempt=1)
    
    # Generate instructions based on language
    instructions_map = {
        "hi": f"कृपया इस शब्द को स्पष्ट रूप से बोलें: '{assessment_word.word}'",
        "kn": f"ದಯವಿಟ್ಟು ಈ ಪದವನ್ನು ಸ್ಪಷ್ಟವಾಗಿ ಹೇಳಿ: '{assessment_word.word}'",
        "en": f"Please say this word clearly: '{assessment_word.word}'"
    }
    
    return AssessmentWordResponse(
        word=assessment_word.word,
        language=assessment_word.language,
        difficulty=assessment_word.difficulty,
        category=assessment_word.category,
        attempt=1,
        instructions=instructions_map.get(language, instructions_map["en"])
    )

@app.post("/api/assessment/submit")
async def submit_assessment(
    audio: UploadFile = File(...),
    word: str = Form(...),
    language: str = Form(...),
    attempt: int = Form(...),
    session_id: Optional[str] = Form(None)
):
    """Submit assessment audio and get results"""
    
    temp_audio_path = None
    try:
        # Save uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            temp_audio_path = tmp_file.name
            shutil.copyfileobj(audio.file, tmp_file)
        
        print(f"🎯 Processing assessment: word='{word}', language={language}, attempt={attempt}")
        
        # Get therapy system for transcription with language-specific models
        therapy = get_therapy_system(language)
        
        # Transcribe audio using optimized ASR
        print("🎤 Transcribing audio...")
        transcription = ""
        
        try:
            from core.simple_multilingual_asr import transcribe_multilingual
            transcription = transcribe_multilingual(temp_audio_path, language)
            print(f"📝 Transcription: '{transcription}'")
        except Exception as e:
            print(f"❌ ASR error: {e}")
            transcription = ""
        
        # Handle empty or unclear transcription
        if not transcription or transcription.strip() == "":
            print("⚠️ Empty or unclear transcription - speech not recognized")
            
            # Return result for unrecognized speech
            result = {
                "word": word,
                "transcription": "[Speech not recognized]",
                "accuracy": 0.0,
                "attempt": attempt,
                "feedback": "Could not understand the speech. Please speak more clearly.",
                "passed": False
            }
            
            # Cleanup temp file
            try:
                os.unlink(temp_audio_path)
            except:
                pass
            
            print("✅ Returned feedback for unrecognized speech")
            return result
        
        # Analyze pronunciation with proper script detection
        if language in ["hi", "kn"] and transcription:
            # Check if transcription is in native script
            is_kannada_script = any('\u0C80' <= char <= '\u0CFF' for char in transcription)
            is_hindi_script = any('\u0900' <= char <= '\u097F' for char in transcription)
            is_native_script = (language == "kn" and is_kannada_script) or (language == "hi" and is_hindi_script)
            
            if is_native_script:
                # Both in native script - direct comparison
                print(f"✅ Both in native script - direct comparison")
                
                # Normalize both
                word_normalized = word.strip()
                transcription_normalized = transcription.strip()
                
                # Remove zero-width characters
                for char in ["\u200b", "\u200c", "\u200d"]:
                    word_normalized = word_normalized.replace(char, "")
                    transcription_normalized = transcription_normalized.replace(char, "")
                
                print(f"🎯 Target: '{word_normalized}'")
                print(f"🎤 Transcription: '{transcription_normalized}'")
                
                # Check for exact match
                if word_normalized == transcription_normalized:
                    print(f"🎉 EXACT MATCH!")
                    accuracy = 100.0
                else:
                    analysis = therapy.analyze_pronunciation(word_normalized, transcription_normalized)
                    accuracy = analysis.get('accuracy', 0)
            else:
                # Romanized transcription - compare with romanized target
                if language == "hi":
                    romanized_target = romanize_hindi(word)
                else:
                    romanized_target = romanize_kannada(word)
                
                analysis1 = therapy.analyze_pronunciation(word, transcription)
                analysis2 = therapy.analyze_pronunciation(romanized_target, transcription)
                fuzzy_accuracy = calculate_fuzzy_accuracy(romanized_target, transcription)
                
                accuracy = max(
                    analysis1.get('accuracy', 0),
                    analysis2.get('accuracy', 0),
                    fuzzy_accuracy
                )
        else:
            analysis = therapy.analyze_pronunciation(word, transcription)
            accuracy = analysis.get('accuracy', 0)
        
        # Calculate pronunciation score (0-100)
        pronunciation_score = accuracy
        
        # Store assessment result
        assessment_result = {
            "word": word,
            "transcription": transcription,
            "accuracy": accuracy,
            "pronunciation_score": pronunciation_score,
            "attempt": attempt,
            "language": language,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update session if provided
        if session_id and session_id in sessions_db:
            sessions_db[session_id]["assessment_results"].append(assessment_result)
        
        # Determine if assessment is complete and what's next
        is_complete = False
        next_word = None
        final_assessment = None
        
        # Get current session assessment results
        current_results = []
        if session_id and session_id in sessions_db:
            current_results = sessions_db[session_id]["assessment_results"]
        else:
            current_results = [assessment_result]  # Just this result
        
        if attempt < 3:
            # Continue assessment with next difficulty level
            next_assessment_word = initial_assessment.get_assessment_word(language, attempt + 1)
            
            instructions_map = {
                "hi": f"अब इस शब्द को बोलें: '{next_assessment_word.word}'",
                "kn": f"ಈಗ ಈ ಪದವನ್ನು ಹೇಳಿ: '{next_assessment_word.word}'",
                "en": f"Now say this word: '{next_assessment_word.word}'"
            }
            
            next_word = AssessmentWordResponse(
                word=next_assessment_word.word,
                language=next_assessment_word.language,
                difficulty=next_assessment_word.difficulty,
                category=next_assessment_word.category,
                attempt=attempt + 1,
                instructions=instructions_map.get(language, instructions_map["en"])
            )
        else:
            # Assessment complete - calculate final severity
            is_complete = True
            severity_level, estimated_wab, recommendations = initial_assessment.calculate_severity_from_assessment(
                current_results, language
            )
            
            # Update session with final assessment
            if session_id and session_id in sessions_db:
                sessions_db[session_id]["assessment_complete"] = True
                sessions_db[session_id]["severity_level"] = severity_level.value
                sessions_db[session_id]["estimated_wab"] = estimated_wab
                sessions_db[session_id]["difficulty"] = initial_assessment.get_practice_difficulty(severity_level)
            
            final_assessment = {
                "severity_level": severity_level.value,
                "estimated_wab": estimated_wab,
                "recommendations": recommendations,
                "practice_difficulty": initial_assessment.get_practice_difficulty(severity_level),
                "session_length_minutes": initial_assessment.get_session_length(severity_level),
                "words_per_session": initial_assessment.get_words_per_session(severity_level)
            }
            
            print(f"🎯 Assessment complete: {severity_level.value} (WAB: {estimated_wab:.1f})")
        
        return AssessmentResultResponse(
            word=word,
            transcription=transcription,
            accuracy=accuracy,
            pronunciation_score=pronunciation_score,
            estimated_wab=estimated_wab if is_complete else accuracy,  # Temporary estimate
            severity_level=severity_level.value if is_complete else "assessing",
            confidence=0.8,  # Fixed confidence for now
            is_assessment_complete=is_complete,
            next_word=next_word,
            final_assessment=final_assessment
        )
        
    except Exception as e:
        print(f"❌ Assessment error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")
        
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)

@app.get("/api/sentences")
async def get_sentences(
    language: str = "en",
    difficulty: str = "easy",
    count: int = 5,
    session_id: Optional[str] = None
):
    """Get therapy sentences using interactive_therapy.py database"""
    
    therapy = get_therapy_system()
    
    # If session provided and assessment complete, use assessment-based difficulty
    if session_id and session_id in sessions_db:
        session = sessions_db[session_id]
        if session.get("assessment_complete", False):
            # Use difficulty from assessment
            assessed_difficulty = session.get("difficulty", difficulty)
            severity_level = session.get("severity_level", "moderate")
            
            print(f"🎯 Using assessment-based difficulty: {assessed_difficulty} (severity: {severity_level})")
            difficulty = assessed_difficulty
            
            # Adjust count based on severity
            if severity_level in ["very_severe", "severe"]:
                count = min(count, initial_assessment.get_words_per_session(SeverityLevel(severity_level)))
    
    sentences = therapy.sentences_db.get(language, {}).get(difficulty, [])
    
    if not sentences:
        raise HTTPException(status_code=404, detail=f"No sentences found for {language}/{difficulty}")
    
    # Convert TherapySentence objects to dict format for frontend
    selected_sentences = sentences[:count] if len(sentences) > count else sentences
    
    return {
        "sentences": [
            {
                "id": f"{language}_{difficulty}_{i}",
                "text": s.text,
                "language": s.language,
                "difficulty": s.difficulty,
                "category": s.category,
                "targetWords": s.target_words  # camelCase for frontend
            }
            for i, s in enumerate(selected_sentences)
        ],
        "total": len(selected_sentences),
        "language": language,
        "difficulty": difficulty,
        "assessment_based": session_id and session_id in sessions_db and sessions_db[session_id].get("assessment_complete", False)
    }

@app.get("/api/get-sentence")
async def get_single_sentence(language: str = "en", wab_score: float = 50):
    """Get a single sentence based on WAB score using interactive_therapy.py method"""
    
    therapy = get_therapy_system()
    sentence = therapy.get_sentence_by_severity(language, wab_score)
    
    return {
        "text": sentence.text,
        "language": sentence.language,
        "difficulty": sentence.difficulty,
        "category": sentence.category,
        "targetWords": sentence.target_words,
        "wab_score": wab_score
    }

@app.post("/api/process-audio")
async def process_audio(
    audio: UploadFile = File(...),
    target_sentence: str = Form(...),
    language: str = Form("en"),
    session_id: Optional[str] = Form(None)
):
    """
    Process audio using EXACT interactive_therapy.py functions:
    1. transcribe_audio()
    2. analyze_pronunciation() 
    3. assess_severity()
    """
    
    temp_audio_path = None
    try:
        print(f"🎯 Starting audio processing: target='{target_sentence}', language={language}")
        
        # Save uploaded audio to temporary file
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                temp_audio_path = tmp_file.name
                shutil.copyfileobj(audio.file, tmp_file)
            print(f"✅ Audio saved to: {temp_audio_path}")
        except Exception as save_error:
            print(f"❌ Error saving audio file: {save_error}")
            raise
        
        # Get therapy system with language-specific models
        try:
            print(f"🔄 Loading therapy system for {language}...")
            therapy = get_therapy_system(language)
            print(f"✅ Therapy system loaded")
        except Exception as therapy_error:
            print(f"❌ Error loading therapy system: {therapy_error}")
            raise
        
        # Step 1: Transcribe audio using optimized ASR
        print("🎤 Step 1: Transcribing audio...")
        
        transcription = ""
        
        # Use simple multilingual ASR (faster, no fallback chain)
        try:
            from core.simple_multilingual_asr import transcribe_multilingual
            
            print(f"🌐 Using optimized ASR for {language}...")
            transcription = transcribe_multilingual(temp_audio_path, language)
            print(f"📝 Transcription result: '{transcription}'")
            
        except Exception as transcribe_error:
            print(f"❌ ASR error: {transcribe_error}")
            import traceback
            traceback.print_exc()
            transcription = ""
        
        # Handle empty or unclear transcription
        if not transcription or transcription.strip() == "":
            print("⚠️ Empty or unclear transcription - speech not recognized")
            
            # Create a result for unrecognized speech
            result = AudioProcessingResult(
                transcription="[Speech not recognized]",
                target_sentence=target_sentence,
                accuracy=0.0,
                wab_score=0.0,  # Added missing field
                severity="Unable to assess",  # Added missing field
                feedback="Could not understand the speech. Please try again with clearer pronunciation.",
                phonetic_analysis={
                    "correct_phonemes": [],
                    "incorrect_phonemes": [],
                    "missing_phonemes": [],
                    "extra_phonemes": []
                },
                word_corrections=[],
                detailed_errors=[],  # Added
                practice_suggestions=[]  # Added
            )
            
            # Store result in session if session_id provided
            if session_id and session_id in sessions_db:
                session = sessions_db[session_id]
                if "results" not in session:
                    session["results"] = []
                session["results"].append(result.dict())
            
            # Cleanup temp file
            try:
                os.unlink(temp_audio_path)
            except:
                pass
            
            print("✅ Returned feedback for unrecognized speech")
            return result
        
        # Step 2: Analyze pronunciation with language-aware comparison
        print("📊 Step 2: Analyzing pronunciation...")
        
        try:
            # Handle language-specific comparison
            if language in ["hi", "kn"] and transcription:
                lang_name = "Hindi" if language == "hi" else "Kannada"
                print(f"🇮🇳 {lang_name} speech transcribed as: '{transcription}'")
                
                # Check if transcription is in native script (Kannada/Hindi)
                is_kannada_script = any('\u0C80' <= char <= '\u0CFF' for char in transcription)
                is_hindi_script = any('\u0900' <= char <= '\u097F' for char in transcription)
                is_native_script = (language == "kn" and is_kannada_script) or (language == "hi" and is_hindi_script)
                
                if is_native_script:
                    # Both target and transcription are in native script - direct comparison!
                    print(f"✅ Both in {lang_name} script - using direct comparison")
                    
                    # Normalize both strings for accurate comparison
                    target_normalized = target_sentence.strip()
                    transcription_normalized = transcription.strip()
                    
                    # Remove any zero-width characters from both
                    for char in ["\u200b", "\u200c", "\u200d"]:
                        target_normalized = target_normalized.replace(char, "")
                        transcription_normalized = transcription_normalized.replace(char, "")
                    
                    print(f"🎯 Target: '{target_normalized}'")
                    print(f"🎤 Transcription: '{transcription_normalized}'")
                    
                    # Direct comparison
                    analysis = therapy.analyze_pronunciation(target_normalized, transcription_normalized)
                    analysis['comparison_method'] = 'direct_native_script'
                    
                    # If exact match, set accuracy to 100%
                    if target_normalized == transcription_normalized:
                        print(f"🎉 EXACT MATCH! Setting accuracy to 100%")
                        analysis['accuracy'] = 100.0
                    
                    print(f"📈 Direct {lang_name} comparison: {analysis.get('accuracy', 0):.1f}% accuracy")
                else:
                    # Transcription is romanized - need to compare with romanized target
                    print(f"⚠️ Transcription is romanized - comparing with romanized target")
                    
                    # Create romanized versions for comparison
                    if language == "hi":
                        romanized_target = romanize_hindi(target_sentence)
                    else:  # language == "kn"
                        romanized_target = romanize_kannada(target_sentence)
                    print(f"🔤 Romanized target: '{romanized_target}'")
                    
                    # Compare both original and romanized versions
                    analysis1 = therapy.analyze_pronunciation(target_sentence, transcription)
                    analysis2 = therapy.analyze_pronunciation(romanized_target, transcription)
                    
                    # Also check fuzzy similarity for better accuracy
                    fuzzy_accuracy = calculate_fuzzy_accuracy(romanized_target, transcription)
                    print(f"🔍 Fuzzy accuracy: {fuzzy_accuracy:.1f}%")
                    
                    # Use the best accuracy
                    best_accuracy = max(
                        analysis1.get('accuracy', 0),
                        analysis2.get('accuracy', 0),
                        fuzzy_accuracy
                    )
                    
                    if fuzzy_accuracy == best_accuracy and fuzzy_accuracy > 50:
                        analysis = analysis2.copy()
                        analysis['accuracy'] = fuzzy_accuracy
                        analysis['comparison_method'] = 'fuzzy_romanized'
                        print(f"📈 Using fuzzy romanized comparison: {fuzzy_accuracy:.1f}% accuracy")
                    elif analysis2.get('accuracy', 0) > analysis1.get('accuracy', 0):
                        analysis = analysis2
                        analysis['comparison_method'] = 'romanized'
                        print(f"📈 Using romanized comparison: {analysis.get('accuracy', 0):.1f}% accuracy")
                    else:
                        analysis = analysis1
                        analysis['comparison_method'] = 'direct'
                        print(f"📈 Using direct comparison: {analysis.get('accuracy', 0):.1f}% accuracy")
            else:
                # For English or other languages
                analysis = therapy.analyze_pronunciation(target_sentence, transcription)
                print(f"📈 Analysis result: {analysis.get('accuracy', 'unknown')} accuracy")
        
            # Step 3: Assess severity using interactive_therapy.py assess_severity()
            print("🏥 Step 3: Assessing severity...")
            severity_info = therapy.assess_severity(temp_audio_path, analysis)
            print(f"🎯 Severity: {severity_info.get('severity_name', 'unknown')} (WAB-AQ: {severity_info.get('wab_aq_score', 0)})")
            
            # Step 4: Generate corrective feedback (if method exists)
            corrective_feedback = {}
            try:
                corrective_feedback = therapy.generate_corrective_feedback(analysis, target_sentence)
            except AttributeError:
                print("⚠️ generate_corrective_feedback method not found, using basic feedback")
                corrective_feedback = {
                    "practice_suggestions": ["Keep practicing!", "Focus on clear pronunciation"],
                    "strengths": ["Good effort!"] if analysis.get('similarity', 0) > 0.5 else []
                }
            
            # Generate language-appropriate feedback
            accuracy_score = analysis.get('accuracy', 0) if isinstance(analysis.get('accuracy'), (int, float)) else 0
            language_feedback = generate_language_feedback(accuracy_score, language, target_sentence, transcription)
            
            # Generate detailed word-level corrections
            word_corrections = generate_word_corrections(target_sentence, transcription, language)
            print(f"🔍 Generated {len(word_corrections)} word corrections")
        
            # Add transcription info for debugging
            transcription_info = transcription
            if language == "hi" and transcription:
                romanized = romanize_hindi(target_sentence)
                transcription_info = f"{transcription} (target: {target_sentence} / {romanized})"
            
            # Generate TTS URL for feedback
            import urllib.parse
            feedback_audio_url = f"/api/tts?text={urllib.parse.quote(language_feedback)}&language={language}"
            
        except Exception as analysis_error:
            print(f"❌ Error during pronunciation analysis: {analysis_error}")
            import traceback
            traceback.print_exc()
            
            # Return basic error result
            result = AudioProcessingResult(
                transcription=transcription or "[Error]",
                target_sentence=target_sentence,
                accuracy=0.0,
                wab_score=0.0,  # Added
                severity="Unable to assess",  # Added
                feedback="Error analyzing pronunciation. Please try again.",
                phonetic_analysis={},
                word_corrections=[],
                detailed_errors=[],  # Added
                practice_suggestions=[]  # Added
            )
            return result
        
        # Prepare result using exact interactive_therapy.py output format
        result = AudioProcessingResult(
            transcription=transcription,
            accuracy=accuracy_score,
            wab_score=severity_info.get('wab_aq_score', 50),
            severity=severity_info.get('severity_name', 'Moderate'),
            feedback=language_feedback,  # Use language-specific feedback
            detailed_errors=analysis.get('detailed_errors', [])[:3],  # Top 3 errors
            practice_suggestions=corrective_feedback.get('practice_suggestions', [])[:3],  # Top 3 suggestions
            strengths=corrective_feedback.get('strengths', []),
            feedback_audio_url=feedback_audio_url,  # URL to get TTS audio
            word_corrections=word_corrections  # Detailed word-level corrections
        )
        
        # Update session if session_id provided
        if session_id and session_id in sessions_db:
            session = sessions_db[session_id]
            session["sentences_completed"] += 1
            session["results"].append(result.dict())
            session["total_accuracy"] = (
                (session["total_accuracy"] * (session["sentences_completed"] - 1) + result.accuracy) 
                / session["sentences_completed"]
            )
            
            # Track category performance
            # Extract category from target_sentence (you may need to pass this separately)
            category = "general"  # Default category
            if category not in session["category_performance"]:
                session["category_performance"][category] = {"total": 0, "correct": 0, "accuracy": 0}
            
            session["category_performance"][category]["total"] += 1
            if result.accuracy >= 70:  # Consider 70% as correct
                session["category_performance"][category]["correct"] += 1
            session["category_performance"][category]["accuracy"] = (
                session["category_performance"][category]["correct"] / 
                session["category_performance"][category]["total"] * 100
            )
        
        print("✅ Audio processing complete")
        return result
        
    except Exception as e:
        print(f"❌ Audio processing error: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print("❌ Full traceback:")
        traceback.print_exc()
        
        # Clean up temp file before raising error
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except:
                pass
        
        # Return detailed error to frontend
        error_detail = {
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Audio processing failed. Check backend console for details."
        }
        raise HTTPException(status_code=500, detail=str(error_detail))
        
    finally:
        # Clean up temporary file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except:
                pass

@app.get("/api/languages")
async def get_supported_languages():
    """Get list of supported languages from interactive_therapy.py"""
    
    therapy = get_therapy_system()
    languages = list(therapy.sentences_db.keys())
    
    language_info = {
        "en": {"name": "English", "native": "English"},
        "hi": {"name": "Hindi", "native": "हिंदी"},
        "kn": {"name": "Kannada", "native": "ಕನ್ನಡ"}
    }
    
    return {
        "languages": [
            {
                "code": lang,
                "name": language_info.get(lang, {}).get("name", lang),
                "native": language_info.get(lang, {}).get("native", lang),
                "available": lang in languages
            }
            for lang in ["en", "hi", "kn"]
        ]
    }

@app.get("/api/difficulties")
async def get_difficulties():
    """Get available difficulty levels"""
    return {
        "difficulties": [
            {"level": "easy", "description": "Basic words and phrases", "wab_range": "0-50"},
            {"level": "medium", "description": "Simple sentences", "wab_range": "51-75"},
            {"level": "hard", "description": "Complex sentences", "wab_range": "76-100"}
        ]
    }

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return sessions_db[session_id]

@app.post("/api/session/{session_id}/complete")
async def complete_session(session_id: str, db: Session = Depends(get_db)):
    """Complete a therapy session and update user progress"""
    
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions_db[session_id]
    patient_id = session["patient_id"]
    language = session["language"]
    difficulty = session["difficulty"]
    sentences_completed = session["sentences_completed"]
    average_accuracy = session["total_accuracy"]
    
    # Mark session as ended
    session["end_time"] = datetime.utcnow().isoformat()
    session["status"] = "completed"
    
    # Update database progress
    progress = db.query(UserDifficultyProgress).filter(
        UserDifficultyProgress.patient_id == patient_id,
        UserDifficultyProgress.language == language
    ).first()
    
    if not progress:
        progress = UserDifficultyProgress(
            patient_id=patient_id,
            language=language,
            easy_completed=0,
            medium_completed=0,
            hard_completed=0,
            current_difficulty='easy'
        )
        db.add(progress)
    
    # Update completed count for current difficulty
    if difficulty == "easy":
        progress.easy_completed += sentences_completed
    elif difficulty == "medium":
        progress.medium_completed += sentences_completed
    elif difficulty == "hard":
        progress.hard_completed += sentences_completed
    
    # Check if user should progress to next difficulty
    # Progress after every 10 sentences completed in current difficulty
    next_difficulty = None
    difficulty_progression_message = None
    should_progress = False
    
    # Check if this session completed 10 sentences (full session)
    if sentences_completed >= 10:
        if difficulty == "easy" and progress.easy_completed >= 10:
            progress.current_difficulty = "medium"
            next_difficulty = "medium"
            difficulty_progression_message = f"🎉 Congratulations! You've completed {progress.easy_completed} easy sentences. Moving to MEDIUM difficulty!"
            should_progress = True
            print(f"🎉 {patient_id} progressed from easy to medium in {language}")
            
        elif difficulty == "medium" and progress.medium_completed >= 10:
            progress.current_difficulty = "hard"
            next_difficulty = "hard"
            difficulty_progression_message = f"🌟 Excellent progress! You've completed {progress.medium_completed} medium sentences. Moving to HARD difficulty!"
            should_progress = True
            print(f"🎉 {patient_id} progressed from medium to hard in {language}")
            
        elif difficulty == "hard" and progress.hard_completed >= 10:
            difficulty_progression_message = f"🏆 Amazing! You've mastered {progress.hard_completed} hard sentences. You're at the highest level - keep practicing!"
            print(f"🏆 {patient_id} completed all difficulties in {language}")
    
    # If not progressing, show encouragement
    if not should_progress and not difficulty_progression_message:
        remaining = 10 - (progress.easy_completed if difficulty == "easy" else 
                         progress.medium_completed if difficulty == "medium" else 
                         progress.hard_completed)
        if remaining > 0:
            difficulty_progression_message = f"Great job! Complete {remaining} more {difficulty} sentences to unlock the next level!"
    
    # Commit changes BEFORE creating session record
    db.commit()
    db.refresh(progress)  # Refresh to ensure changes are persisted
    
    print(f"✅ Progress updated and committed: easy={progress.easy_completed}, medium={progress.medium_completed}, hard={progress.hard_completed}")
    print(f"✅ Current difficulty in DB: {progress.current_difficulty}")
    
    # Create database session record
    try:
        db_session = DBTherapySession(
            session_id=session_id,
            patient_id=patient_id,
            session_type='sentence',
            language=language,
            difficulty=difficulty,
            start_time=datetime.fromisoformat(session["started_at"]),
            end_time=datetime.utcnow(),
            duration_seconds=int((datetime.utcnow() - datetime.fromisoformat(session["started_at"])).total_seconds()),
            total_exercises=sentences_completed,
            completed_exercises=sentences_completed,
            average_accuracy=average_accuracy
        )
        db.add(db_session)
        db.commit()
        print(f"✅ Session saved to database: {session_id}")
    except Exception as e:
        print(f"⚠️ Failed to save session to database: {e}")
    
    # Update daily progress
    try:
        from datetime import date
        today = date.today()
        daily_progress = db.query(DBPatientProgress).filter(
            DBPatientProgress.patient_id == patient_id,
            DBPatientProgress.date == today
        ).first()
        
        if not daily_progress:
            daily_progress = DBPatientProgress(
                patient_id=patient_id,
                date=today,
                sessions_completed=1,
                total_exercises=sentences_completed,
                average_accuracy=average_accuracy,
                streak_days=1
            )
            db.add(daily_progress)
        else:
            daily_progress.sessions_completed += 1
            daily_progress.total_exercises += sentences_completed
            # Recalculate average
            daily_progress.average_accuracy = (
                (daily_progress.average_accuracy * (daily_progress.sessions_completed - 1) + average_accuracy) /
                daily_progress.sessions_completed
            )
        
        db.commit()
        print(f"✅ Daily progress updated for {patient_id}")
    except Exception as e:
        print(f"⚠️ Failed to update daily progress: {e}")
    
    user_lang_progress = {
        "easy": progress.easy_completed,
        "medium": progress.medium_completed,
        "hard": progress.hard_completed,
        "current_difficulty": progress.current_difficulty
    }
    
    return {
        "session_id": session_id,
        "status": "completed",
        "sentences_completed": sentences_completed,
        "average_accuracy": session["total_accuracy"],
        "difficulty": difficulty,
        "next_difficulty": next_difficulty,
        "progression_message": difficulty_progression_message,
        "progress": user_lang_progress,
        "category_performance": session.get("category_performance", {})
    }

class TTSRequest(BaseModel):
    text: str
    language: str = "en"

@app.post("/api/tts")
async def text_to_speech_endpoint(request: TTSRequest):
    """Convert text to speech and return audio"""
    
    text = request.text
    language = request.language
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    print(f"🔊 TTS Request: '{text}' (language: {language})")
    
    try:
        # Generate speech audio
        audio_bytes = text_to_speech(text, language)
        
        if not audio_bytes:
            print("❌ TTS returned empty bytes")
            raise HTTPException(status_code=500, detail="TTS generation returned empty audio")
        
        print(f"✅ TTS endpoint success: {len(audio_bytes)} bytes")
        
        # Determine media type based on content
        media_type = "audio/mpeg" if audio_bytes.startswith(b'ID3') or audio_bytes.startswith(b'\xff\xfb') else "audio/wav"
        
        # Return audio as streaming response
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type=media_type,
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ TTS endpoint error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

@app.get("/api/tts")
async def tts_get_endpoint(text: str, language: str = "en"):
    """GET version of TTS endpoint for easy testing"""
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text parameter required")
    
    try:
        audio_bytes = text_to_speech(text, language)
        
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="TTS generation failed")
        
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        print(f"❌ TTS GET error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
