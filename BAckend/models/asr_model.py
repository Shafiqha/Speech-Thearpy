"""
Dual-Headed ASR Model for Aphasia Detection

Implements a multilingual ASR model with dual CTC heads:
1. Word-level CTC head for transcription
2. Phoneme-level CTC head for alignment and error analysis
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from dataclasses import dataclass

from transformers import (
    Wav2Vec2Model, 
    Wav2Vec2Config,
    Wav2Vec2Processor,
    Wav2Vec2CTCTokenizer,
    Wav2Vec2FeatureExtractor
)


@dataclass
class ASRModelOutput:
    """Output structure for the dual-headed ASR model."""
    # Required outputs (no defaults)
    transcription_logits: torch.Tensor
    phoneme_logits: torch.Tensor
    
    # Optional outputs (with defaults)
    transcription_loss: Optional[torch.Tensor] = None
    phoneme_loss: Optional[torch.Tensor] = None
    total_loss: Optional[torch.Tensor] = None
    hidden_states: Optional[torch.Tensor] = None
    attention_weights: Optional[torch.Tensor] = None


class PhonemeVocabulary:
    """Manages phoneme vocabularies for different languages."""
    
    def __init__(self):
        # IPA phonemes (subset for multilingual support)
        self.ipa_phonemes = [
            # Vowels
            'a', 'e', 'i', 'o', 'u', 'ə', 'ɛ', 'ɪ', 'ɔ', 'ʊ', 'ʌ', 'æ', 'ɑ',
            # Consonants
            'p', 'b', 't', 'd', 'k', 'g', 'f', 'v', 'θ', 'ð', 's', 'z', 'ʃ', 'ʒ',
            'h', 'm', 'n', 'ŋ', 'l', 'r', 'j', 'w',
            # Indic-specific phonemes
            'ʈ', 'ɖ', 'ɳ', 'ɽ', 'ɭ', 'ɲ', 'c', 'ɟ', 'x', 'ɣ'
        ]
        
        # ARPAbet for English
        self.arpabet_phonemes = [
            # Vowels
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 
            'OW', 'OY', 'UH', 'UW',
            # Consonants  
            'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 
            'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
        ]
        
        # Special tokens
        self.special_tokens = ['<pad>', '<unk>', '<s>', '</s>', '<sil>']
        
        # Build vocabularies
        self.phoneme_to_id = {}
        self.id_to_phoneme = {}
        self._build_vocabulary()
    
    def _build_vocabulary(self):
        """Build phoneme vocabulary mappings."""
        all_phonemes = self.special_tokens + self.ipa_phonemes + self.arpabet_phonemes
        
        for i, phoneme in enumerate(all_phonemes):
            self.phoneme_to_id[phoneme] = i
            self.id_to_phoneme[i] = phoneme
    
    def encode(self, phonemes: List[str]) -> List[int]:
        """Encode phoneme sequence to IDs."""
        return [self.phoneme_to_id.get(p, self.phoneme_to_id['<unk>']) for p in phonemes]
    
    def decode(self, ids: List[int]) -> List[str]:
        """Decode IDs to phoneme sequence."""
        return [self.id_to_phoneme.get(i, '<unk>') for i in ids]
    
    @property
    def vocab_size(self) -> int:
        """Get vocabulary size."""
        return len(self.phoneme_to_id)


class DualHeadCTCModel(nn.Module):
    """Dual-headed CTC model with word and phoneme outputs."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        
        # Load base wav2vec2 model
        model_name = config['asr_model']['base_model']
        self.wav2vec2 = Wav2Vec2Model.from_pretrained(model_name)
        
        # Get hidden size from the base model
        self.hidden_size = self.wav2vec2.config.hidden_size
        
        # Phoneme vocabulary
        self.phoneme_vocab = PhonemeVocabulary()
        
        # Feature projection layer
        feature_config = config['asr_model']['architecture']['feature_projection']
        self.feature_projection = nn.Sequential(
            nn.Linear(self.hidden_size, feature_config['hidden_size']),
            nn.GELU(),
            nn.Dropout(feature_config['dropout']),
            nn.LayerNorm(feature_config['hidden_size'])
        )
        
        # CTC heads
        ctc_config = config['asr_model']['architecture']['ctc_head']
        phoneme_ctc_config = config['asr_model']['architecture']['phoneme_ctc_head']
        
        # Word-level CTC head
        self.transcription_head = nn.Sequential(
            nn.Dropout(ctc_config['dropout']),
            nn.Linear(feature_config['hidden_size'], ctc_config['vocab_size'])
        )
        
        # Phoneme-level CTC head
        self.phoneme_head = nn.Sequential(
            nn.Dropout(phoneme_ctc_config['dropout']),
            nn.Linear(feature_config['hidden_size'], self.phoneme_vocab.vocab_size)
        )
        
        # Loss functions
        self.ctc_loss = nn.CTCLoss(blank=0, reduction='mean', zero_infinity=True)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize model weights."""
        for module in [self.feature_projection, self.transcription_head, self.phoneme_head]:
            for layer in module:
                if isinstance(layer, nn.Linear):
                    torch.nn.init.normal_(layer.weight, mean=0.0, std=0.02)
                    if layer.bias is not None:
                        torch.nn.init.zeros_(layer.bias)
    
    def forward(
        self,
        input_values: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        transcription_labels: Optional[torch.Tensor] = None,
        phoneme_labels: Optional[torch.Tensor] = None,
        return_dict: bool = True
    ) -> ASRModelOutput:
        """
        Forward pass through the dual-headed model.
        
        Args:
            input_values: Audio input tensor [batch_size, sequence_length]
            attention_mask: Attention mask for input
            transcription_labels: Ground truth transcription labels
            phoneme_labels: Ground truth phoneme labels
            return_dict: Whether to return structured output
            
        Returns:
            ASRModelOutput with transcription and phoneme predictions
        """
        
        # Extract features using wav2vec2
        wav2vec2_outputs = self.wav2vec2(
            input_values=input_values,
            attention_mask=attention_mask,
            return_dict=True
        )
        
        # Get hidden states
        hidden_states = wav2vec2_outputs.last_hidden_state
        
        # Project features
        projected_features = self.feature_projection(hidden_states)
        
        # Generate predictions from both heads
        transcription_logits = self.transcription_head(projected_features)
        phoneme_logits = self.phoneme_head(projected_features)
        
        # Calculate losses if labels provided
        total_loss = None
        transcription_loss = None
        phoneme_loss = None
        
        if transcription_labels is not None:
            # Calculate input and target lengths for CTC
            input_lengths = self._get_feat_extract_output_lengths(
                attention_mask.sum(-1) if attention_mask is not None 
                else torch.full((input_values.shape[0],), input_values.shape[1], device=input_values.device)
            )
            
            # Transcription CTC loss
            with torch.backends.cudnn.flags(enabled=False):
                transcription_loss = self.ctc_loss(
                    transcription_logits.log_softmax(-1).transpose(0, 1),
                    transcription_labels,
                    input_lengths,
                    self._get_target_lengths(transcription_labels)
                )
        
        if phoneme_labels is not None:
            # Phoneme CTC loss
            input_lengths = self._get_feat_extract_output_lengths(
                attention_mask.sum(-1) if attention_mask is not None 
                else torch.full((input_values.shape[0],), input_values.shape[1], device=input_values.device)
            )
            
            with torch.backends.cudnn.flags(enabled=False):
                phoneme_loss = self.ctc_loss(
                    phoneme_logits.log_softmax(-1).transpose(0, 1),
                    phoneme_labels,
                    input_lengths,
                    self._get_target_lengths(phoneme_labels)
                )
        
        # Combine losses
        if transcription_loss is not None and phoneme_loss is not None:
            loss_config = self.config['training']['loss']
            total_loss = (
                loss_config['ctc_weight'] * transcription_loss +
                loss_config['phoneme_ctc_weight'] * phoneme_loss
            )
        elif transcription_loss is not None:
            total_loss = transcription_loss
        elif phoneme_loss is not None:
            total_loss = phoneme_loss
        
        if not return_dict:
            return (transcription_logits, phoneme_logits, total_loss)
        
        return ASRModelOutput(
            transcription_logits=transcription_logits,
            phoneme_logits=phoneme_logits,
            transcription_loss=transcription_loss,
            phoneme_loss=phoneme_loss,
            total_loss=total_loss,
            hidden_states=projected_features,
            attention_weights=wav2vec2_outputs.attentions if hasattr(wav2vec2_outputs, 'attentions') else None
        )
    
    def _get_feat_extract_output_lengths(self, input_lengths: torch.Tensor) -> torch.Tensor:
        """Calculate output lengths after feature extraction."""
        # This is based on wav2vec2's conv layers
        # Typically: (input_length - 1) // 2 + 1 for each conv layer
        def _conv_out_length(input_length, kernel_size, stride):
            return (input_length - kernel_size) // stride + 1
        
        # wav2vec2 has 7 conv layers with specific configurations
        for kernel_size, stride in [(10, 5), (3, 2), (3, 2), (3, 2), (3, 2), (2, 2), (2, 2)]:
            input_lengths = _conv_out_length(input_lengths, kernel_size, stride)
        
        return input_lengths
    
    def _get_target_lengths(self, labels: torch.Tensor) -> torch.Tensor:
        """Get target sequence lengths (non-padding tokens)."""
        return (labels != -100).sum(-1)
    
    def decode_transcription(self, logits: torch.Tensor, tokenizer) -> List[str]:
        """Decode transcription logits to text."""
        # Get predictions
        predicted_ids = torch.argmax(logits, dim=-1)
        
        # Decode using tokenizer
        transcriptions = []
        for pred_ids in predicted_ids:
            # Remove padding and special tokens
            pred_ids = pred_ids[pred_ids != 0]  # Remove CTC blank
            transcription = tokenizer.decode(pred_ids.cpu().numpy())
            transcriptions.append(transcription)
        
        return transcriptions
    
    def decode_phonemes(self, logits: torch.Tensor) -> List[List[str]]:
        """Decode phoneme logits to phoneme sequences."""
        # Get predictions
        predicted_ids = torch.argmax(logits, dim=-1)
        
        # Decode phonemes
        phoneme_sequences = []
        for pred_ids in predicted_ids:
            # Remove CTC blank tokens (ID 0)
            pred_ids = pred_ids[pred_ids != 0]
            
            # Remove consecutive duplicates (CTC collapse)
            if len(pred_ids) > 0:
                unique_ids = [pred_ids[0].item()]
                for i in range(1, len(pred_ids)):
                    if pred_ids[i] != pred_ids[i-1]:
                        unique_ids.append(pred_ids[i].item())
                
                phonemes = self.phoneme_vocab.decode(unique_ids)
                phoneme_sequences.append(phonemes)
            else:
                phoneme_sequences.append([])
        
        return phoneme_sequences


class MultilingualASRProcessor:
    """Processor for handling multilingual ASR inputs and outputs."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize feature extractor
        model_name = config['asr_model']['base_model']
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
        
        # Initialize tokenizers for each language
        self.tokenizers = {}
        self._init_tokenizers()
        
        # Phoneme vocabulary
        self.phoneme_vocab = PhonemeVocabulary()
    
    def _init_tokenizers(self):
        """Initialize tokenizers for supported languages."""
        for lang in self.config['languages']['supported']:
            # For now, use character-level tokenization
            # In production, you'd load pre-trained tokenizers
            vocab_size = self.config['asr_model']['architecture']['ctc_head']['vocab_size']
            
            # Create simple character tokenizer (placeholder)
            # This should be replaced with proper language-specific tokenizers
            self.tokenizers[lang] = self._create_char_tokenizer(lang, vocab_size)
    
    def _create_char_tokenizer(self, language: str, vocab_size: int):
        """Create a simple character-level tokenizer."""
        # This is a simplified implementation
        # In practice, you'd use proper tokenizers with language-specific vocabularies
        
        if language == 'en':
            chars = list('abcdefghijklmnopqrstuvwxyz ')
        elif language == 'hi':
            # Devanagari characters (simplified)
            chars = list('अआइईउऊएऐओऔकखगघचछजझटठडढतथदधनपफबभमयरलवशषसह ')
        elif language == 'kn':
            # Kannada characters (simplified)  
            chars = list('ಅಆಇಈಉಊಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹ ')
        else:
            chars = list('abcdefghijklmnopqrstuvwxyz ')
        
        # Add special tokens
        special_tokens = ['<pad>', '<unk>', '<s>', '</s>']
        vocab = special_tokens + chars
        
        # Pad to vocab_size if needed
        while len(vocab) < vocab_size:
            vocab.append(f'<extra_{len(vocab)}>')
        
        # Create mappings
        char_to_id = {char: i for i, char in enumerate(vocab)}
        id_to_char = {i: char for i, char in enumerate(vocab)}
        
        return {
            'char_to_id': char_to_id,
            'id_to_char': id_to_char,
            'vocab': vocab,
            'vocab_size': len(vocab)
        }
    
    def preprocess_audio(self, audio: np.ndarray, sampling_rate: int) -> Dict[str, torch.Tensor]:
        """Preprocess audio for model input."""
        # Extract features
        inputs = self.feature_extractor(
            audio,
            sampling_rate=sampling_rate,
            return_tensors="pt",
            padding=True
        )
        
        return inputs
    
    def encode_text(self, text: str, language: str) -> torch.Tensor:
        """Encode text to token IDs."""
        tokenizer = self.tokenizers[language]
        
        # Simple character-level encoding
        char_ids = []
        for char in text.lower():
            char_id = tokenizer['char_to_id'].get(char, tokenizer['char_to_id']['<unk>'])
            char_ids.append(char_id)
        
        return torch.tensor(char_ids, dtype=torch.long)
    
    def decode_text(self, token_ids: torch.Tensor, language: str) -> str:
        """Decode token IDs to text."""
        tokenizer = self.tokenizers[language]
        
        # Simple character-level decoding
        chars = []
        for token_id in token_ids:
            char = tokenizer['id_to_char'].get(token_id.item(), '<unk>')
            if char not in ['<pad>', '<s>', '</s>', '<unk>']:
                chars.append(char)
        
        return ''.join(chars)
    
    def encode_phonemes(self, phonemes: List[str]) -> torch.Tensor:
        """Encode phoneme sequence to IDs."""
        phoneme_ids = self.phoneme_vocab.encode(phonemes)
        return torch.tensor(phoneme_ids, dtype=torch.long)
    
    def get_vocab_size(self, language: str) -> int:
        """Get vocabulary size for a language."""
        return self.tokenizers[language]['vocab_size']


def create_asr_model(config: Dict[str, Any]) -> Tuple[DualHeadCTCModel, MultilingualASRProcessor]:
    """Create and return the ASR model and processor."""
    
    # Create processor
    processor = MultilingualASRProcessor(config)
    
    # Update config with actual vocab sizes
    for lang in config['languages']['supported']:
        vocab_size = processor.get_vocab_size(lang)
        # Use the maximum vocab size across languages
        config['asr_model']['architecture']['ctc_head']['vocab_size'] = max(
            config['asr_model']['architecture']['ctc_head'].get('vocab_size', 0),
            vocab_size
        )
    
    # Create model
    model = DualHeadCTCModel(config)
    
    return model, processor


# Example usage and testing
if __name__ == "__main__":
    import yaml
    
    # Load config
    with open("configs/model_config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Create model and processor
    model, processor = create_asr_model(config)
    
    print(f"Model created successfully!")
    print(f"Transcription vocab size: {config['asr_model']['architecture']['ctc_head']['vocab_size']}")
    print(f"Phoneme vocab size: {processor.phoneme_vocab.vocab_size}")
    
    # Test with dummy input
    batch_size, seq_length = 2, 16000  # 1 second of 16kHz audio
    dummy_audio = torch.randn(batch_size, seq_length)
    
    # Forward pass
    outputs = model(dummy_audio)
    print(f"Transcription logits shape: {outputs.transcription_logits.shape}")
    print(f"Phoneme logits shape: {outputs.phoneme_logits.shape}")
    print(f"Hidden states shape: {outputs.hidden_states.shape}")
