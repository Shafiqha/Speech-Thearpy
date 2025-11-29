"""
FastAPI Routes for Lip Animation Exercise
Handles word input, video generation, and mouth tracking analysis
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import sys
import tempfile
import shutil
from datetime import datetime
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.phoneme_viseme_mapper import get_phoneme_viseme_mapper
from services.lip_animation_generator import get_lip_animation_generator
from services.improved_lip_generator import get_improved_lip_generator
from services.rhubarb_lip_sync import get_rhubarb_lip_sync
from services.simple_working_video import get_simple_working_video
from services.synced_rhubarb_video import get_synced_rhubarb_video
from services.real_rhubarb_integration import get_real_rhubarb_lip_sync
from services.rhubarb_with_sprites import get_rhubarb_with_sprites  # NEW: Sprite-based generator
from services.mouth_tracking_analyzer import get_mouth_tracking_analyzer
from services.advanced_asr import AdvancedASRService  # Your trained model
from services.phoneme_forced_alignment import get_phoneme_aligner  # NEW: Forced alignment
from services.sentence_phoneme_alignment import get_sentence_aligner  # NEW: Sentence alignment
from services.short_phrase_lip_sync import get_short_phrase_lip_sync  # NEW: Short phrase (2-3 words)
from services.audio_driven_lip_sync import get_audio_driven_lip_sync  # NEW: Audio-driven (all languages)
from services.true_audio_lip_mapping import get_true_audio_lip_mapper  # NEW: TRUE audio-to-lip mapping
from services.intelligent_lip_sync_router import get_intelligent_router  # NEW: Intelligent routing
from core.simple_tts import text_to_speech_file

# Initialize router
router = APIRouter(prefix="/api/lip-animation", tags=["Lip Animation Exercise"])

# Pydantic models
class WordAnalysisRequest(BaseModel):
    word: str
    language: str = "en"

class WordAnalysisResponse(BaseModel):
    word: str
    language: str
    phonemes: List[str]
    visemes: List[Dict]
    total_duration: int
    phoneme_count: int
    viseme_count: int

class VideoGenerationRequest(BaseModel):
    word: str
    language: str = "en"

class VideoGenerationResponse(BaseModel):
    success: bool
    word: str
    language: str
    video_url: str
    audio_url: str
    phonemes: List[str]
    visemes: List[Dict]
    duration_ms: int

class PracticeSubmissionResponse(BaseModel):
    success: bool
    accuracy: float
    lip_sync_score: float
    transcription: str
    feedback: str
    errors: List[str]
    phoneme_accuracy: Dict
    viseme_accuracy: Dict
    video_analysis: Dict


@router.post("/analyze-word", response_model=WordAnalysisResponse)
async def analyze_word(request: WordAnalysisRequest):
    """
    Analyze a word and return phoneme/viseme breakdown
    
    Args:
        word: Word to analyze
        language: Language code (en, hi, kn)
        
    Returns:
        Phoneme and viseme breakdown
    """
    try:
        mapper = get_phoneme_viseme_mapper()
        
        # Get phoneme and viseme breakdown
        analysis = mapper.word_to_visemes(request.word, request.language)
        
        return WordAnalysisResponse(
            word=analysis['word'],
            language=analysis['language'],
            phonemes=analysis['phonemes'],
            visemes=analysis['visemes'],
            total_duration=analysis['total_duration'],
            phoneme_count=analysis['phoneme_count'],
            viseme_count=analysis['viseme_count']
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Word analysis failed: {str(e)}")


@router.post("/generate-video", response_model=VideoGenerationResponse)
async def generate_video(request: VideoGenerationRequest):
    """
    Generate lip animation video with audio for a word
    
    Args:
        word: Word to generate video for
        language: Language code
        
    Returns:
        URLs to video and audio files
    """
    try:
        # Use Rhubarb with Sprites - Uses your downloaded mouth shape images!
        generator = get_rhubarb_with_sprites()
        mapper = get_phoneme_viseme_mapper()
        
        # Create media directories (in api folder where main.py serves from)
        api_dir = Path(__file__).parent
        video_dir = api_dir / 'media' / 'lip_animations'
        audio_dir = api_dir / 'media' / 'lip_audio'
        video_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Video directory: {video_dir}")
        print(f"📁 Audio directory: {audio_dir}")
        
        # Generate unique filename
        file_id = f"{request.word}_{request.language}_{uuid.uuid4().hex[:8]}"
        video_path = str(video_dir / f"{file_id}.mp4")
        audio_path = str(audio_dir / f"{file_id}.mp3")
        
        # Generate audio using TTS
        try:
            success = text_to_speech_file(request.word, audio_path, request.language)
            if not success:
                print(f"⚠️ TTS failed, creating placeholder")
                # Create a simple WAV file as fallback
                import numpy as np
                import soundfile as sf
                sample_rate = 22050
                duration = 1.0
                t = np.linspace(0, duration, int(sample_rate * duration))
                audio_signal = np.sin(2 * np.pi * 440 * t) * 0.3
                sf.write(audio_path.replace('.mp3', '.wav'), audio_signal, sample_rate)
                audio_path = audio_path.replace('.mp3', '.wav')
        except Exception as e:
            print(f"⚠️ TTS failed: {e}")
            audio_path = None
        
        # Use INTELLIGENT ROUTING for optimal accuracy
        print(f"🎯 Using Intelligent Lip Sync Router for {request.language}")
        print(f"   Automatically selects best method based on input")
        
        router_service = get_intelligent_router()
        lip_sync_data, optimization_info = router_service.generate_optimized_lip_sync(
            audio_path=audio_path,
            text=request.word,
            language=request.language
        )
        
        print(f"✅ Optimization: {optimization_info['expected_accuracy']} accuracy")
        print(f"   Method: {optimization_info['recommended_method']}")
        print(f"   Recognizer: {optimization_info['recognizer']}")
        
        if lip_sync_data:
            # Generate video frames from forced alignment
            frames = generator._generate_frames(lip_sync_data, request.word)
            generator._encode_video(frames, audio_path, video_path)
            print(f"✅ Video generated with forced alignment")
        else:
            raise Exception("Forced alignment failed")
        
        # Get phoneme/viseme data
        analysis = mapper.word_to_visemes(request.word, request.language)
        
        # Return URLs (relative paths that frontend can access)
        video_url = f"/media/lip_animations/{Path(video_path).name}"
        audio_url = f"/media/lip_audio/{Path(audio_path).name}"
        
        return VideoGenerationResponse(
            success=True,
            word=request.word,
            language=request.language,
            video_url=video_url,
            audio_url=audio_url,
            phonemes=analysis['phonemes'],
            visemes=analysis['visemes'],
            duration_ms=analysis['total_duration']
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@router.get("/video/{filename}")
async def get_video(filename: str):
    """Serve generated lip animation video"""
    video_path = Path('media/lip_animations') / filename
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        video_path, 
        media_type="video/mp4",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve generated audio file"""
    audio_path = Path('media/lip_audio') / filename
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    
    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.get("/accuracy-recommendations/{language}")
async def get_accuracy_recommendations(language: str):
    """
    Get accuracy recommendations for a specific language
    
    Args:
        language: Language code (en, hi, kn)
        
    Returns:
        Recommendations for best accuracy
    """
    try:
        router_service = get_intelligent_router()
        recommendations = router_service.get_recommendations(language)
        
        return {
            "success": True,
            "language": language,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.post("/submit-practice", response_model=PracticeSubmissionResponse)
async def submit_practice(
    video: UploadFile = File(...),
    audio: UploadFile = File(...),
    word: str = Form(...),
    language: str = Form("en"),
    session_id: Optional[str] = Form(None)
):
    """
    Submit practice attempt with video and audio for analysis
    
    Args:
        video: User's video recording
        audio: User's audio recording
        word: Target word
        language: Language code
        session_id: Optional session ID
        
    Returns:
        Analysis results with feedback
    """
    temp_video_path = None
    temp_audio_path = None
    
    try:
        # Save uploaded files
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_video:
            temp_video_path = tmp_video.name
            shutil.copyfileobj(video.file, tmp_video)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_audio:
            temp_audio_path = tmp_audio.name
            shutil.copyfileobj(audio.file, tmp_audio)
        
        print(f"🎯 Analyzing practice: word='{word}', language={language}")
        
        # Get services
        mapper = get_phoneme_viseme_mapper()
        analyzer = get_mouth_tracking_analyzer()
        
        # Get target visemes
        target_analysis = mapper.word_to_visemes(word, language)
        target_visemes = target_analysis['visemes']
        
        # Analyze user's video
        video_analysis = analyzer.analyze_video_file(temp_video_path, target_visemes)
        
        # Transcribe audio using YOUR TRAINED MODEL
        transcription = ""
        try:
            # Try your advanced ASR model first
            print(f"🤖 Using YOUR trained ASR model...")
            asr = AdvancedASRService()
            transcription = asr.transcribe(temp_audio_path, language)
            print(f"✅ Transcription (YOUR MODEL): '{transcription}'")
        except Exception as e:
            print(f"⚠️ Advanced ASR failed: {e}, falling back to multilingual ASR")
            try:
                from core.simple_multilingual_asr import transcribe_multilingual
                transcription = transcribe_multilingual(temp_audio_path, language)
                print(f"📝 Transcription (fallback): '{transcription}'")
            except Exception as e2:
                print(f"⚠️ All transcription failed: {e2}")
                transcription = ""
        
        # Calculate accuracies
        comparison = video_analysis.get('comparison', {})
        accuracy = comparison.get('accuracy', 0.0)
        lip_sync_score = comparison.get('lip_sync_score', 0.0)
        
        # Calculate speech accuracy (transcription vs target word)
        speech_accuracy = 0.0
        if transcription and word:
            # Normalize both for comparison
            trans_normalized = transcription.strip().lower()
            word_normalized = word.strip().lower()
            
            # Check if transcription matches target word
            if trans_normalized == word_normalized:
                speech_accuracy = 100.0
                print(f"✅ Perfect speech match: '{transcription}' == '{word}'")
            else:
                # Calculate similarity
                from difflib import SequenceMatcher
                similarity = SequenceMatcher(None, trans_normalized, word_normalized).ratio()
                speech_accuracy = similarity * 100
                print(f"📊 Speech similarity: {speech_accuracy:.1f}% ('{transcription}' vs '{word}')")
        
        # Calculate phoneme accuracy
        phoneme_accuracy = {}
        for i, phoneme in enumerate(target_analysis['phonemes']):
            # Use speech accuracy as phoneme accuracy
            phoneme_accuracy[phoneme] = speech_accuracy
        
        # Calculate viseme accuracy
        viseme_accuracy = {}
        detected_visemes = video_analysis.get('detected_visemes', [])
        for i, viseme_info in enumerate(target_visemes):
            viseme = viseme_info['viseme']
            if i < len(detected_visemes):
                viseme_accuracy[viseme] = 100.0 if detected_visemes[i] == viseme else 0.0
            else:
                viseme_accuracy[viseme] = 0.0
        
        # Generate feedback combining both speech and lip sync
        # Use speech accuracy as primary feedback since transcription is correct
        if speech_accuracy >= 90:
            # Speech is correct, use language-specific feedback
            from main import generate_language_feedback
            feedback = generate_language_feedback(speech_accuracy, language, word, transcription)
            print(f"✅ Generated speech feedback: {feedback}")
        else:
            # Fall back to lip sync feedback
            feedback = analyzer.generate_feedback(comparison, language)
            print(f"📊 Generated lip sync feedback: {feedback}")
        
        # Get errors
        errors = comparison.get('errors', [])
        
        return PracticeSubmissionResponse(
            success=True,
            accuracy=accuracy,
            lip_sync_score=lip_sync_score,
            transcription=transcription,
            feedback=feedback,
            errors=errors,
            phoneme_accuracy=phoneme_accuracy,
            viseme_accuracy=viseme_accuracy,
            video_analysis={
                'total_frames': video_analysis.get('analyzed_frames', 0),
                'detected_viseme_count': len(detected_visemes),
                'target_viseme_count': len(target_visemes),
                'viseme_sequence': video_analysis.get('viseme_sequence', [])
            }
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Practice analysis failed: {str(e)}")
    
    finally:
        # Cleanup temporary files
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)


@router.get("/exercises")
async def get_exercises(language: str = "en", difficulty: str = "easy"):
    """
    Get list of available lip animation exercises
    
    Args:
        language: Language code
        difficulty: Difficulty level
        
    Returns:
        List of exercise words
    """
    # Predefined exercise words by language and difficulty
    exercises = {
        'en': {
            'easy': ['hello', 'water', 'food', 'home', 'yes', 'no'],
            'medium': ['thank', 'please', 'sorry', 'help', 'good', 'morning'],
            'hard': ['beautiful', 'wonderful', 'excellent', 'pronunciation', 'therapy']
        },
        'hi': {
            'easy': ['नमस्ते', 'पानी', 'खाना', 'घर', 'हाँ', 'नहीं'],
            'medium': ['धन्यवाद', 'अच्छा', 'बुरा', 'मदद', 'सुबह', 'रात'],
            'hard': ['सुंदर', 'अद्भुत', 'उत्कृष्ट', 'उच्चारण', 'चिकित्सा']
        },
        'kn': {
            'easy': ['ನಮಸ್ಕಾರ', 'ನೀರು', 'ಅನ್ನ', 'ಮನೆ', 'ಹೌದು', 'ಇಲ್ಲ'],
            'medium': ['ಧನ್ಯವಾದ', 'ಒಳ್ಳೆಯದು', 'ಕೆಟ್ಟದು', 'ಸಹಾಯ', 'ಬೆಳಿಗ್ಗೆ', 'ರಾತ್ರಿ'],
            'hard': ['ಸುಂದರ', 'ಅದ್ಭುತ', 'ಅತ್ಯುತ್ತಮ', 'ಉಚ್ಚಾರಣೆ', 'ಚಿಕಿತ್ಸೆ']
        }
    }
    
    words = exercises.get(language, {}).get(difficulty, exercises['en']['easy'])
    
    return {
        'language': language,
        'difficulty': difficulty,
        'exercises': [
            {
                'word': word,
                'id': f"{language}_{difficulty}_{i}"
            }
            for i, word in enumerate(words)
        ],
        'total': len(words)
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if media directories exist
    api_dir = Path(__file__).parent
    video_dir = api_dir / 'media' / 'lip_animations'
    audio_dir = api_dir / 'media' / 'lip_audio'
    
    return {
        "status": "healthy",
        "service": "Lip Animation Exercise",
        "timestamp": datetime.now().isoformat(),
        "media_directories": {
            "video_dir": str(video_dir),
            "video_exists": video_dir.exists(),
            "audio_dir": str(audio_dir),
            "audio_exists": audio_dir.exists(),
            "video_files": len(list(video_dir.glob("*.mp4"))) if video_dir.exists() else 0,
            "audio_files": len(list(audio_dir.glob("*.mp3"))) if audio_dir.exists() else 0
        }
    }
