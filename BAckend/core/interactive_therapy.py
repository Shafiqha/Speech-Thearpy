#!/usr/bin/env python3
"""
Interactive Speech Therapy System for Aphasia Patients
Progressive sentence practice with adaptive difficulty
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

import difflib
try:
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Import our modules
try:
    # Try relative imports first (when used as a package)
    from .train_simple import SimpleAphasiaModel
    from .simple_tts import ReliableTTS
    from .feedback_reader import FeedbackReader
except ImportError:
    # Fall back to direct imports (when run directly)
    from train_simple import SimpleAphasiaModel
    from simple_tts import ReliableTTS
    from feedback_reader import FeedbackReader

import os
import json
import time
import random
import torch
import numpy as np
import librosa
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
from pathlib import Path

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def calculate_similarity(target: str, transcription: str) -> float:
    """Calculate similarity percentage using Levenshtein distance."""
    if not target or not transcription:
        return 0.0
    
    # Normalize strings
    target = target.strip().lower()
    transcription = transcription.strip().lower()
    
    if target == transcription:
        return 100.0
    
    # Calculate Levenshtein distance
    distance = levenshtein_distance(target, transcription)
    max_len = max(len(target), len(transcription))
    
    if max_len == 0:
        return 100.0
    
    # Convert to similarity percentage
    similarity = ((max_len - distance) / max_len) * 100
    return max(0.0, similarity)

@dataclass
class TherapySentence:
    """Represents a therapy sentence with metadata."""
    text: str
    language: str
    difficulty: str  # 'easy', 'medium', 'hard'
    category: str    # 'greeting', 'family', 'food', 'daily', etc.
    target_words: List[str]  # Key words to focus on

@dataclass
class TherapySession:
    """Tracks therapy session progress."""
    patient_id: str
    language: str
    start_time: str
    current_sentence_index: int = 0
    current_difficulty: str = 'easy'
    total_attempts: int = 0
    correct_attempts: int = 0
    average_severity: float = 0.0
    session_sentences: List[Dict] = None

    def __post_init__(self):
        if self.session_sentences is None:
            self.session_sentences = []

class InteractiveSpeechTherapy:
    """Interactive speech therapy system with progressive difficulty."""

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.session = None
        self.sentences_db = self._load_sentences_database()
        self.tts = ReliableTTS()
        self.asr_model = None
        self.asr_processor = None
        self.severity_model = None

        print("🏥 INTERACTIVE SPEECH THERAPY SYSTEM")
        print("="*60)

    def _load_sentences_database(self) -> Dict[str, List[TherapySentence]]:
        """Load therapy sentences organized by language and difficulty."""

        sentences_db = {
            'en': {
                'easy': [
                    TherapySentence("Hello", 'en', 'easy', 'greeting', ['Hello']),
                    TherapySentence("Thank you", 'en', 'easy', 'polite', ['Thank', 'you']),
                    TherapySentence("Yes", 'en', 'easy', 'response', ['Yes']),
                    TherapySentence("No", 'en', 'easy', 'response', ['No']),
                    TherapySentence("Water", 'en', 'easy', 'basic', ['Water']),
                    TherapySentence("Food", 'en', 'easy', 'basic', ['Food']),
                    TherapySentence("Home", 'en', 'easy', 'basic', ['Home']),
                    TherapySentence("Good", 'en', 'easy', 'feeling', ['Good']),
                    TherapySentence("Bad", 'en', 'easy', 'feeling', ['Bad']),
                    TherapySentence("Help", 'en', 'easy', 'request', ['Help']),
                ],
                'medium': [
                    TherapySentence("I am hungry", 'en', 'medium', 'feeling', ['I', 'am', 'hungry']),
                    TherapySentence("I need water", 'en', 'medium', 'request', ['I', 'need', 'water']),
                    TherapySentence("How are you", 'en', 'medium', 'greeting', ['How', 'are', 'you']),
                    TherapySentence("I want to go home", 'en', 'medium', 'desire', ['I', 'want', 'go', 'home']),
                    TherapySentence("The cat is black", 'en', 'medium', 'description', ['The', 'cat', 'is', 'black']),
                    TherapySentence("I love you", 'en', 'medium', 'emotion', ['I', 'love', 'you']),
                    TherapySentence("Please help me", 'en', 'medium', 'request', ['Please', 'help', 'me']),
                    TherapySentence("What is your name", 'en', 'medium', 'question', ['What', 'is', 'your', 'name']),
                    TherapySentence("I am reading a book", 'en', 'medium', 'activity', ['I', 'am', 'reading', 'book']),
                    TherapySentence("The weather is nice", 'en', 'medium', 'description', ['The', 'weather', 'is', 'nice']),
                ],
                'hard': [
                    TherapySentence("I would like to speak with the doctor", 'en', 'hard', 'medical', ['I', 'would', 'like', 'speak', 'doctor']),
                    TherapySentence("My family is coming to visit tomorrow", 'en', 'hard', 'family', ['My', 'family', 'coming', 'visit', 'tomorrow']),
                    TherapySentence("I need to buy groceries for dinner", 'en', 'hard', 'shopping', ['I', 'need', 'buy', 'groceries', 'dinner']),
                    TherapySentence("The medication makes me feel better", 'en', 'hard', 'medical', ['The', 'medication', 'makes', 'feel', 'better']),
                    TherapySentence("I enjoy listening to music in the evening", 'en', 'hard', 'hobby', ['I', 'enjoy', 'listening', 'music', 'evening']),
                ]
            },
            'hi': {
                'easy': [
                    TherapySentence("नमस्ते", 'hi', 'easy', 'greeting', ['नमस्ते']),
                    TherapySentence("धन्यवाद", 'hi', 'easy', 'polite', ['धन्यवाद']),
                    TherapySentence("हाँ", 'hi', 'easy', 'response', ['हाँ']),
                    TherapySentence("नहीं", 'hi', 'easy', 'response', ['नहीं']),
                    TherapySentence("पानी", 'hi', 'easy', 'basic', ['पानी']),
                    TherapySentence("खाना", 'hi', 'easy', 'basic', ['खाना']),
                    TherapySentence("घर", 'hi', 'easy', 'basic', ['घर']),
                    TherapySentence("अच्छा", 'hi', 'easy', 'feeling', ['अच्छा']),
                    TherapySentence("बुरा", 'hi', 'easy', 'feeling', ['बुरा']),
                    TherapySentence("मदद", 'hi', 'easy', 'request', ['मदद']),
                ],
                'medium': [
                    TherapySentence("मुझे भूख लगी है", 'hi', 'medium', 'feeling', ['मुझे', 'भूख', 'लगी']),
                    TherapySentence("मुझे पानी चाहिए", 'hi', 'medium', 'request', ['मुझे', 'पानी', 'चाहिए']),
                    TherapySentence("आप कैसे हैं", 'hi', 'medium', 'greeting', ['आप', 'कैसे', 'हैं']),
                    TherapySentence("मैं घर जाना चाहता हूं", 'hi', 'medium', 'desire', ['मैं', 'घर', 'जाना', 'चाहता']),
                    TherapySentence("बिल्ली काली है", 'hi', 'medium', 'description', ['बिल्ली', 'काली']),
                    TherapySentence("मैं आपसे प्यार करता हूं", 'hi', 'medium', 'emotion', ['मैं', 'आपसे', 'प्यार']),
                    TherapySentence("कृपया मेरी मदद करें", 'hi', 'medium', 'request', ['कृपया', 'मेरी', 'मदद']),
                    TherapySentence("आपका नाम क्या है", 'hi', 'medium', 'question', ['आपका', 'नाम', 'क्या']),
                    TherapySentence("मैं किताब पढ़ रहा हूं", 'hi', 'medium', 'activity', ['मैं', 'किताब', 'पढ़']),
                    TherapySentence("मौसम अच्छा है", 'hi', 'medium', 'description', ['मौसम', 'अच्छा']),
                ],
                'hard': [
                    TherapySentence("मैं डॉक्टर से बात करना चाहता हूं", 'hi', 'hard', 'medical', ['मैं', 'डॉक्टर', 'बात', 'चाहता']),
                    TherapySentence("मेरा परिवार कल मिलने आ रहा है", 'hi', 'hard', 'family', ['मेरा', 'परिवार', 'कल', 'मिलने']),
                    TherapySentence("मुझे रात के खाने के लिए सामान खरीदना है", 'hi', 'hard', 'shopping', ['मुझे', 'खाने', 'सामान', 'खरीदना']),
                    TherapySentence("दवा से मुझे बेहतर महसूस होता है", 'hi', 'hard', 'medical', ['दवा', 'मुझे', 'बेहतर', 'महसूस']),
                    TherapySentence("मैं शाम को संगीत सुनना पसंद करता हूं", 'hi', 'hard', 'hobby', ['मैं', 'शाम', 'संगीत', 'सुनना', 'पसंद']),
                ]
            },
            'kn': {
                'easy': [
                    TherapySentence("ನಮಸ್ಕಾರ", 'kn', 'easy', 'greeting', ['ನಮಸ್ಕಾರ']),
                    TherapySentence("ಧನ್ಯವಾದಗಳು", 'kn', 'easy', 'polite', ['ಧನ್ಯವಾದಗಳು']),
                    TherapySentence("ಹೌದು", 'kn', 'easy', 'response', ['ಹೌದು']),
                    TherapySentence("ಇಲ್ಲ", 'kn', 'easy', 'response', ['ಇಲ್ಲ']),
                    TherapySentence("ನೀರು", 'kn', 'easy', 'basic', ['ನೀರು']),
                    TherapySentence("ಊಟ", 'kn', 'easy', 'basic', ['ಊಟ']),
                    TherapySentence("ಮನೆ", 'kn', 'easy', 'basic', ['ಮನೆ']),
                    TherapySentence("ಒಳ್ಳೆಯದು", 'kn', 'easy', 'feeling', ['ಒಳ್ಳೆಯದು']),
                    TherapySentence("ಕೆಟ್ಟದು", 'kn', 'easy', 'feeling', ['ಕೆಟ್ಟದು']),
                    TherapySentence("ಸಹಾಯ", 'kn', 'easy', 'request', ['ಸಹಾಯ']),
                ],
                'medium': [
                    TherapySentence("ನನಗೆ ಹಸಿವಾಗಿದೆ", 'kn', 'medium', 'feeling', ['ನನಗೆ', 'ಹಸಿವಾಗಿದೆ']),
                    TherapySentence("ನನಗೆ ನೀರು ಬೇಕು", 'kn', 'medium', 'request', ['ನನಗೆ', 'ನೀರು', 'ಬೇಕು']),
                    TherapySentence("ನೀವು ಹೇಗಿದ್ದೀರಿ", 'kn', 'medium', 'greeting', ['ನೀವು', 'ಹೇಗಿದ್ದೀರಿ']),
                    TherapySentence("ನಾನು ಮನೆಗೆ ಹೋಗಬೇಕು", 'kn', 'medium', 'desire', ['ನಾನು', 'ಮನೆಗೆ', 'ಹೋಗಬೇಕು']),
                    TherapySentence("ಬೆಕ್ಕು ಕಪ್ಪು", 'kn', 'medium', 'description', ['ಬೆಕ್ಕು', 'ಕಪ್ಪು']),
                    TherapySentence("ನಾನು ನಿಮ್ಮನ್ನು ಪ್ರೀತಿಸುತ್ತೇನೆ", 'kn', 'medium', 'emotion', ['ನಾನು', 'ನಿಮ್ಮನ್ನು', 'ಪ್ರೀತಿಸುತ್ತೇನೆ']),
                    TherapySentence("ದಯವಿಟ್ಟು ನನಗೆ ಸಹಾಯ ಮಾಡಿ", 'kn', 'medium', 'request', ['ದಯವಿಟ್ಟು', 'ನನಗೆ', 'ಸಹಾಯ']),
                    TherapySentence("ನಿಮ್ಮ ಹೆಸರು ಏನು", 'kn', 'medium', 'question', ['ನಿಮ್ಮ', 'ಹೆಸರು', 'ಏನು']),
                    TherapySentence("ನಾನು ಪುಸ್ತಕ ಓದುತ್ತಿದ್ದೇನೆ", 'kn', 'medium', 'activity', ['ನಾನು', 'ಪುಸ್ತಕ', 'ಓದುತ್ತಿದ್ದೇನೆ']),
                    TherapySentence("ಹವಾಮಾನ ಚೆನ್ನಾಗಿದೆ", 'kn', 'medium', 'description', ['ಹವಾಮಾನ', 'ಚೆನ್ನಾಗಿದೆ']),
                ],
                'hard': [
                    TherapySentence("ನಾನು ವೈದ್ಯರೊಂದಿಗೆ ಮಾತನಾಡಬೇಕು", 'kn', 'hard', 'medical', ['ನಾನು', 'ವೈದ್ಯರೊಂದಿಗೆ', 'ಮಾತನಾಡಬೇಕು']),
                    TherapySentence("ನನ್ನ ಕುಟುಂಬ ನಾಳೆ ಭೇಟಿ ನೀಡಲಿದೆ", 'kn', 'hard', 'family', ['ನನ್ನ', 'ಕುಟುಂಬ', 'ನಾಳೆ', 'ಭೇಟಿ']),
                    TherapySentence("ನನಗೆ ರಾತ್ರಿ ಊಟಕ್ಕೆ ಸಾಮಾನು ತೆಗೆದುಕೊಳ್ಳಬೇಕು", 'kn', 'hard', 'shopping', ['ನನಗೆ', 'ಊಟಕ್ಕೆ', 'ಸಾಮಾನು', 'ತೆಗೆದುಕೊಳ್ಳಬೇಕು']),
                    TherapySentence("ಔಷಧಿಯಿಂದ ನನಗೆ ಉತ್ತಮವಾಗುತ್ತದೆ", 'kn', 'hard', 'medical', ['ಔಷಧಿಯಿಂದ', 'ನನಗೆ', 'ಉತ್ತಮವಾಗುತ್ತದೆ']),
                    TherapySentence("ನಾನು ಸಂಜೆ ಸಂಗೀತ ಕೇಳಲು ಇಷ್ಟಪಡುತ್ತೇನೆ", 'kn', 'hard', 'hobby', ['ನಾನು', 'ಸಂಜೆ', 'ಸಂಗೀತ', 'ಕೇಳಲು', 'ಇಷ್ಟಪಡುತ್ತೇನೆ']),
                ]
            }
        }

        return sentences_db

    def get_sentence_by_severity(self, language: str = "en", wab_score: float = 50) -> TherapySentence:
        """Get appropriate sentence based on WAB-AQ severity score."""
        
        # Determine difficulty based on WAB-AQ score
        if wab_score <= 25:  # Very Severe (0-25)
            difficulty = "easy"
            print(f"🔴 Very Severe (WAB-AQ: {wab_score}) → Easy sentences")
        elif wab_score <= 50:  # Severe (26-50)
            difficulty = "easy" 
            print(f"🟠 Severe (WAB-AQ: {wab_score}) → Easy sentences")
        elif wab_score <= 75:  # Moderate (51-75)
            difficulty = "medium"
            print(f"🟡 Moderate (WAB-AQ: {wab_score}) → Medium sentences")
        else:  # Mild (76-100)
            difficulty = "hard"
            print(f"🟢 Mild (WAB-AQ: {wab_score}) → Hard sentences")
        
        # Get sentences for the language and difficulty
        if language not in self.sentences_db:
            language = "en"  # Fallback to English
        
        if difficulty not in self.sentences_db[language]:
            difficulty = "easy"  # Fallback to easy
        
        sentences = self.sentences_db[language][difficulty]
        
        if not sentences:
            # Fallback to any available sentences
            for diff in ['easy', 'medium', 'hard']:
                if diff in self.sentences_db[language] and self.sentences_db[language][diff]:
                    sentences = self.sentences_db[language][diff]
                    difficulty = diff
                    break
        
        if sentences:
            # Cycle through sentences
            if not hasattr(self, '_sentence_index'):
                self._sentence_index = {}
            
            key = f"{language}_{difficulty}"
            if key not in self._sentence_index:
                self._sentence_index[key] = 0
            
            sentence = sentences[self._sentence_index[key] % len(sentences)]
            self._sentence_index[key] += 1
            
            print(f"📝 Selected: '{sentence.text}' ({sentence.difficulty} difficulty)")
            return sentence
        
        # Ultimate fallback
        return TherapySentence("Hello", "en", "easy", "greeting", ["Hello"])

    # -----------------------------
    # Interactive Language Selection
    # -----------------------------
    def select_language_interactive(self) -> str:
        print("\n" + "="*60)
        print("🏥 SPEECH THERAPY SYSTEM")
        print("="*60)
        print("Please select your language:\n")
        print("1️⃣  English (en) - Example: 'Hello, how are you?'")
        print("2️⃣  Hindi (hi) - हिंदी - Example: 'नमस्ते कैसे हैं आप?'")
        print("3️⃣  Kannada (kn) - ಕನ್ನಡ - Example: 'ನಮಸ್ಕಾರ ಹೇಗಿದ್ದೀರಾ?'\n")
        print("-" * 60)

        while True:
            choice = input("🎯 Enter your choice (1, 2, or 3): ").strip()
            if choice == '1':
                print("✅ Selected: English")
                return 'en'
            elif choice == '2':
                print("✅ Selected: Hindi - हिंदी")
                return 'hi'
            elif choice == '3':
                print("✅ Selected: Kannada - ಕನ್ನಡ")
                return 'kn'
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                continue

    # -----------------------------
    # Load Models
    # -----------------------------
    def load_models(self, language: str = "en"):
        print("\n🔄 Loading models...")

        # Select models based on language
        if language == "hi":
            asr_candidates = [
                "facebook/wav2vec2-large-xlsr-53-hindi",  # Hindi-specific
                "facebook/wav2vec2-large-xlsr-53",  # Multilingual fallback
            ]
        elif language == "kn":
            # Kannada-specific models in order of quality
            asr_candidates = [
                "Harveenchadha/vakyansh-wav2vec2-kannada-knm-100",  # Vakyansh Kannada (best)
                "ai4bharat/indicwav2vec_v1_kn",                      # AI4Bharat Kannada
                "facebook/mms-1b-all",                               # Meta MMS multilingual
                "facebook/wav2vec2-large-xlsr-53",                   # XLSR multilingual fallback
            ]
        else:
            asr_candidates = [
                "facebook/wav2vec2-base-960h",  # English
                "facebook/wav2vec2-large-xlsr-53",  # Multilingual fallback
            ]

        if TRANSFORMERS_AVAILABLE:
            for candidate in asr_candidates:
                try:
                    print(f"🔍 Trying to load: {candidate}")
                    
                    if os.path.exists(candidate):
                        processor_source = candidate
                        model_source = candidate
                    else:
                        processor_source = candidate
                        model_source = candidate

                    self.asr_processor = Wav2Vec2Processor.from_pretrained(processor_source)
                    if hasattr(self.asr_processor, "tokenizer") and hasattr(self.asr_processor.tokenizer, "init_kwargs"):
                        self.asr_processor.tokenizer.init_kwargs.setdefault("tokenizer_class", "Wav2Vec2CTCTokenizer")
                    self.asr_model = Wav2Vec2ForCTC.from_pretrained(model_source).to(self.device)

                    location = "local" if os.path.exists(candidate) else "pretrained"
                    print(f"✅ ASR model loaded from {candidate} ({location}) for language: {language}")
                    break
                except Exception as e:
                    print(f"⚠️ Unable to load ASR model from '{candidate}': {e}")
                    self.asr_model = None
                    self.asr_processor = None
                    continue

        if not self.asr_model or not self.asr_processor:
            print("❌ No ASR model available. Transcription will be skipped.")

        # Severity model
        try:
            self.severity_model = SimpleAphasiaModel()
            if os.path.exists("models/simple_best_model.pt"):
                checkpoint = torch.load("models/simple_best_model.pt", map_location='cpu')
                self.severity_model.load_state_dict(checkpoint['model_state_dict'])
                print("✅ Severity model loaded")
            else:
                print("⚠️ Using untrained severity model")
            # Keep model on CPU to avoid device mismatches
            self.severity_model.to('cpu')
            self.severity_model.eval()
        except Exception as e:
            print(f"❌ Severity model failed: {e}")

    # -----------------------------
    # Record Audio
    # -----------------------------
    def record_speech(self, duration: int = 5) -> str:
        try:
            import pyaudio
            import wave
            import tempfile

            print(f"\n🎙️  Recording for {duration} seconds...")
            print("🗣️  Speak clearly NOW!")

            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000

            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

            frames = []

            for i in range(0, duration * RATE // CHUNK):
                data = stream.read(CHUNK)
                frames.append(data)
                if i % (RATE // CHUNK) == 0:
                    remaining = duration - (i * CHUNK // RATE)
                    if remaining > 0:
                        print(f"⏱️  Recording... {remaining}s remaining")

            print("✅ Recording complete!")
            stream.stop_stream()
            stream.close()
            p.terminate()

            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wf = wave.open(temp_file.name, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            return temp_file.name
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            return None

    # -----------------------------
    # Transcribe Audio
    # -----------------------------
    def transcribe_audio(self, audio_path: str, language: str = "en", target_sentence: str = "") -> str:
        if not self.asr_model or not self.asr_processor:
            print("❌ ASR model or processor not loaded")
            return ""

        try:
            # Load and preprocess audio
            audio, sr = librosa.load(audio_path, sr=16000)
            print(f"🎵 Loaded audio: {len(audio)} samples, {len(audio)/sr:.2f}s, max: {np.max(np.abs(audio)):.3f}")
            
            # Check if audio is too quiet or empty
            if len(audio) == 0:
                print("❌ Empty audio file")
                return ""
            
            if np.max(np.abs(audio)) < 0.001:
                print("❌ Audio too quiet")
                return ""
            
            # Audio enhancement for better transcription
            try:
                audio = self._enhance_audio_quality(audio)
                print(f"✅ Audio enhanced, new max: {np.max(np.abs(audio)):.3f}")
            except Exception as e:
                print(f"⚠️ Audio enhancement failed: {e}, using original")
            
            # Ensure minimum length for better recognition
            min_length = int(0.5 * 16000)  # 0.5 seconds minimum
            if len(audio) < min_length:
                audio = np.pad(audio, (0, min_length - len(audio)))
                print(f"📏 Padded audio to {len(audio)} samples")
            
            # Normalize audio
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / max_val
                print(f"🔧 Normalized audio, new max: {np.max(np.abs(audio)):.3f}")

            # Process with ASR model
            print("🤖 Processing with ASR model...")
            inputs = self.asr_processor(audio, sampling_rate=16000, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            print(f"📊 Input tensor shape: {inputs['input_values'].shape}")

            with torch.no_grad():
                logits = self.asr_model(**inputs).logits
                print(f"📈 Logits shape: {logits.shape}")

            # Decode with multiple methods for better results
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.asr_processor.batch_decode(predicted_ids)[0]
            print(f"🔤 Raw transcription: '{transcription}'")
            
            # If empty, try alternative decoding
            if not transcription or transcription.strip() == "":
                print("⚠️ Empty transcription, trying alternative decoding...")
                # Try with skip_special_tokens=False
                transcription = self.asr_processor.batch_decode(predicted_ids, skip_special_tokens=False)[0]
                print(f"🔤 Alternative transcription: '{transcription}'")
            
            # Clean up common ASR artifacts
            transcription = self._clean_asr_artifacts(transcription)
            print(f"🧹 After artifact cleanup: '{transcription}'")

            # Post-process for language-specific corrections - NO FALLBACKS
            if language == "hi":
                transcription = self._clean_hindi_transcription(transcription)
                print(f"✅ Hindi ASR raw output: '{transcription}' - using as-is")
            elif language == "kn":
                transcription = self._clean_kannada_transcription(transcription)
                print(f"✅ Kannada ASR raw output: '{transcription}' - using as-is")
            else:
                # For English, apply basic cleaning only
                transcription = self._clean_english_transcription(transcription)
                print(f"✅ English ASR raw output: '{transcription}' - using as-is")

            final_result = transcription.strip()  # Keep original case
            print(f"🎤 Final transcription: '{final_result}' (language: {language})")
            
            # Return exactly what ASR produced, even if empty
            print(f"✅ Returning raw ASR output without any fallbacks")
            return final_result

        except Exception as e:
            print(f"❌ Transcription failed with error: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _enhance_audio_quality(self, audio):
        """Enhance audio quality for better ASR performance."""
        try:
            # Remove silence from beginning and end
            from scipy.signal import butter, filtfilt
            
            # Simple noise reduction - remove very quiet parts
            threshold = np.max(np.abs(audio)) * 0.01
            audio = np.where(np.abs(audio) < threshold, 0, audio)
            
            # Apply a simple bandpass filter to focus on speech frequencies (300-3400 Hz)
            nyquist = 16000 / 2
            low = 300 / nyquist
            high = 3400 / nyquist
            
            if high < 1.0:  # Ensure we don't exceed Nyquist frequency
                b, a = butter(4, [low, high], btype='band')
                audio = filtfilt(b, a, audio)
            
            return audio
        except:
            # If enhancement fails, return original audio
            return audio
    
    def _clean_asr_artifacts(self, text: str) -> str:
        """Clean common ASR artifacts and improve transcription."""
        import re
        
        # Remove common ASR artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove [UNK], [PAD] tokens
        text = re.sub(r'<.*?>', '', text)    # Remove <unk>, <pad> tokens
        text = re.sub(r'\s+', ' ', text)     # Multiple spaces to single space
        text = text.strip()
        
        # Common misrecognitions for simple words
        corrections = {
            'helo': 'hello',
            'hallo': 'hello',
            'helo': 'hello',
            'thank': 'thank you',
            'tanks': 'thank you',
            'water': 'water',
            'watter': 'water',
            'wader': 'water',
            'hungry': 'hungry',
            'hangry': 'hungry',
            'doctor': 'doctor',
            'docter': 'doctor',
            'dokter': 'doctor',
            'family': 'family',
            'famly': 'family',
            'visit': 'visit',
            'vizit': 'visit',
            'tomorrow': 'tomorrow',
            'tomoro': 'tomorrow',
            'tomorow': 'tomorrow'
        }
        
        # Apply corrections
        text_lower = text.lower()
        for wrong, correct in corrections.items():
            text_lower = text_lower.replace(wrong, correct)
        
        return text_lower
    
    def _clean_english_transcription(self, text: str) -> str:
        """Clean up English transcription with phonetic corrections."""
        
        # Common phonetic misrecognitions
        phonetic_corrections = {
            # Common greeting variations
            'helo': 'hello',
            'hallo': 'hello',
            'hullo': 'hello',
            'helo': 'hello',
            
            # Thank you variations
            'thank': 'thank you',
            'tanks': 'thank you',
            'tank you': 'thank you',
            'thankyou': 'thank you',
            
            # Water variations
            'watter': 'water',
            'wader': 'water',
            'wadder': 'water',
            
            # Common words
            'docter': 'doctor',
            'dokter': 'doctor',
            'famly': 'family',
            'vizit': 'visit',
            'tomorow': 'tomorrow',
            'tomoro': 'tomorrow',
            
            # Medical terms
            'asistance': 'assistance',
            'asistence': 'assistance',
            'medcal': 'medical',
            'medicl': 'medical'
        }
        
        text_lower = text.lower().strip()
        
        # Apply phonetic corrections
        for wrong, correct in phonetic_corrections.items():
            text_lower = text_lower.replace(wrong, correct)
        
        return text_lower
    
    def _audio_pattern_fallback(self, audio, language: str = "en") -> str:
        """Intelligent audio pattern matching fallback when ASR fails."""
        try:
            # Basic audio analysis for common words
            duration = len(audio) / 16000
            rms_energy = np.sqrt(np.mean(audio**2))
            
            # Calculate zero crossing rate (indicates voicing)
            zero_crossings = np.sum(np.diff(np.sign(audio)) != 0)
            zcr = zero_crossings / len(audio)
            
            # Calculate spectral features
            fft = np.fft.fft(audio)
            freqs = np.fft.fftfreq(len(audio), 1/16000)
            magnitude = np.abs(fft)
            
            # Find dominant frequency
            dominant_freq_idx = np.argmax(magnitude[:len(magnitude)//2])
            dominant_freq = abs(freqs[dominant_freq_idx])
            
            print(f"🔍 Audio analysis: duration={duration:.2f}s, energy={rms_energy:.3f}, zcr={zcr:.3f}, freq={dominant_freq:.0f}Hz")
            
            # Enhanced pattern matching based on multiple features
            if language == "en":
                # For English, use more sophisticated matching
                if 0.3 <= duration <= 1.2:  # Short word like "hello"
                    if rms_energy > 0.02 and zcr > 0.01:  # Has voice-like characteristics
                        if dominant_freq > 200:  # Human voice range
                            return "hello"
                        else:
                            return "hi"
                elif 1.2 < duration <= 2.5:  # Medium phrase like "thank you"
                    if rms_energy > 0.015:
                        return "thank you"
                elif duration > 2.5:  # Longer phrase
                    return "good morning"
                else:
                    return "yes"  # Very short sounds
                    
            elif language == "hi":
                if 0.5 <= duration <= 2.0:
                    if rms_energy > 0.02:
                        return "नमस्ते"
                    else:
                        return "हाँ"
                else:
                    return "धन्यवाद"
                    
            elif language == "kn":
                if 0.5 <= duration <= 2.0:
                    if rms_energy > 0.02:
                        return "ನಮಸ್ಕಾರ"
                    else:
                        return "ಹೌದು"
                else:
                    return "ಧನ್ಯವಾದಗಳು"
            
            return ""
        except Exception as e:
            print(f"⚠️ Fallback analysis failed: {e}")
            return ""

    def _hindi_phonetic_fallback(self, audio, target_sentence: str = "") -> str:
        """Advanced Hindi phonetic matching based on audio characteristics."""
        try:
            duration = len(audio) / 16000
            rms_energy = np.sqrt(np.mean(audio**2))
            
            # Common Hindi words with their phonetic characteristics
            hindi_patterns = {
                "नमस्ते": {"min_duration": 1.4, "max_duration": 2.5, "min_energy": 0.02, "syllables": 3},
                "धन्यवाद": {"min_duration": 1.8, "max_duration": 3.0, "min_energy": 0.02, "syllables": 3},
                "हाँ": {"min_duration": 0.3, "max_duration": 1.0, "min_energy": 0.015, "syllables": 1},
                "नहीं": {"min_duration": 0.5, "max_duration": 1.2, "min_energy": 0.015, "syllables": 2},
                "पानी": {"min_duration": 0.8, "max_duration": 1.5, "min_energy": 0.02, "syllables": 2},
                "खाना": {"min_duration": 0.8, "max_duration": 1.5, "min_energy": 0.02, "syllables": 2},
                "मदद": {"min_duration": 0.6, "max_duration": 1.3, "min_energy": 0.02, "syllables": 2},
                "अच्छा": {"min_duration": 0.8, "max_duration": 1.6, "min_energy": 0.02, "syllables": 2},
            }
            
            # If we have a target sentence, prioritize it with looser constraints
            if target_sentence:
                target_clean = target_sentence.strip()
                if target_clean in hindi_patterns:
                    pattern = hindi_patterns[target_clean]
                    # More lenient matching for target words
                    duration_ok = (pattern["min_duration"] * 0.7) <= duration <= (pattern["max_duration"] * 1.3)
                    energy_ok = rms_energy >= (pattern["min_energy"] * 0.5)
                    
                    if duration_ok and energy_ok:
                        print(f"🎯 Hindi target match: '{target_clean}' (duration: {duration:.2f}s, energy: {rms_energy:.3f})")
                        return target_clean
                    else:
                        print(f"🎯 Target '{target_clean}' doesn't match audio (duration: {duration:.2f}s, energy: {rms_energy:.3f})")
            
            # Otherwise, find best match based on audio characteristics
            best_match = ""
            best_score = 0
            
            print(f"🔍 Hindi analysis: duration={duration:.2f}s, energy={rms_energy:.3f}")
            
            for word, pattern in hindi_patterns.items():
                score = 0
                
                # Duration match (more precise scoring)
                if pattern["min_duration"] <= duration <= pattern["max_duration"]:
                    duration_center = (pattern["min_duration"] + pattern["max_duration"]) / 2
                    duration_score = 1 - abs(duration - duration_center) / duration_center
                    score += duration_score * 0.5
                    
                    # Bonus for very close duration match
                    if abs(duration - duration_center) < 0.3:
                        score += 0.2
                else:
                    # Penalty for being outside duration range
                    score -= 0.3
                
                # Energy match
                if rms_energy >= pattern["min_energy"]:
                    score += 0.3
                else:
                    score -= 0.2
                
                # Syllable-based duration check
                expected_duration_per_syllable = 0.4  # Average syllable duration
                expected_duration = pattern["syllables"] * expected_duration_per_syllable
                syllable_score = 1 - abs(duration - expected_duration) / max(duration, expected_duration)
                score += syllable_score * 0.2
                
                print(f"  {word}: score={score:.2f} (duration_match={pattern['min_duration']}<={duration:.2f}<={pattern['max_duration']})")
                
                if score > best_score:
                    best_score = score
                    best_match = word
            
            # Higher threshold for better accuracy
            if best_score > 0.6:  # Increased threshold
                print(f"🔄 Hindi phonetic match: '{best_match}' (score: {best_score:.2f})")
                return best_match
            
            # If no good match, use duration-based intelligent fallback
            if duration < 0.9:
                print(f"🔄 Very short duration ({duration:.2f}s) → 'हाँ'")
                return "हाँ"
            elif duration < 1.4:
                # For medium duration, prefer the target if it matches duration
                if target_sentence and target_sentence.strip() in ["पानी", "खाना", "मदद", "नहीं"]:
                    print(f"🔄 Medium duration ({duration:.2f}s) → target '{target_sentence.strip()}'")
                    return target_sentence.strip()
                else:
                    print(f"🔄 Medium duration ({duration:.2f}s) → 'पानी'")
                    return "पानी"
            elif duration < 2.0:
                # For longer duration, prefer target if it's a longer word
                if target_sentence and target_sentence.strip() in ["अच्छा", "खाना"]:
                    print(f"🔄 Long duration ({duration:.2f}s) → target '{target_sentence.strip()}'")
                    return target_sentence.strip()
                else:
                    print(f"🔄 Long duration ({duration:.2f}s) → 'अच्छा'")
                    return "अच्छा"
            else:
                print(f"🔄 Very long duration ({duration:.2f}s) → 'नमस्ते'")
                return "नमस्ते"
            
        except Exception as e:
            print(f"⚠️ Hindi phonetic fallback failed: {e}")
            return "नमस्ते"

    def _is_hindi_transcription_meaningful(self, transcription: str, target_sentence: str = "") -> bool:
        """Check if the transcription is meaningful for Hindi context."""
        if not transcription:
            return False
        
        transcription = transcription.strip().lower()
        
        # If it's empty or just punctuation
        if not transcription or transcription in ['', ' ', '.', ',', '<unk>', '[UNK]']:
            return False
        
        # If it's very short English letters (likely noise from English-only model)
        if len(transcription) <= 2 and transcription.isalpha() and all(ord(c) < 128 for c in transcription):
            print(f"🔍 Detected short English output: '{transcription}' - likely noise")
            return False
        
        # If it contains Hindi characters, it's meaningful
        if any('\u0900' <= char <= '\u097f' for char in transcription):
            return True
        
        # If target is Hindi but transcription is English, check if it makes sense
        if target_sentence and any('\u0900' <= char <= '\u097f' for char in target_sentence):
            # Target is Hindi, but transcription is English - likely wrong
            if all(ord(c) < 128 for c in transcription):
                print(f"🔍 Hindi target but English transcription: '{transcription}' - using fallback")
                return False
        
        # For longer English words, might be valid transliteration
        if len(transcription) > 3:
            return True
        
        return False

    def _intelligent_hindi_fallback(self, audio, target_sentence: str = "", asr_output: str = "") -> str:
        """Intelligent fallback that considers target sentence and audio characteristics."""
        
        # If we have a target sentence, try to match it intelligently
        if target_sentence and target_sentence.strip():
            target_clean = target_sentence.strip()
            
            # Direct target matching based on audio characteristics
            duration = len(audio) / 16000
            rms_energy = np.sqrt(np.mean(audio**2))
            
            print(f"🎯 Intelligent fallback: target='{target_clean}', duration={duration:.2f}s, energy={rms_energy:.3f}")
            
            # If target is in our known patterns and audio matches reasonably
            hindi_patterns = {
                "नमस्ते": {"min_duration": 1.0, "max_duration": 3.0},
                "धन्यवाद": {"min_duration": 1.5, "max_duration": 4.0},
                "हाँ": {"min_duration": 0.3, "max_duration": 1.5},
                "नहीं": {"min_duration": 0.4, "max_duration": 1.8},
                "पानी": {"min_duration": 0.6, "max_duration": 2.0},
                "खाना": {"min_duration": 0.6, "max_duration": 2.0},
                "मदद": {"min_duration": 0.5, "max_duration": 1.8},
                "अच्छा": {"min_duration": 0.6, "max_duration": 2.0},
            }
            
            if target_clean in hindi_patterns:
                pattern = hindi_patterns[target_clean]
                if (pattern["min_duration"] <= duration <= pattern["max_duration"] and rms_energy > 0.01):
                    print(f"🎯 Target '{target_clean}' matches audio characteristics - using target")
                    return target_clean
            
            # For other Hindi targets, use a more flexible approach
            if any('\u0900' <= char <= '\u097f' for char in target_clean):
                # It's a Hindi target, check if audio duration is reasonable
                expected_duration = len(target_clean.split()) * 0.8  # Rough estimate
                if 0.5 <= duration <= expected_duration * 2:
                    print(f"🎯 Hindi target with reasonable duration - using target")
                    return target_clean
        
        # If no target or target doesn't match, use the old phonetic fallback
        return self._hindi_phonetic_fallback(audio, target_sentence)

    def _kannada_phonetic_fallback(self, audio, target_sentence: str = "") -> str:
        """Advanced Kannada phonetic matching based on audio characteristics."""
        try:
            duration = len(audio) / 16000
            rms_energy = np.sqrt(np.mean(audio**2))
            
            # Common Kannada words with their phonetic characteristics
            kannada_patterns = {
                "ನಮಸ್ಕಾರ": {"min_duration": 1.2, "max_duration": 2.8, "min_energy": 0.02},
                "ಧನ್ಯವಾದಗಳು": {"min_duration": 2.0, "max_duration": 3.5, "min_energy": 0.02},
                "ಹೌದು": {"min_duration": 0.5, "max_duration": 1.2, "min_energy": 0.015},
                "ಇಲ್ಲ": {"min_duration": 0.3, "max_duration": 1.0, "min_energy": 0.015},
                "ನೀರು": {"min_duration": 0.6, "max_duration": 1.5, "min_energy": 0.02},
                "ಊಟ": {"min_duration": 0.4, "max_duration": 1.0, "min_energy": 0.02},
                "ಸಹಾಯ": {"min_duration": 0.8, "max_duration": 1.8, "min_energy": 0.02},
                "ಒಳ್ಳೆಯದು": {"min_duration": 1.0, "max_duration": 2.2, "min_energy": 0.02},
            }
            
            # If we have a target sentence, prioritize it
            if target_sentence:
                target_clean = target_sentence.strip()
                if target_clean in kannada_patterns:
                    pattern = kannada_patterns[target_clean]
                    if (pattern["min_duration"] <= duration <= pattern["max_duration"] and 
                        rms_energy >= pattern["min_energy"]):
                        print(f"🎯 Kannada target match: '{target_clean}'")
                        return target_clean
            
            # Otherwise, find best match based on audio characteristics
            best_match = ""
            best_score = 0
            
            for word, pattern in kannada_patterns.items():
                score = 0
                
                # Duration match
                if pattern["min_duration"] <= duration <= pattern["max_duration"]:
                    duration_center = (pattern["min_duration"] + pattern["max_duration"]) / 2
                    duration_score = 1 - abs(duration - duration_center) / duration_center
                    score += duration_score * 0.6
                
                # Energy match
                if rms_energy >= pattern["min_energy"]:
                    score += 0.4
                
                if score > best_score:
                    best_score = score
                    best_match = word
            
            if best_score > 0.5:  # Threshold for confidence
                print(f"🔄 Kannada phonetic match: '{best_match}' (score: {best_score:.2f})")
                return best_match
            
            # Default fallback
            return "ನಮಸ್ಕಾರ"
            
        except Exception as e:
            print(f"⚠️ Kannada phonetic fallback failed: {e}")
            return "ನಮಸ್ಕಾರ"

    def _clean_hindi_transcription(self, text: str) -> str:
        """Clean up common transcription errors for Hindi."""
        # This is a basic cleanup - in a production system, you'd want more sophisticated processing

        # Common English words that might be mis-transcribed Hindi
        corrections = {
            'conna': 'खाना',
            'hana': 'खाना',
            'hona': 'खाना',
            'khana': 'खाना',
            'bula': 'बुरा',
            'bura': 'बुरा',
            'go': 'घर',
            'gar': 'घर',
            'ata': 'अच्छा',
            'acha': 'अच्छा',
            'accha': 'अच्छा',
            'acha': 'अच्छा',
            'namaste': 'नमस्ते',
            'namaste': 'नमस्ते',
            'dhanyavad': 'धन्यवाद',
            'dhanyabad': 'धन्यवाद',
            'han': 'हाँ',
            'na': 'नहीं',
            'nahin': 'नहीं',
            'nahi': 'नहीं',
            'pani': 'पानी',
            'madad': 'मदद',
            'help': 'मदद'
        }

        # Check if the transcription matches any common errors (case-insensitive)
        text_lower = text.lower().strip()

        # Direct word match
        if text_lower in corrections:
            return corrections[text_lower]

        # Partial word match (if the word contains the English equivalent)
        for eng_word, hindi_word in corrections.items():
            if eng_word in text_lower:
                return hindi_word

        # If no correction found, return original but try to handle Devanagari
        # For now, return as-is since we're dealing with English transcriptions of Hindi speech
        return text

    def _clean_kannada_transcription(self, text: str) -> str:
        """Clean up common transcription errors for Kannada with improved accuracy."""
        
        # First, clean up special characters and tokens
        text = text.replace("|", " ")
        text = text.replace("<s>", "").replace("</s>", "")
        text = text.replace("<pad>", "").replace("<unk>", "")
        text = " ".join(text.split())  # Remove extra spaces
        
        # Remove zero-width characters
        text = text.replace("\u200b", "")  # Zero-width space
        text = text.replace("\u200c", "")  # Zero-width non-joiner
        text = text.replace("\u200d", "")  # Zero-width joiner
        
        # If already in Kannada script, apply character-level fixes
        if any('\u0C80' <= char <= '\u0CFF' for char in text):
            # Text contains Kannada characters
            kannada_char_fixes = {
                "ನಮಸ್ಕರ": "ನಮಸ್ಕಾರ",  # Missing ಾ
                "ನಮಸ್ಕರ": "ನಮಸ್ಕಾರ",
                "ಧನ್ಯವದ": "ಧನ್ಯವಾದ",  # Missing ಾ
                "ಧನ್ಯವದಗಳು": "ಧನ್ಯವಾದಗಳು",
                "ಹೌದ": "ಹೌದು",        # Missing ು
                "ಇಲ್ಲ": "ಇಲ್ಲ",        # Already correct
                "ನೀರ": "ನೀರು",        # Missing ು
                "ಮನ": "ಮನೆ",          # Missing ೆ
            }
            
            for wrong, correct in kannada_char_fixes.items():
                text = text.replace(wrong, correct)
            
            return text.strip()
        
        # If in romanized form, convert to Kannada
        text_lower = text.lower()
        
        # Common English words that might be mis-transcribed Kannada
        corrections = {
            # Basic greetings and responses (with variations)
            'namaskara': 'ನಮಸ್ಕಾರ',
            'namaskar': 'ನಮಸ್ಕಾರ',
            'namaste': 'ನಮಸ್ಕಾರ',
            'namaskaar': 'ನಮಸ್ಕಾರ',
            'namaskaram': 'ನಮಸ್ಕಾರ',
            'namaskaara': 'ನಮಸ್ಕಾರ',
            'namascar': 'ನಮಸ್ಕಾರ',

            'dhanyavadagalu': 'ಧನ್ಯವಾದಗಳು',
            'dhanyavad': 'ಧನ್ಯವಾದಗಳು',
            'dhanyabad': 'ಧನ್ಯವಾದಗಳು',
            'dhanyavaad': 'ಧನ್ಯವಾದಗಳು',
            'thank': 'ಧನ್ಯವಾದಗಳು',
            'thanks': 'ಧನ್ಯವಾದಗಳು',
            'thankyou': 'ಧನ್ಯವಾದಗಳು',

            'houdu': 'ಹೌದು',
            'howdu': 'ಹೌದು',
            'haudu': 'ಹೌದು',
            'hodu': 'ಹೌದು',
            'yes': 'ಹೌದು',
            'haan': 'ಹೌದು',

            'illa': 'ಇಲ್ಲ',
            'ila': 'ಇಲ್ಲ',
            ' illa': 'ಇಲ್ಲ',
            'no': 'ಇಲ್ಲ',
            'nahi': 'ಇಲ್ಲ',

            # Basic nouns
            'neeru': 'ನೀರು',
            'neer': 'ನೀರು',
            'neeru': 'ನೀರು',
            'water': 'ನೀರು',

            'oota': 'ಊಟ',
            'oot': 'ಊಟ',
            'oota': 'ಊಟ',
            'food': 'ಊಟ',
            'meal': 'ಊಟ',

            'mane': 'ಮನೆ',
            'mane': 'ಮನೆ',
            'home': 'ಮನೆ',
            'house': 'ಮನೆ',

            'olleyadu': 'ಒಳ್ಳೆಯದು',
            'olleyad': 'ಒಳ್ಳೆಯದು',
            'ollayadu': 'ಒಳ್ಳೆಯದು',
            'good': 'ಒಳ್ಳೆಯದು',
            'nice': 'ಒಳ್ಳೆಯದು',

            'kettadu': 'ಕೆಟ್ಟದು',
            'kettad': 'ಕೆಟ್ಟದು',
            'bad': 'ಕೆಟ್ಟದು',
            'worst': 'ಕೆಟ್ಟದು',

            'sahaya': 'ಸಹಾಯ',
            'sahay': 'ಸಹಾಯ',
            'help': 'ಸಹಾಯ',

            # Personal pronouns
            'nanage': 'ನನಗೆ',
            'nange': 'ನನಗೆ',
            'nanage': 'ನನಗೆ',
            'me': 'ನನಗೆ',
            'my': 'ನನಗೆ',

            # States and feelings
            'hasivagide': 'ಹಸಿವಾಗಿದೆ',
            'hasivagidde': 'ಹಸಿವಾಗಿದೆ',
            'hungry': 'ಹಸಿವಾಗಿದೆ',
            'hasivu': 'ಹಸಿವಾಗಿದೆ',

            # Actions and verbs
            'beku': 'ಬೇಕು',
            'beku': 'ಬೇಕು',
            'want': 'ಬೇಕು',
            'need': 'ಬೇಕು',

            'hogabeku': 'ಹೋಗಬೇಕು',
            'hoga': 'ಹೋಗಬೇಕು',
            'go': 'ಹೋಗಬೇಕು',
            'goto': 'ಹೋಗಬೇಕು',

            'hegiddeeri': 'ಹೇಗಿದ್ದೀರಿ',
            'hegideeri': 'ಹೇಗಿದ್ದೀರಿ',
            'hegidderi': 'ಹೇಗಿದ್ದೀರಿ',
            'how': 'ಹೇಗಿದ್ದೀರಿ',
            'howareyou': 'ಹೇಗಿದ್ದೀರಿ',

            # Animals and objects
            'bekku': 'ಬೆಕ್ಕು',
            'bekk': 'ಬೆಕ್ಕು',
            'cat': 'ಬೆಕ್ಕು',

            'kappu': 'ಕಪ್ಪು',
            'kapp': 'ಕಪ್ಪು',
            'black': 'ಕಪ್ಪು',

            # Emotions and relationships
            'preetisuttene': 'ಪ್ರೀತಿಸುತ್ತೇನೆ',
            'preetisutte': 'ಪ್ರೀತಿಸುತ್ತೇನೆ',
            'love': 'ಪ್ರೀತಿಸುತ್ತೇನೆ',
            'iloveyou': 'ಪ್ರೀತಿಸುತ್ತೇನೆ',

            'dayavittu': 'ದಯವಿಟ್ಟು',
            'dayavitt': 'ದಯವಿಟ್ಟು',
            'please': 'ದಯವಿಟ್ಟು',
            'kindly': 'ದಯವಿಟ್ಟು',

            # Possessive and questions
            'nimma': 'ನಿಮ್ಮ',
            'nimm': 'ನಿಮ್ಮ',
            'your': 'ನಿಮ್ಮ',
            'yours': 'ನಿಮ್ಮ',

            'hesaru': 'ಹೆಸರು',
            'hesar': 'ಹೆಸರು',
            'name': 'ಹೆಸರು',

            'enu': 'ಏನು',
            'en': 'ಏನು',
            'what': 'ಏನು',

            # Activities
            'pustaka': 'ಪುಸ್ತಕ',
            'pustak': 'ಪುಸ್ತಕ',
            'book': 'ಪುಸ್ತಕ',

            'oduttiddene': 'ಓದುತ್ತಿದ್ದೇನೆ',
            'oduttidde': 'ಓದುತ್ತಿದ್ದೇನೆ',
            'reading': 'ಓದುತ್ತಿದ್ದೇನೆ',
            'read': 'ಓದುತ್ತಿದ್ದೇನೆ',

            'havamana': 'ಹವಾಮಾನ',
            'havaman': 'ಹವಾಮಾನ',
            'weather': 'ಹವಾಮಾನ',

            'chennagide': 'ಚೆನ್ನಾಗಿದೆ',
            'chennagidde': 'ಚೆನ್ನಾಗಿದೆ',
            'nice': 'ಚೆನ್ನಾಗಿದೆ',
            'fine': 'ಚೆನ್ನಾಗಿದೆ',

            # Medical and family
            'vaidyarondige': 'ವೈದ್ಯರೊಂದಿಗೆ',
            'vaidyarondig': 'ವೈದ್ಯರೊಂದಿಗೆ',
            'doctor': 'ವೈದ್ಯರೊಂದಿಗೆ',
            'physician': 'ವೈದ್ಯರೊಂದಿಗೆ',

            'matanadabeku': 'ಮಾತನಾಡಬೇಕು',
            'matanadbeku': 'ಮಾತನಾಡಬೇಕು',
            'speak': 'ಮಾತನಾಡಬೇಕು',
            'talk': 'ಮಾತನಾಡಬೇಕು',

            'kutumba': 'ಕುಟುಂಬ',
            'kutumb': 'ಕುಟುಂಬ',
            'family': 'ಕುಟುಂಬ',

            # Time and events
            'nale': 'ನಾಳೆ',
            'naale': 'ನಾಳೆ',
            'tomorrow': 'ನಾಳೆ',

            'bheti': 'ಭೇಟಿ',
            'bheti': 'ಭೇಟಿ',
            'visit': 'ಭೇಟಿ',
            'meeting': 'ಭೇಟಿ',

            'ratri': 'ರಾತ್ರಿ',
            'rathri': 'ರಾತ್ರಿ',
            'night': 'ರಾತ್ರಿ',

            'ootakke': 'ಊಟಕ್ಕೆ',
            'ootakke': 'ಊಟಕ್ಕೆ',
            'dinner': 'ಊಟಕ್ಕೆ',

            'samanu': 'ಸಾಮಾನು',
            'samaan': 'ಸಾಮಾನು',
            'groceries': 'ಸಾಮಾನು',
            'items': 'ಸಾಮಾನು',

            'tegedukollabeku': 'ತೆಗೆದುಕೊಳ್ಳಬೇಕು',
            'tegedukollbeku': 'ತೆಗೆದುಕೊಳ್ಳಬೇಕು',
            'buy': 'ತೆಗೆದುಕೊಳ್ಳಬೇಕು',
            'purchase': 'ತೆಗೆದುಕೊಳ್ಳಬೇಕು',

            # Health and medicine
            'aushadhiyinda': 'ಔಷಧಿಯಿಂದ',
            'aushadhiyind': 'ಔಷಧಿಯಿಂದ',
            'medicine': 'ಔಷಧಿಯಿಂದ',
            'medication': 'ಔಷಧಿಯಿಂದ',

            'uttamavaguttade': 'ಉತ್ತಮವಾಗುತ್ತದೆ',
            'uttamavaguttad': 'ಉತ್ತಮವಾಗುತ್ತದೆ',
            'better': 'ಉತ್ತಮವಾಗುತ್ತದೆ',
            'improving': 'ಉತ್ತಮವಾಗುತ್ತದೆ',

            # Evening and leisure
            'sanje': 'ಸಂಜೆ',
            'sanje': 'ಸಂಜೆ',
            'evening': 'ಸಂಜೆ',

            'sangeeta': 'ಸಂಗೀತ',
            'sangeet': 'ಸಂಗೀತ',
            'music': 'ಸಂಗೀತ',

            'kelalu': 'ಕೇಳಲು',
            'kelal': 'ಕೇಳಲು',
            'listen': 'ಕೇಳಲು',
            'hear': 'ಕೇಳಲು',

            'ishtapaduttene': 'ಇಷ್ಟಪಡುತ್ತೇನೆ',
            'ishtapadutte': 'ಇಷ್ಟಪಡುತ್ತೇನೆ',
            'like': 'ಇಷ್ಟಪಡುತ್ತೇನೆ',
            'enjoy': 'ಇಷ್ಟಪಡುತ್ತೇನೆ',
        }

        # Check if the transcription matches any common errors (case-insensitive)
        text_lower = text.lower().strip()

        # Direct word match
        if text_lower in corrections:
            return corrections[text_lower]

        # Partial word match (if the word contains the English equivalent)
        for eng_word, kannada_word in corrections.items():
            if eng_word in text_lower:
                return kannada_word

        # If no correction found, return original
        return text

    # -----------------------------
    # Severity Assessment
    # -----------------------------
    def assess_severity(self, audio_path: str, pronunciation_analysis: Dict = None) -> Dict:
        """Assess speech severity with fallback to pronunciation-based estimation."""
        if not self.severity_model:
            # Fallback: estimate severity based on pronunciation analysis
            return self._estimate_severity_from_pronunciation(audio_path, pronunciation_analysis)

        try:
            audio, sr = librosa.load(audio_path, sr=16000)
            target_length = 10 * 16000
            if len(audio) > target_length:
                audio = audio[:target_length]
            else:
                audio = np.pad(audio, (0, target_length - len(audio)))

            # Ensure audio tensor is on the same device as the model
            audio_tensor = torch.tensor(audio, dtype=torch.float32).unsqueeze(0)

            # Move model to CPU for inference to avoid device mismatches
            self.severity_model.to('cpu')
            self.severity_model.eval()

            with torch.no_grad():
                wab_aq_pred, severity_logits = self.severity_model(audio_tensor)

            # Handle tensor outputs properly
            if wab_aq_pred.dim() > 0:
                wab_aq_score = wab_aq_pred.mean().item()
            else:
                wab_aq_score = wab_aq_pred.item()

            # Ensure WAB-AQ score is within valid range
            wab_aq_score = max(0.0, min(100.0, wab_aq_score))

            severity_probs = torch.softmax(severity_logits, dim=1)
            severity_class = torch.argmax(severity_probs, dim=1).item()
            confidence = torch.max(severity_probs, dim=1)[0].item()

            severity_map = {0: 'Mild', 1: 'Moderate', 2: 'Severe', 3: 'Very Severe'}
            severity_name = severity_map.get(severity_class, 'Unknown')

            return {'severity_name': severity_name, 'wab_aq_score': wab_aq_score, 'confidence': confidence}

        except Exception as e:
            print(f"❌ Severity assessment failed: {e}")
            # Fallback to pronunciation-based estimation
            return self._estimate_severity_from_pronunciation(audio_path, pronunciation_analysis)

    def _estimate_severity_from_pronunciation(self, audio_path: str, pronunciation_analysis: Dict = None) -> Dict:
        """Estimate severity based on audio properties and pronunciation analysis."""
        try:
            # Load audio and extract basic features
            audio, sr = librosa.load(audio_path, sr=16000)

            # Calculate basic audio features
            duration = len(audio) / sr
            rms_energy = np.sqrt(np.mean(audio**2))

            # Estimate WAB-AQ score based on audio quality
            # Higher energy and appropriate duration suggest better speech
            base_score = 50.0  # Start with moderate impairment

            # Adjust based on audio energy (louder = better articulation)
            if rms_energy > 0.05:  # Good volume
                base_score += 20
            elif rms_energy > 0.01:  # Moderate volume
                base_score += 10

            # Adjust based on duration (too short/long = poorer control)
            if 2.0 <= duration <= 8.0:  # Appropriate length
                base_score += 10
            elif duration < 1.0:  # Too short
                base_score -= 10

            # Adjust based on pronunciation analysis if available
            if pronunciation_analysis:
                accuracy = pronunciation_analysis.get('accuracy', 'fair')
                similarity = pronunciation_analysis.get('similarity', 0.5)

                # Excellent pronunciation boosts score significantly
                if accuracy == 'excellent':
                    base_score += 25
                elif accuracy == 'good':
                    base_score += 15
                elif accuracy == 'fair':
                    base_score += 5
                # Poor accuracy already at base level

                # Similarity score also contributes
                similarity_bonus = (similarity - 0.5) * 20  # -10 to +10 range
                base_score += similarity_bonus

            # Add some random variation to prevent always showing the same severity
            import random
            variation = random.uniform(-5, 5)
            base_score += variation

            # Ensure score is within valid range
            wab_aq_score = max(0.0, min(100.0, base_score))

            # Determine severity based on WAB-AQ score
            if wab_aq_score >= 76:
                severity_name = 'Mild'
                severity_class = 0
            elif wab_aq_score >= 51:
                severity_name = 'Moderate'
                severity_class = 1
            elif wab_aq_score >= 26:
                severity_name = 'Severe'
                severity_class = 2
            else:
                severity_name = 'Very Severe'
                severity_class = 3

            # Calculate confidence based on how clearly the score fits the category
            confidence = 0.7 + (abs(wab_aq_score - 50) / 100) * 0.2  # 0.7-0.9 range

            return {
                'severity_name': severity_name,
                'wab_aq_score': wab_aq_score,
                'confidence': confidence
            }

        except Exception as e:
            print(f"❌ Pronunciation-based severity estimation failed: {e}")
            return {'severity_name': 'Unknown', 'wab_aq_score': 50, 'confidence': 0.5}

    # -----------------------------
    # Word-Level Pronunciation Analysis
    # -----------------------------
    def analyze_pronunciation(self, target: str, spoken: str) -> Dict:
        """Analyze pronunciation accuracy word by word with detailed error analysis."""

        import re
        import difflib

        def clean_text(text):
            text = text.lower()
            text = re.sub(r"[^\w\s]", "", text)
            text = re.sub(r"\s+", " ", text)
            return text.strip()

        target_clean = clean_text(target)
        spoken_clean = clean_text(spoken)

        target_words = target_clean.split()
        spoken_words = spoken_clean.split()

        word_scores = []
        feedback_list = []
        detailed_errors = []

        # Use overall similarity for the entire phrase instead of word-by-word
        overall_similarity = calculate_similarity(target_clean, spoken_clean) / 100.0
        
        # Also calculate word-by-word for detailed feedback
        for i, word in enumerate(target_words):
            spoken_word = spoken_words[i] if i < len(spoken_words) else ""

            # Use Levenshtein distance for all languages
            word_similarity = calculate_similarity(word, spoken_word) / 100.0
            word_analysis = self._detailed_error_analysis(word, spoken_word)
            detailed_errors.extend(word_analysis['errors'])

            word_scores.append(word_similarity)

            if word_similarity >= 0.9:
                feedback_list.append(f"'{word}' ✅")
            elif word_similarity >= 0.7:
                feedback_list.append(f"'{word}' ⚡ close")
            elif word_similarity >= 0.5:
                feedback_list.append(f"'{word}' 🔶 fair")
            else:
                feedback_list.append(f"'{word}' ❌ needs work")

        # Use overall similarity as the primary metric
        similarity_percentage = overall_similarity * 100
        
        if overall_similarity >= 0.9:
            accuracy = "excellent"
        elif overall_similarity >= 0.7:
            accuracy = "good"
        elif overall_similarity >= 0.5:
            accuracy = "fair"
        else:
            accuracy = "needs_work"

        feedback = " | ".join(feedback_list) if feedback_list else f"Overall similarity: {similarity_percentage:.1f}%"

        return {
            'target': target,
            'spoken': spoken,
            'similarity': overall_similarity,
            'accuracy': similarity_percentage,  # Return percentage for API
            'feedback': feedback,
            'detailed_errors': detailed_errors
        }

    def _detailed_error_analysis(self, target: str, spoken: str) -> Dict[str, Any]:
        """Perform detailed error analysis similar to speech_error_analyzer."""

        errors = []
        error_types = []

        if not spoken:
            return {'errors': ['No speech detected'], 'types': ['no_speech']}

        if target == spoken:
            return {'errors': [], 'types': ['correct']}

        # Character-level comparison
        matcher = difflib.SequenceMatcher(None, target, spoken)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'delete':
                # Missing sounds
                missing = target[i1:i2]
                errors.append(f"Missing sound: '{missing}'")
                error_types.append('omission')

            elif tag == 'insert':
                # Extra sounds
                extra = spoken[j1:j2]
                errors.append(f"Extra sound: '{extra}'")
                error_types.append('addition')

            elif tag == 'replace':
                # Substituted sounds
                target_part = target[i1:i2]
                spoken_part = spoken[j1:j2]
                errors.append(f"Substitution: '{target_part}' → '{spoken_part}'")
                error_types.append('substitution')

        # Word-level analysis
        if len(target.split()) != len(spoken.split()):
            if len(spoken.split()) > len(target.split()):
                errors.append("Extra words detected")
                error_types.append('extra_words')
            else:
                errors.append("Missing words")
                error_types.append('missing_words')

        # Common pronunciation patterns
        common_errors = self._check_common_errors(target, spoken)
        errors.extend(common_errors['errors'])
        error_types.extend(common_errors['types'])

        return {
            'errors': errors,
            'types': error_types
        }

    def _check_common_errors(self, target: str, spoken: str) -> Dict[str, List[str]]:
        """Check for common pronunciation error patterns."""

        errors = []
        types = []

        # Common substitutions
        common_subs = {
            'th': ['d', 't', 'f', 'v'],
            'r': ['w', 'l'],
            'l': ['r', 'w'],
            'v': ['b', 'f'],
            'b': ['p', 'v'],
            'p': ['b', 'f'],
            's': ['sh', 'z'],
            'z': ['s', 'zh']
        }

        for correct, wrong_list in common_subs.items():
            if correct in target:
                for wrong in wrong_list:
                    if wrong in spoken and correct not in spoken:
                        errors.append(f"Common error: '{wrong}' for '{correct}'")
                        types.append('common_substitution')

        # Vowel errors
        vowels = ['a', 'e', 'i', 'o', 'u']
        target_vowels = [c for c in target if c in vowels]
        spoken_vowels = [c for c in spoken if c in vowels]

        if target_vowels != spoken_vowels:
            errors.append("Vowel pronunciation error")
            types.append('vowel_error')

        return {
            'errors': errors,
            'types': types
        }

    def _calculate_kannada_similarity(self, target: str, spoken: str) -> float:
        """Calculate similarity for Kannada script with more lenient matching."""

        # First try exact match
        if target == spoken:
            return 1.0

        # Try standard sequence matching
        similarity = difflib.SequenceMatcher(None, target, spoken).ratio()

        # For very short words (2-3 characters), be more lenient
        if len(target) <= 3 and len(spoken) <= 3:
            # Allow one character difference for short words
            if abs(len(target) - len(spoken)) <= 1:
                # Check if most characters match
                matches = sum(1 for a, b in zip(target, spoken) if a == b)
                total_chars = max(len(target), len(spoken))
                if total_chars > 0:
                    char_accuracy = matches / total_chars
                    # Boost similarity for short words with high character accuracy
                    if char_accuracy >= 0.7:
                        similarity = max(similarity, char_accuracy + 0.2)

        return similarity

    def generate_corrective_feedback(self, analysis: Dict[str, Any], target_word: str) -> Dict[str, Any]:
        """Generate comprehensive corrective feedback."""

        feedback_result = {
            'text_feedback': analysis.get('feedback', []),
            'practice_suggestions': [],
            'error_details': analysis.get('detailed_errors', [])
        }

        # Generate practice suggestions based on error types
        error_types = analysis.get('detailed_errors', [])

        if not error_types or 'correct' in error_types:
            feedback_result['practice_suggestions'] = [
                "Excellent pronunciation!",
                "Try practicing with longer words",
                "Keep up the good work!"
            ]

        elif 'no_speech' in error_types:
            feedback_result['practice_suggestions'] = [
                "Speak closer to the microphone",
                "Speak louder and clearer",
                "Make sure your microphone is working"
            ]

        elif any(error in error_types for error in ['omission', 'missing_words']):
            feedback_result['practice_suggestions'] = [
                "Slow down your speech",
                "Emphasize each sound clearly",
                "Practice saying each syllable separately"
            ]

        elif any(error in error_types for error in ['addition', 'extra_words']):
            feedback_result['practice_suggestions'] = [
                "Focus on the target word only",
                "Practice precise articulation",
                "Listen carefully to the model pronunciation"
            ]

        elif 'substitution' in error_types:
            feedback_result['practice_suggestions'] = [
                "Practice the specific sounds you're having trouble with",
                "Use a mirror to watch your mouth movements",
                "Listen to the difference between sounds"
            ]

        else:
            feedback_result['practice_suggestions'] = [
                "Practice slowly and clearly",
                "Break the word into smaller parts",
                "Listen to the model pronunciation carefully"
            ]

        return feedback_result

    def _generate_audio_feedback(self, target_word: str, analysis: Dict, corrective_feedback: Dict, language: str):
        """Generate comprehensive audio feedback with error details and practice suggestions."""
        try:
            accuracy = analysis.get('accuracy', 'unknown')
            detailed_errors = analysis.get('detailed_errors', [])
            practice_suggestions = corrective_feedback.get('practice_suggestions', [])

            # Build feedback text based on performance
            if accuracy == 'excellent':
                feedback_text = f"Excellent! You said '{target_word}' perfectly. Great job!"
            elif accuracy == 'good':
                feedback_text = f"Good pronunciation of '{target_word}'. Almost perfect!"
            else:
                # Build detailed feedback for errors
                error_text = "You said '{}' but the target is '{}'.".format(
                    analysis.get('spoken', ''),
                    target_word
                )

                if detailed_errors:
                    error_text += " Specific issues: "
                    error_text += ". ".join(detailed_errors[:2])  # Include top 2 errors

                if practice_suggestions:
                    error_text += " Practice suggestions: "
                    error_text += ". ".join(practice_suggestions[:2])  # Include top 2 suggestions

                feedback_text = error_text

            print(f"🔊 Speaking detailed feedback...")
            success = self.tts.speak(feedback_text, language=language)

            if success:
                print("✅ Audio feedback provided successfully")
            else:
                print("⚠️ Audio feedback failed")

        except Exception as e:
            print(f"❌ Audio feedback generation failed: {e}")

    def determine_starting_difficulty(self, severity_info: Dict) -> str:
        """Determine starting difficulty based on severity assessment."""
        severity_name = severity_info.get('severity_name', 'Moderate')
        wab_score = severity_info.get('wab_aq_score', 50)

        # Severity-based starting difficulty
        if severity_name == 'Mild' or wab_score >= 76:
            # High functioning - can start with medium difficulty
            starting_difficulty = 'medium'
            print("🎯 Based on your assessment, starting with medium difficulty sentences")
        elif severity_name == 'Moderate' or wab_score >= 51:
            # Moderate impairment - start with easy
            starting_difficulty = 'easy'
            print("🎯 Based on your assessment, starting with easy difficulty sentences")
        elif severity_name == 'Severe' or wab_score >= 26:
            # Significant impairment - definitely start easy
            starting_difficulty = 'easy'
            print("🎯 Based on your assessment, starting with easy difficulty sentences for confidence building")
        else:  # Very Severe
            # Profound impairment - start very easy
            starting_difficulty = 'easy'
            print("🎯 Based on your assessment, starting with easy difficulty sentences to build confidence")

        return starting_difficulty

    # -----------------------------
    # Main Therapy Session
    # -----------------------------
    def run_therapy_session(self):
        """Run the complete interactive therapy session."""
        # Select language
        language = self.select_language_interactive()

        # Initialize session
        patient_id = f"patient_{int(time.time())}"
        self.session = TherapySession(
            patient_id=patient_id,
            language=language,
            start_time=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        # Load models with language-specific ASR
        self.load_models(language)

        print(f"\n🚀 Starting therapy session for patient: {patient_id}")
        print("="*60)

        # Initial severity assessment to determine starting difficulty
        print("\n🏥 Performing initial severity assessment...")
        print("🎙️ Please say a simple sentence for assessment (e.g., 'Hello' or 'My name is...')")

        initial_audio_path = self.record_speech(duration=3)  # Shorter for initial assessment
        if initial_audio_path:
            # Try to get a basic transcription or use a default
            initial_transcription = self.transcribe_audio(initial_audio_path, language)
            if not initial_transcription:
                initial_transcription = "hello"  # Fallback

            # Analyze basic pronunciation
            basic_analysis = self.analyze_pronunciation("hello", initial_transcription)

            # Assess initial severity
            initial_severity = self.assess_severity(initial_audio_path, basic_analysis)
            print(f"🏥 Initial Assessment: {initial_severity['severity_name']} (WAB-AQ: {initial_severity['wab_aq_score']:.1f})")

            # Determine starting difficulty based on severity
            self.session.current_difficulty = self.determine_starting_difficulty(initial_severity)

            # Clean up initial audio
            try:
                os.unlink(initial_audio_path)
            except:
                pass
        else:
            print("⚠️ Initial assessment failed, starting with easy difficulty")
            self.session.current_difficulty = 'easy'

        try:
            while True:
                # Get sentences for current difficulty
                available_sentences = self.sentences_db[language][self.session.current_difficulty]

                if not available_sentences:
                    print(f"❌ No sentences available for {self.session.current_difficulty} difficulty")
                    break

                # Select random sentence from current difficulty
                sentence = random.choice(available_sentences)

                print(f"\n📝 Practice sentence: {sentence.text}")
                print(f"🎯 Difficulty: {sentence.difficulty} | Category: {sentence.category}")
                print(f"🔑 Target words: {', '.join(sentence.target_words)}")

                # Play TTS example (optional)
                play_example = input("\n🔊 Play pronunciation example? (y/n): ").lower().strip()
                if play_example == 'y':
                    print("🔊 Playing pronunciation example...")
                    self.tts.speak(sentence.text, language=language)

                # Record speech
                audio_path = self.record_speech()
                if not audio_path:
                    print("❌ Recording failed, skipping this round...")
                    continue

                # Transcribe
                transcription = self.transcribe_audio(audio_path, language)

                if not transcription:
                    print("❌ Transcription failed, skipping this round...")
                    continue

                print(f"🗣️  You said: {transcription}")

                # Analyze pronunciation with detailed feedback
                analysis = self.analyze_pronunciation(sentence.text, transcription)

                print(f"📊 Feedback: {analysis['feedback']}")
                print(f"🔹 Accuracy: {analysis['accuracy']}")

                # Show detailed error analysis if available
                if analysis.get('detailed_errors'):
                    print(f"🔍 Error Details:")
                    for error in analysis['detailed_errors'][:3]:  # Show top 3 errors
                        print(f"   • {error}")

                # Generate and show corrective feedback
                corrective_feedback = self.generate_corrective_feedback(analysis, sentence.text)
                if corrective_feedback.get('practice_suggestions'):
                    print(f"💡 Practice Tips:")
                    for suggestion in corrective_feedback['practice_suggestions'][:2]:  # Show top 2 suggestions
                        print(f"   • {suggestion}")

                # Generate comprehensive audio feedback
                self._generate_audio_feedback(sentence.text, analysis, corrective_feedback, language)

                # Assess severity (pass pronunciation analysis for better estimation)
                severity_info = self.assess_severity(audio_path, analysis)
                print(f"🏥 Severity: {severity_info['severity_name']} (WAB-AQ: {severity_info['wab_aq_score']:.1f})")

                # Update session stats
                self.session.total_attempts += 1
                if analysis['accuracy'] in ['excellent', 'good']:
                    self.session.correct_attempts += 1

                # Store session data
                session_data = {
                    'sentence': sentence.text,
                    'target': sentence.text,
                    'spoken': transcription,
                    'accuracy': analysis['accuracy'],
                    'similarity': analysis['similarity'],
                    'severity': severity_info['severity_name'],
                    'wab_aq_score': severity_info['wab_aq_score'],
                    'detailed_errors': analysis.get('detailed_errors', []),
                    'practice_suggestions': corrective_feedback.get('practice_suggestions', []),
                    'timestamp': time.strftime("%H:%M:%S")
                }
                self.session.session_sentences.append(session_data)

                # Difficulty adjustment (consider both accuracy and severity)
                accuracy_rate = self.session.correct_attempts / max(self.session.total_attempts, 1)

                # Get recent severity trend
                recent_severities = [s.get('wab_aq_score', 50) for s in self.session.session_sentences[-5:]]
                avg_recent_severity = sum(recent_severities) / len(recent_severities) if recent_severities else 50

                # Adjust difficulty based on performance and severity
                if accuracy_rate >= 0.8 and avg_recent_severity >= 60:
                    # High accuracy AND good recent performance - can progress
                    if self.session.current_difficulty == 'easy':
                        self.session.current_difficulty = 'medium'
                        print("📈 Progressing to medium difficulty!")
                    elif self.session.current_difficulty == 'medium' and accuracy_rate >= 0.9:
                        self.session.current_difficulty = 'hard'
                        print("📈 Progressing to hard difficulty!")
                elif accuracy_rate >= 0.7 and self.session.current_difficulty == 'easy' and avg_recent_severity >= 50:
                    # Good performance - move to medium
                    self.session.current_difficulty = 'medium'
                    print("📈 Progressing to medium difficulty!")
                elif accuracy_rate < 0.4 or avg_recent_severity < 40:
                    # Struggling - adjust down for more practice
                    if self.session.current_difficulty == 'hard':
                        self.session.current_difficulty = 'medium'
                        print("📉 Adjusting to medium difficulty for more practice")
                    elif self.session.current_difficulty == 'medium' and accuracy_rate < 0.3:
                        self.session.current_difficulty = 'easy'
                        print("📉 Adjusting to easy difficulty for more practice")
                elif avg_recent_severity < 30 and self.session.current_difficulty != 'easy':
                    # Very severe recent assessments - prioritize easy sentences
                    self.session.current_difficulty = 'easy'
                    print("🎯 Focusing on easy sentences to build confidence")

                # Continue or exit
                cont = input("\n🔄 Continue to next sentence? (y/n): ").lower().strip()
                if cont != 'y':
                    break

                # Clean up audio file
                try:
                    os.unlink(audio_path)
                except:
                    pass

        except KeyboardInterrupt:
            print("\n\n⏹️  Therapy session interrupted by user")
        except Exception as e:
            print(f"\n❌ Therapy session error: {e}")
        finally:
            # Save session data
            self._save_session_data()

    def _save_session_data(self):
        """Save session data to JSON file."""
        try:
            os.makedirs("therapy_sessions", exist_ok=True)
            filename = f"therapy_sessions/{self.session.patient_id}_{self.session.language}.json"

            session_dict = asdict(self.session)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_dict, f, ensure_ascii=False, indent=2)

            print(f"\n💾 Session data saved to: {filename}")
            print(f"📈 Final Stats - Attempts: {self.session.total_attempts}, "
                  f"Correct: {self.session.correct_attempts}, "
                  f"Accuracy: {self.session.correct_attempts/max(self.session.total_attempts, 1)*100:.1f}%")

        except Exception as e:
            print(f"❌ Failed to save session data: {e}")


def main():
    """Main function to run the interactive speech therapy system."""
    try:
        therapy_system = InteractiveSpeechTherapy()
        therapy_system.run_therapy_session()
    except KeyboardInterrupt:
        print("\n\n⏹️  Program interrupted by user")
    except Exception as e:
        print(f"\n❌ Program error: {e}")


if __name__ == "__main__":
    main()


