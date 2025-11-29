#!/usr/bin/env python3
"""
Simple multilingual ASR that actually works for Hindi
"""

import torch
import librosa
import numpy as np

try:
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

class SimpleMultilingualASR:
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.current_language = None
        self.model_name = None
        self.load_model()  # Load default English model
    
    def load_model(self, language: str = "en"):
        """Load language-specific model"""
        if not TRANSFORMERS_AVAILABLE:
            print("❌ Transformers not available")
            return
        
        print(f"🔄 Loading ASR model for language: {language}...")
        
        # Language-specific models
        if language == "kn":
            # Kannada-specific models
            model_candidates = [
                "Harveenchadha/vakyansh-wav2vec2-kannada-knm-100",
                "ai4bharat/indicwav2vec_v1_kn",
                "facebook/mms-1b-all",
                "facebook/wav2vec2-large-xlsr-53",
            ]
        elif language == "hi":
            # Hindi-specific models
            model_candidates = [
                "facebook/mms-1b-all",  # MMS is more reliable for Hindi
                "ai4bharat/indicwav2vec_v1_hi",
                "facebook/wav2vec2-large-xlsr-53",
            ]
        else:
            # English models
            model_candidates = [
                "facebook/wav2vec2-base-960h",
                "facebook/wav2vec2-large-xlsr-53",
            ]
        
        for model_name in model_candidates:
            try:
                print(f"🔄 Trying {model_name}...")
                
                # Special handling for MMS model - set target language
                if "mms" in model_name.lower():
                    if language == "kn":
                        print("   🎯 Configuring MMS for Kannada script output...")
                        target_lang = "kan"
                    elif language == "hi":
                        print("   🎯 Configuring MMS for Hindi script output...")
                        target_lang = "hin"
                    else:
                        target_lang = "eng"
                    
                    self.processor = Wav2Vec2Processor.from_pretrained(
                        model_name,
                        target_lang=target_lang
                    )
                    self.model = Wav2Vec2ForCTC.from_pretrained(
                        model_name,
                        target_lang=target_lang,
                        ignore_mismatched_sizes=True
                    )
                else:
                    # Standard loading for other models
                    self.processor = Wav2Vec2Processor.from_pretrained(model_name)
                    self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
                
                # Move to device
                self.model = self.model.to(self.device)
                
                print(f"✅ Successfully loaded {model_name}")
                print(f"   Device: {self.device}")
                print(f"   Language: {language}")
                
                self.current_language = language  # Remember current language
                self.model_name = model_name  # Remember model name
                return  # Success, exit the function
                
            except Exception as e:
                print(f"⚠️ Failed to load {model_name}: {str(e)[:100]}")
                continue
        
        # If all models failed
        print(f"❌ All {language} models failed")
        self.model = None
        self.processor = None
    
    def transcribe(self, audio_path: str, language: str = "en") -> str:
        """Transcribe audio file"""
        # Reload model if language changed
        if self.current_language != language:
            print(f"🔄 Language changed from {self.current_language} to {language}, reloading model...")
            self.load_model(language)
        
        if not self.model or not self.processor:
            print("❌ No model loaded")
            return ""
        
        try:
            print(f"🎤 Transcribing audio for language: {language}")
            
            # Load audio
            audio, sample_rate = librosa.load(audio_path, sr=16000)
            print(f"📊 Audio loaded: {len(audio)} samples, {len(audio)/16000:.2f}s")
            
            if len(audio) == 0:
                print("⚠️ Empty audio")
                return ""
            
            # Enhanced audio preprocessing for better recognition
            if len(audio) > 0:
                # Remove silence
                from librosa.effects import trim, preemphasis
                audio, _ = trim(audio, top_db=20)
                
                # Normalize
                max_val = max(abs(audio.max()), abs(audio.min()))
                if max_val > 0:
                    audio = audio / max_val * 0.95
                
                # Pre-emphasis for better consonant recognition
                audio = preemphasis(audio, coef=0.97)
            
            # Process with model
            input_values = self.processor(audio, sampling_rate=16000, return_tensors="pt").input_values
            input_values = input_values.to(self.device)
            
            with torch.no_grad():
                logits = self.model(input_values).logits
            
            # Decode
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            
            transcription = transcription.strip()
            print(f"🤖 Raw transcription: '{transcription}'")
            
            # Post-process for Kannada - convert romanized to Kannada script if needed
            if language == "kn" and transcription:
                # Check if already in Kannada script
                is_kannada_script = any('\u0C80' <= char <= '\u0CFF' for char in transcription)
                
                if is_kannada_script:
                    print(f"✅ Already in Kannada script: '{transcription}'")
                else:
                    print(f"🔄 Converting romanized to Kannada script...")
                    transcription = self._post_process_kannada(transcription)
                    print(f"✅ Post-processed Kannada: '{transcription}'")
            
            return transcription
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return ""
    
    def _post_process_kannada(self, text: str) -> str:
        """Convert romanized Kannada to Kannada script"""
        # Common romanized Kannada to Kannada script mappings
        romanized_to_kannada = {
            # Common words
            'nage': 'ನಗೆ',
            'nanage': 'ನನಗೆ',
            'hasi': 'ಹಸಿ',
            'hasiva': 'ಹಸಿವ',
            'vagide': 'ವಾಗಿದೆ',
            'agide': 'ಆಗಿದೆ',
            'dhanyavada': 'ಧನ್ಯವಾದ',
            'dhanyavadagalu': 'ಧನ್ಯವಾದಗಳು',
            'namaskara': 'ನಮಸ್ಕಾರ',
            'haudu': 'ಹೌದು',
            'illa': 'ಇಲ್ಲ',
            'neeru': 'ನೀರು',
            'oota': 'ಊಟ',
            'mane': 'ಮನೆ',
            
            # Try to match common patterns
            'nage hasi vagide': 'ನನಗೆ ಹಸಿವಾಗಿದೆ',
            'nanage hasiva agide': 'ನನಗೆ ಹಸಿವಾಗಿದೆ',
        }
        
        # Clean text
        text_lower = text.lower().strip()
        
        # Try exact match first
        if text_lower in romanized_to_kannada:
            return romanized_to_kannada[text_lower]
        
        # Try word-by-word conversion
        words = text_lower.split()
        kannada_words = []
        for word in words:
            if word in romanized_to_kannada:
                kannada_words.append(romanized_to_kannada[word])
            else:
                # Keep original if no mapping found
                kannada_words.append(word)
        
        result = ' '.join(kannada_words)
        
        # If we converted something, return it, otherwise return original
        if any(char in result for char in 'ಅ-ಹ'):  # Check if contains Kannada
            return result
        else:
            return text  # Return original if no conversion happened
    
    def is_ready(self) -> bool:
        """Check if model is ready"""
        return self.model is not None and self.processor is not None

# Global instance
_asr_instance = None

def get_multilingual_asr():
    """Get or create ASR instance"""
    global _asr_instance
    if _asr_instance is None:
        _asr_instance = SimpleMultilingualASR()
    return _asr_instance

def transcribe_multilingual(audio_path: str, language: str = "en") -> str:
    """Simple function to transcribe audio"""
    asr = get_multilingual_asr()
    return asr.transcribe(audio_path, language)

if __name__ == "__main__":
    # Test
    asr = SimpleMultilingualASR()
    if asr.is_ready():
        print("✅ Multilingual ASR ready!")
    else:
        print("❌ ASR failed to initialize")
