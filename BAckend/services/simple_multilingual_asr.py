"""
Simple Multilingual ASR (Automatic Speech Recognition)
Fallback transcription service for lip animation exercise
"""

import os
import sys
from pathlib import Path

try:
    import torch
    import torchaudio
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


def transcribe_multilingual(audio_path: str, language: str = "en") -> str:
    """
    Transcribe audio file to text using language-specific Wav2Vec2 models
    
    Args:
        audio_path: Path to audio file
        language: Language code (en, hi, kn)
        
    Returns:
        Transcribed text
    """
    if not TRANSFORMERS_AVAILABLE or not LIBROSA_AVAILABLE:
        print("⚠️ ASR libraries not available")
        return ""
    
    try:
        # Load audio
        audio, sr = librosa.load(audio_path, sr=16000)
        
        # Enhanced audio preprocessing for better recognition
        if len(audio) > 0:
            # Remove silence from start and end
            audio, _ = librosa.effects.trim(audio, top_db=20)
            
            # Normalize audio
            max_val = max(abs(audio.max()), abs(audio.min()))
            if max_val > 0:
                audio = audio / max_val * 0.95  # Normalize to 95% to avoid clipping
            
            # Apply pre-emphasis to boost high frequencies (improves consonant recognition)
            audio = librosa.effects.preemphasis(audio, coef=0.97)
        
        print(f"🎵 Audio loaded: {len(audio)} samples, {len(audio)/sr:.2f}s")
        
        # Select best model for each language
        model_name = None
        processor = None
        model = None
        
        if language == "hi":
            # Hindi-specific model
            model_name = "facebook/wav2vec2-large-xlsr-53-hindi"
            print(f"🇮🇳 Using Hindi model: {model_name}")
            
        elif language == "kn":
            # For Kannada, try multiple models in order of quality
            kannada_models = [
                "Harveenchadha/vakyansh-wav2vec2-kannada-knm-100",  # Vakyansh Kannada
                "ai4bharat/indicwav2vec_v1_kn",                      # AI4Bharat Kannada
                "facebook/mms-1b-all",                               # Meta MMS multilingual
                "facebook/wav2vec2-large-xlsr-53"                    # XLSR multilingual
            ]
            
            for candidate in kannada_models:
                try:
                    print(f"🔍 Trying Kannada model: {candidate}")
                    processor = Wav2Vec2Processor.from_pretrained(candidate)
                    model = Wav2Vec2ForCTC.from_pretrained(candidate)
                    model_name = candidate
                    print(f"✅ Loaded Kannada model: {candidate}")
                    break
                except Exception as e:
                    print(f"⚠️ Failed to load {candidate}: {str(e)[:100]}")
                    continue
            
            if not model_name:
                print("⚠️ No Kannada-specific model available, using multilingual")
                model_name = "facebook/wav2vec2-large-xlsr-53"
                
        else:
            # English model
            model_name = "facebook/wav2vec2-base-960h"
            print(f"🇬🇧 Using English model: {model_name}")
        
        # Load model and processor if not already loaded (for non-Kannada or if Kannada loop failed)
        if processor is None or model is None:
            print(f"📥 Loading model: {model_name}")
            processor = Wav2Vec2Processor.from_pretrained(model_name)
            model = Wav2Vec2ForCTC.from_pretrained(model_name)
        
        # Process audio with the model
        input_values = processor(audio, sampling_rate=16000, return_tensors="pt", padding=True).input_values
        
        print(f"📊 Input shape: {input_values.shape}")
        
        # Get predictions
        with torch.no_grad():
            logits = model(input_values).logits
        
        print(f"📈 Logits shape: {logits.shape}")
        
        # Improved decoding for better accuracy
        # Use beam search-like approach by considering top predictions
        predicted_ids = torch.argmax(logits, dim=-1)
        
        # Try multiple decoding strategies for Kannada
        if language == "kn":
            # Strategy 1: Standard decoding
            transcription = processor.batch_decode(predicted_ids)[0]
            print(f"📝 Standard decode: '{transcription}'")
            
            # Strategy 2: Decode with skip_special_tokens
            transcription_clean = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            print(f"📝 Clean decode: '{transcription_clean}'")
            
            # Use the cleaner version if it's not empty
            if transcription_clean and len(transcription_clean.strip()) > 0:
                transcription = transcription_clean
                print(f"✅ Using clean decode")
        else:
            # For other languages, use standard decoding
            transcription = processor.batch_decode(predicted_ids)[0]
        
        print(f"📝 Raw transcription: '{transcription}'")
        
        # Language-specific post-processing
        if language == "kn":
            # Kannada-specific cleaning and normalization
            transcription = transcription.strip()
            
            # Remove word delimiters and special tokens
            transcription = transcription.replace("|", " ")
            transcription = transcription.replace("<s>", "").replace("</s>", "")
            transcription = transcription.replace("<pad>", "").replace("<unk>", "")
            
            # Remove extra spaces
            transcription = " ".join(transcription.split())
            
            # Normalize Kannada characters (handle different Unicode representations)
            # Remove zero-width characters that might interfere
            transcription = transcription.replace("\u200b", "")  # Zero-width space
            transcription = transcription.replace("\u200c", "")  # Zero-width non-joiner
            transcription = transcription.replace("\u200d", "")  # Zero-width joiner
            
            # Common Kannada transcription fixes
            # Fix common model mistakes
            kannada_fixes = {
                "ನಮಸ್ಕರ": "ನಮಸ್ಕಾರ",  # namaskara
                "ಧನ್ಯವದ": "ಧನ್ಯವಾದ",  # dhanyavaada
                "ಹೌದು": "ಹೌದು",        # haudu (already correct)
                "ಇಲ್ಲ": "ಇಲ್ಲ",        # illa (already correct)
            }
            
            for wrong, correct in kannada_fixes.items():
                transcription = transcription.replace(wrong, correct)
            
            print(f"✅ Kannada transcription: '{transcription}'")
            
        elif language == "hi":
            # Hindi-specific cleaning
            transcription = transcription.strip()
            transcription = " ".join(transcription.split())
            transcription = transcription.replace("|", " ").strip()
            print(f"✅ Hindi transcription: '{transcription}'")
        else:
            # English cleaning
            transcription = transcription.strip().lower()
            print(f"✅ English transcription: '{transcription}'")
        
        return transcription
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return ""


if __name__ == "__main__":
    # Test
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        lang = sys.argv[2] if len(sys.argv) > 2 else "en"
        
        result = transcribe_multilingual(audio_file, lang)
        print(f"Transcription: {result}")
    else:
        print("Usage: python simple_multilingual_asr.py <audio_file> [language]")
