"""
Trained Model Lip Sync Service
Uses your trained LSTM model to predict visemes from audio
This is YOUR custom-trained model for accurate lip sync!
"""

import os
import sys
import torch
import torch.nn as nn
import librosa
import numpy as np
from pathlib import Path
from typing import Dict, List
from pydub import AudioSegment

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class LipSyncModel(nn.Module):
    """Your trained lip sync prediction model"""
    
    def __init__(self, input_dim=15, hidden_dim=128, num_visemes=9, num_layers=2):
        """
        Initialize model (same architecture as training)
        
        Args:
            input_dim: Input feature dimension (MFCC + energy + ZCR)
            hidden_dim: Hidden layer dimension
            num_visemes: Number of viseme classes (9: A, B, C, D, E, F, G, H, X)
            num_layers: Number of LSTM layers
        """
        super(LipSyncModel, self).__init__()
        
        self.lstm = nn.LSTM(
            input_dim,
            hidden_dim,
            num_layers,
            batch_first=True,
            bidirectional=True
        )
        
        self.fc = nn.Linear(hidden_dim * 2, num_visemes)
    
    def forward(self, x):
        """Forward pass"""
        lstm_out, _ = self.lstm(x)
        output = self.fc(lstm_out)
        return output


class TrainedModelLipSync:
    """
    Lip sync service using YOUR trained model
    Predicts visemes directly from audio features
    """
    
    def __init__(self, model_path='models/simple_best_model.pt'):
        """
        Initialize with your trained model
        
        Args:
            model_path: Path to your trained model
        """
        self.model_path = Path(__file__).parent.parent / model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Viseme mapping (9 mouth shapes)
        self.viseme_map = {
            0: 'X',  # Closed/rest
            1: 'A',  # Open mouth
            2: 'B',  # Lips together
            3: 'C',  # Slightly open
            4: 'D',  # Wide smile
            5: 'E',  # Relaxed
            6: 'F',  # Teeth on lip
            7: 'G',  # Tongue between teeth
            8: 'H'   # Narrow opening
        }
        
        # Load model
        self.model = self._load_model()
        
        print(f"✅ Trained Model Lip Sync initialized")
        print(f"   Model: {self.model_path.name}")
        print(f"   Device: {self.device}")
        print(f"   Visemes: {len(self.viseme_map)}")
    
    def _load_model(self):
        """Load your trained model"""
        try:
            # Create model
            model = LipSyncModel().to(self.device)
            
            # Load weights
            if self.model_path.exists():
                checkpoint = torch.load(self.model_path, map_location=self.device)
                model.load_state_dict(checkpoint)
                model.eval()
                print(f"✅ Loaded trained model from {self.model_path}")
            else:
                print(f"⚠️ Model file not found: {self.model_path}")
                print(f"   Using untrained model (will have random predictions)")
            
            return model
        
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            # Return untrained model as fallback
            model = LipSyncModel().to(self.device)
            model.eval()
            return model
    
    def extract_audio_features(self, audio_path: str) -> np.ndarray:
        """
        Extract audio features (same as training)
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Audio features (MFCC + energy + ZCR)
        """
        # Load audio
        y, sr = librosa.load(audio_path, sr=22050)
        
        # Extract MFCC (13 coefficients)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Extract energy (RMS)
        energy = librosa.feature.rms(y=y)
        
        # Extract zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)
        
        # Combine features (13 + 1 + 1 = 15 features)
        features = np.vstack([mfcc, energy, zcr]).T
        
        return features
    
    def predict_visemes(self, audio_path: str) -> List[Dict]:
        """
        Predict viseme sequence from audio using your trained model
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of viseme predictions with timing
        """
        try:
            print(f"\n{'='*70}")
            print(f"🎯 TRAINED MODEL LIP SYNC")
            print(f"{'='*70}")
            print(f"Audio: {audio_path}")
            print(f"Using YOUR trained model!")
            
            # Extract audio features
            audio_features = self.extract_audio_features(audio_path)
            print(f"✅ Extracted features: {audio_features.shape}")
            
            # Prepare input
            x = torch.FloatTensor(audio_features).unsqueeze(0).to(self.device)
            
            # Predict
            with torch.no_grad():
                output = self.model(x)
                predictions = torch.argmax(output, dim=-1).squeeze().cpu().numpy()
            
            print(f"✅ Predicted {len(predictions)} visemes")
            
            # Convert to mouth cues with timing
            mouth_cues = self._predictions_to_mouth_cues(predictions, audio_path)
            
            print(f"✅ Generated {len(mouth_cues)} mouth cues")
            print(f"{'='*70}\n")
            
            return mouth_cues
        
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _predictions_to_mouth_cues(self, predictions: np.ndarray, audio_path: str) -> List[Dict]:
        """
        Convert model predictions to mouth cues with PRECISE timing and smoothing
        
        Args:
            predictions: Array of predicted viseme IDs
            audio_path: Path to audio file (for duration)
            
        Returns:
            List of mouth cues with precise timing
        """
        # Get audio duration and features for precise timing
        y, sr = librosa.load(audio_path, sr=22050)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Detect onsets for precise timing
        onset_frames = librosa.onset.onset_detect(
            y=y, 
            sr=sr, 
            units='time',
            hop_length=256,
            backtrack=True
        )
        
        # Calculate energy for better mouth opening
        hop_length = 256
        energy = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        times = librosa.frames_to_time(np.arange(len(energy)), sr=sr, hop_length=hop_length)
        
        # Calculate time per prediction frame
        time_per_frame = duration / len(predictions)
        
        # Smooth predictions to avoid jitter
        smoothed_predictions = self._smooth_predictions(predictions)
        
        # Convert predictions to mouth cues with precise timing
        mouth_cues = []
        current_viseme = None
        start_time = 0.0
        
        for i, pred_id in enumerate(smoothed_predictions):
            viseme = self.viseme_map.get(int(pred_id), 'X')
            current_time = i * time_per_frame
            
            # If viseme changed, save previous cue
            if viseme != current_viseme:
                if current_viseme is not None:
                    end_time = current_time
                    
                    # Snap to nearest onset if close
                    nearest_onset = self._find_nearest_onset(onset_frames, start_time)
                    if nearest_onset is not None and abs(nearest_onset - start_time) < 0.05:
                        start_time = nearest_onset
                    
                    nearest_onset_end = self._find_nearest_onset(onset_frames, end_time)
                    if nearest_onset_end is not None and abs(nearest_onset_end - end_time) < 0.05:
                        end_time = nearest_onset_end
                    
                    mouth_cues.append({
                        'start': start_time,
                        'end': end_time,
                        'value': current_viseme
                    })
                
                current_viseme = viseme
                start_time = current_time
        
        # Add final cue
        if current_viseme is not None:
            mouth_cues.append({
                'start': start_time,
                'end': duration,
                'value': current_viseme
            })
        
        # Post-process: merge very short cues
        mouth_cues = self._merge_short_cues(mouth_cues, min_duration=0.03)
        
        return mouth_cues
    
    def _smooth_predictions(self, predictions: np.ndarray, window_size: int = 3) -> np.ndarray:
        """
        Smooth predictions to avoid jitter
        
        Args:
            predictions: Raw predictions
            window_size: Smoothing window size
            
        Returns:
            Smoothed predictions
        """
        smoothed = predictions.copy()
        
        for i in range(len(predictions)):
            # Get window
            start = max(0, i - window_size // 2)
            end = min(len(predictions), i + window_size // 2 + 1)
            window = predictions[start:end]
            
            # Use most common prediction in window
            unique, counts = np.unique(window, return_counts=True)
            smoothed[i] = unique[np.argmax(counts)]
        
        return smoothed
    
    def _find_nearest_onset(self, onset_frames: np.ndarray, time: float) -> float:
        """Find nearest onset to given time"""
        if len(onset_frames) == 0:
            return None
        
        distances = np.abs(onset_frames - time)
        nearest_idx = np.argmin(distances)
        
        if distances[nearest_idx] < 0.1:  # Within 100ms
            return onset_frames[nearest_idx]
        
        return None
    
    def _merge_short_cues(self, mouth_cues: List[Dict], min_duration: float = 0.03) -> List[Dict]:
        """
        Merge very short cues with neighbors
        
        Args:
            mouth_cues: List of mouth cues
            min_duration: Minimum cue duration in seconds
            
        Returns:
            Merged mouth cues
        """
        if not mouth_cues:
            return mouth_cues
        
        merged = []
        i = 0
        
        while i < len(mouth_cues):
            cue = mouth_cues[i]
            duration = cue['end'] - cue['start']
            
            # If cue is too short, merge with next or previous
            if duration < min_duration and i < len(mouth_cues) - 1:
                # Merge with next
                next_cue = mouth_cues[i + 1]
                merged.append({
                    'start': cue['start'],
                    'end': next_cue['end'],
                    'value': next_cue['value']  # Use next cue's viseme
                })
                i += 2
            else:
                merged.append(cue)
                i += 1
        
        return merged
    
    def generate_lip_sync(self, audio_path: str, text: str, language: str = 'en') -> Dict:
        """
        Generate lip sync data using your trained model
        
        Args:
            audio_path: Path to audio file
            text: Text being spoken (for metadata)
            language: Language code (for metadata)
            
        Returns:
            Lip sync data with mouth cues
        """
        try:
            # Convert to WAV if needed
            wav_path = audio_path
            if not audio_path.endswith('.wav'):
                wav_path = audio_path.replace(Path(audio_path).suffix, '.wav')
                audio = AudioSegment.from_file(audio_path)
                audio.export(wav_path, format='wav')
                print(f"✅ Converted to WAV: {wav_path}")
            
            # Predict visemes
            mouth_cues = self.predict_visemes(wav_path)
            
            if not mouth_cues:
                return None
            
            # Get audio duration
            y, sr = librosa.load(wav_path, sr=22050)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Create lip sync data
            lip_sync_data = {
                'metadata': {
                    'duration': duration,
                    'soundFile': wav_path,
                    'model': 'trained_lstm',
                    'text': text,
                    'language': language
                },
                'mouthCues': mouth_cues
            }
            
            # Count mouth shapes
            mouth_shape_counts = {}
            for cue in mouth_cues:
                shape = cue['value']
                mouth_shape_counts[shape] = mouth_shape_counts.get(shape, 0) + 1
            
            print(f"\n📊 MOUTH SHAPE ANALYSIS:")
            print(f"   Total cues: {len(mouth_cues)}")
            print(f"   Mouth shapes used: {dict(sorted(mouth_shape_counts.items()))}")
            print(f"   Duration: {duration:.2f}s")
            
            # Show first few cues for verification
            print(f"\n📋 First 5 mouth cues:")
            for i, cue in enumerate(mouth_cues[:5]):
                duration_ms = (cue['end'] - cue['start']) * 1000
                print(f"   {i+1}. {cue['value']} ({cue['start']:.3f}s - {cue['end']:.3f}s) [{duration_ms:.0f}ms]")
            
            return lip_sync_data
        
        except Exception as e:
            print(f"❌ Generation error: {e}")
            import traceback
            traceback.print_exc()
            return None


# Singleton instance
_trained_model_instance = None

def get_trained_model_lip_sync():
    """Get singleton instance of trained model lip sync"""
    global _trained_model_instance
    if _trained_model_instance is None:
        _trained_model_instance = TrainedModelLipSync()
    return _trained_model_instance


# Test
if __name__ == "__main__":
    service = get_trained_model_lip_sync()
    print("✅ Trained model service ready!")
