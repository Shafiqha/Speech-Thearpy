"""
Advanced ASR Service using the trained dual-headed model
"""

import torch
import torchaudio
import numpy as np
from typing import Dict, List, Optional, Tuple
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.asr_model import DualHeadCTCModel, PhonemeVocabulary
    from transformers import Wav2Vec2Processor, Wav2Vec2CTCTokenizer
except ImportError as e:
    print(f"⚠️ Advanced ASR imports failed: {e}")
    # Create dummy classes to prevent import errors
    class DualHeadCTCModel:
        def __init__(self, *args, **kwargs): pass
    class PhonemeVocabulary:
        def __init__(self, *args, **kwargs): 
            self.vocab_size = 64

class AdvancedASRService:
    """Advanced ASR service using the trained dual-headed model"""
    
    def __init__(self, model_path: str = None, config_path: str = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.phoneme_vocab = PhonemeVocabulary()
        
        # Default config if not provided
        self.config = {
            'asr_model': {
                'base_model': 'facebook/wav2vec2-large-xlsr-53',
                'architecture': {
                    'feature_projection': {
                        'hidden_size': 768,
                        'dropout': 0.1
                    },
                    'ctc_head': {
                        'vocab_size': 32,  # Adjust based on your vocabulary
                        'dropout': 0.1
                    },
                    'phoneme_ctc_head': {
                        'dropout': 0.1
                    }
                }
            },
            'training': {
                'loss': {
                    'ctc_weight': 0.7,
                    'phoneme_ctc_weight': 0.3
                }
            }
        }
        
        self.model_path = model_path
        self.config_path = config_path
        
        # Language-specific configurations
        self.language_configs = {
            'en': {'sample_rate': 16000, 'normalize': True},
            'hi': {'sample_rate': 16000, 'normalize': True},
            'kn': {'sample_rate': 16000, 'normalize': True}
        }
        
    def load_model(self):
        """Load the trained model"""
        print("🤖 Loading advanced ASR model...")
        
        try:
            # Initialize model
            self.model = DualHeadCTCModel(self.config)
            
            # Load trained weights if available
            if self.model_path and os.path.exists(self.model_path):
                print(f"📂 Loading trained weights from {self.model_path}")
                checkpoint = torch.load(self.model_path, map_location=self.device)
                
                # Handle different checkpoint formats
                if 'model_state_dict' in checkpoint:
                    try:
                        self.model.load_state_dict(checkpoint['model_state_dict'])
                        print("✅ Trained weights loaded successfully")
                    except Exception as e:
                        print(f"⚠️ Failed to load state dict: {e}")
                        print("🔄 Using base model instead")
                else:
                    print("⚠️ Checkpoint format not recognized, using base model")
            else:
                print("⚠️ No trained weights found, using base model")
            
            self.model.to(self.device)
            self.model.eval()
            
            # Load processor and tokenizer with error handling
            try:
                base_model = self.config['asr_model']['base_model']
                self.processor = Wav2Vec2Processor.from_pretrained(base_model)
                
                # Create simple tokenizer for multilingual support
                vocab_dict = self._create_multilingual_vocab()
                self.tokenizer = Wav2Vec2CTCTokenizer(
                    vocab_dict,
                    unk_token="<unk>",
                    pad_token="<pad>",
                    word_delimiter_token="|"
                )
                
                print("✅ Advanced ASR model loaded successfully")
                return True
                
            except Exception as e:
                print(f"⚠️ Failed to load processor/tokenizer: {e}")
                print("🔄 Model loaded but processor failed")
                return False
            
        except Exception as e:
            print(f"❌ Failed to load advanced ASR model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_multilingual_vocab(self) -> Dict[str, int]:
        """Create vocabulary for multilingual support"""
        
        # Basic vocabulary covering English, Hindi romanized, and Kannada romanized
        vocab = {
            "<pad>": 0,
            "<s>": 1,
            "</s>": 2,
            "<unk>": 3,
            "|": 4,  # word delimiter
        }
        
        # Add common characters
        chars = "abcdefghijklmnopqrstuvwxyz"
        for i, char in enumerate(chars):
            vocab[char] = i + 5
        
        return vocab
    
    def transcribe_audio(self, audio_path: str, language: str = 'en', target_text: str = None) -> Dict:
        """
        Transcribe audio using the advanced ASR model
        
        Args:
            audio_path: Path to audio file
            language: Language code (en, hi, kn)
            target_text: Target text for comparison (optional)
            
        Returns:
            Dict with transcription results
        """
        
        if not self.model:
            if not self.load_model():
                return self._fallback_transcription(audio_path, language)
        
        try:
            print(f"🎤 Advanced ASR transcribing: {language}")
            
            # Load and preprocess audio
            audio_input = self._preprocess_audio(audio_path, language)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(
                    input_values=audio_input,
                    attention_mask=None,
                    return_dict=True
                )
            
            # Decode transcription
            transcription_logits = outputs.transcription_logits
            transcriptions = self.model.decode_transcription(transcription_logits, self.tokenizer)
            
            # Decode phonemes for detailed analysis
            phoneme_logits = outputs.phoneme_logits
            phoneme_sequences = self.model.decode_phonemes(phoneme_logits)
            
            # Get the best transcription
            transcription = transcriptions[0] if transcriptions else ""
            phonemes = phoneme_sequences[0] if phoneme_sequences else []
            
            # Post-process for language-specific improvements
            transcription = self._post_process_transcription(transcription, language)
            
            print(f"📝 Advanced transcription: '{transcription}'")
            
            # Calculate confidence scores
            confidence = self._calculate_confidence(transcription_logits)
            
            # Detailed analysis if target provided
            analysis = {}
            if target_text:
                analysis = self._analyze_transcription(transcription, target_text, phonemes, language)
            
            return {
                'transcription': transcription,
                'phonemes': phonemes,
                'confidence': confidence,
                'language': language,
                'model_type': 'advanced_dual_head',
                'analysis': analysis
            }
            
        except Exception as e:
            print(f"❌ Advanced ASR failed: {e}")
            return self._fallback_transcription(audio_path, language)
    
    def _preprocess_audio(self, audio_path: str, language: str) -> torch.Tensor:
        """Preprocess audio for the model"""
        
        config = self.language_configs.get(language, self.language_configs['en'])
        
        # Load audio
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Resample if needed
        if sample_rate != config['sample_rate']:
            resampler = torchaudio.transforms.Resample(sample_rate, config['sample_rate'])
            waveform = resampler(waveform)
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        # Normalize
        if config['normalize']:
            waveform = waveform / torch.max(torch.abs(waveform))
        
        # Process with wav2vec2 processor
        inputs = self.processor(
            waveform.squeeze().numpy(),
            sampling_rate=config['sample_rate'],
            return_tensors="pt",
            padding=True
        )
        
        return inputs.input_values.to(self.device)
    
    def _post_process_transcription(self, transcription: str, language: str) -> str:
        """Post-process transcription for language-specific improvements"""
        
        # Clean up transcription
        transcription = transcription.strip().lower()
        
        # Language-specific post-processing
        if language == 'hi':
            # Hindi-specific improvements
            transcription = self._improve_hindi_transcription(transcription)
        elif language == 'kn':
            # Kannada-specific improvements
            transcription = self._improve_kannada_transcription(transcription)
        elif language == 'en':
            # English-specific improvements
            transcription = self._improve_english_transcription(transcription)
        
        return transcription
    
    def _improve_hindi_transcription(self, text: str) -> str:
        """Improve Hindi transcription with common corrections"""
        
        # Common Hindi word corrections
        corrections = {
            'namaskar': 'namaste',
            'namaskar': 'namaste',
            'dhanywad': 'dhanyawad',
            'dhanyabad': 'dhanyawad',
            'haan': 'haan',
            'nahi': 'nahin',
            'paani': 'paani',
            'khaana': 'khaana'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def _improve_kannada_transcription(self, text: str) -> str:
        """Improve Kannada transcription with common corrections"""
        
        # Common Kannada word corrections
        corrections = {
            'namaskar': 'namaskara',
            'namascar': 'namaskara',
            'dhanyabad': 'dhanyavaada',
            'dhanyawad': 'dhanyavaada',
            'haudu': 'haudu',
            'illa': 'illa',
            'neeru': 'neeru',
            'anna': 'anna'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def _improve_english_transcription(self, text: str) -> str:
        """Improve English transcription"""
        
        # Basic English improvements
        corrections = {
            'helo': 'hello',
            'thankyou': 'thank you',
            'gud': 'good',
            'mornin': 'morning'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def _calculate_confidence(self, logits: torch.Tensor) -> float:
        """Calculate confidence score from logits"""
        
        # Get probabilities
        probs = torch.softmax(logits, dim=-1)
        
        # Calculate average max probability as confidence
        max_probs = torch.max(probs, dim=-1)[0]
        confidence = torch.mean(max_probs).item()
        
        return confidence
    
    def _analyze_transcription(self, transcription: str, target: str, phonemes: List[str], language: str) -> Dict:
        """Analyze transcription quality"""
        
        # Basic analysis
        analysis = {
            'word_accuracy': self._calculate_word_accuracy(transcription, target),
            'character_accuracy': self._calculate_character_accuracy(transcription, target),
            'phoneme_analysis': self._analyze_phonemes(phonemes, target, language)
        }
        
        return analysis
    
    def _calculate_word_accuracy(self, transcription: str, target: str) -> float:
        """Calculate word-level accuracy"""
        
        trans_words = transcription.split()
        target_words = target.split()
        
        if not target_words:
            return 0.0
        
        correct = sum(1 for t, r in zip(target_words, trans_words) if t.lower() == r.lower())
        return correct / len(target_words)
    
    def _calculate_character_accuracy(self, transcription: str, target: str) -> float:
        """Calculate character-level accuracy"""
        
        if not target:
            return 0.0
        
        # Simple character matching
        correct = sum(1 for t, r in zip(target.lower(), transcription.lower()) if t == r)
        return correct / len(target)
    
    def _analyze_phonemes(self, phonemes: List[str], target: str, language: str) -> Dict:
        """Analyze phoneme-level accuracy"""
        
        return {
            'phoneme_count': len(phonemes),
            'target_length': len(target),
            'phoneme_accuracy': len(phonemes) / max(len(target), 1)
        }
    
    def _fallback_transcription(self, audio_path: str, language: str) -> Dict:
        """Fallback to simple transcription if advanced model fails"""
        
        print("⚠️ Using fallback transcription")
        
        # Simple fallback - could integrate with existing simple ASR
        return {
            'transcription': '',
            'phonemes': [],
            'confidence': 0.0,
            'language': language,
            'model_type': 'fallback',
            'analysis': {}
        }

# Global instance
advanced_asr_service = None

def get_advanced_asr_service(model_path: str = None) -> AdvancedASRService:
    """Get or create the advanced ASR service"""
    global advanced_asr_service
    
    if advanced_asr_service is None:
        advanced_asr_service = AdvancedASRService(model_path)
    
    return advanced_asr_service
