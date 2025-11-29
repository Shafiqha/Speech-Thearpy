"""
Audio-Driven Lip Sync
Maps lip movements DIRECTLY to audio waveform
Works for ALL languages by analyzing actual sound
"""

import os
import json
import librosa
import numpy as np
from pathlib import Path
from typing import Dict, List
from pydub import AudioSegment


class AudioDrivenLipSync:
    """
    Generates lip sync by analyzing ACTUAL AUDIO
    No text needed - works purely from sound
    Perfect for Hindi, Kannada, and all languages
    """
    
    def __init__(self):
        """Initialize audio-driven lip sync"""
        print(f"✅ Audio-Driven Lip Sync initialized")
        print(f"   Method: Direct audio analysis")
        print(f"   Works for: ALL languages")
    
    def generate_lip_sync_from_audio(
        self,
        audio_path: str,
        text: str = "",
        language: str = 'en'
    ) -> Dict:
        """
        Generate lip sync by analyzing ACTUAL AUDIO
        
        Args:
            audio_path: Path to audio file
            text: Text (optional, for metadata only)
            language: Language code
            
        Returns:
            Lip sync data with accurate timing
        """
        try:
            print(f"\n{'='*70}")
            print(f"🎯 AUDIO-DRIVEN LIP SYNC")
            print(f"{'='*70}")
            print(f"Text: {text}")
            print(f"Language: {language}")
            print(f"Audio: {audio_path}")
            print(f"Method: Analyzing ACTUAL audio waveform")
            
            # Load audio
            y, sr = librosa.load(audio_path, sr=22050)
            duration = len(y) / sr
            
            print(f"✅ Audio loaded: {duration:.2f}s")
            
            # Analyze audio features
            print(f"🔬 Analyzing audio features...")
            
            # 1. Detect onsets (sound starts)
            onset_frames = librosa.onset.onset_detect(
                y=y, 
                sr=sr, 
                units='time',
                backtrack=True,
                hop_length=256
            )
            
            # 2. Calculate energy (volume)
            hop_length = 256
            energy = librosa.feature.rms(y=y, hop_length=hop_length)[0]
            times = librosa.frames_to_time(np.arange(len(energy)), sr=sr, hop_length=hop_length)
            
            # 3. Detect pitch (high/low sounds)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=hop_length)
            
            # 4. Spectral centroid (brightness of sound)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
            
            # 5. Zero crossing rate (consonant detection)
            zcr = librosa.feature.zero_crossing_rate(y=y, hop_length=hop_length)[0]
            
            print(f"✅ Detected {len(onset_frames)} sound onsets")
            print(f"✅ Analyzed {len(times)} time frames")
            
            # Generate mouth cues from audio analysis
            mouth_cues = self._generate_mouth_cues_from_audio(
                times=times,
                energy=energy,
                zcr=zcr,
                spectral_centroids=spectral_centroids,
                onset_frames=onset_frames,
                duration=duration
            )
            
            print(f"✅ Generated {len(mouth_cues)} mouth cues")
            
            # Create alignment data structure
            alignment_data = {
                'metadata': {
                    'duration': duration,
                    'soundFile': audio_path
                },
                'mouthCues': mouth_cues
            }
            
            # Show sample cues
            print(f"\n📊 Sample mouth cues:")
            for i, cue in enumerate(mouth_cues[:10]):
                print(f"   {i+1}. {cue['value']} ({cue['start']:.2f}s - {cue['end']:.2f}s)")
            if len(mouth_cues) > 10:
                print(f"   ... and {len(mouth_cues) - 10} more")
            
            print(f"{'='*70}\n")
            
            return alignment_data
            
        except Exception as e:
            print(f"❌ Audio analysis error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_mouth_cues_from_audio(
        self,
        times: np.ndarray,
        energy: np.ndarray,
        zcr: np.ndarray,
        spectral_centroids: np.ndarray,
        onset_frames: np.ndarray,
        duration: float
    ) -> List[Dict]:
        """
        Generate mouth cues by analyzing audio features
        
        Maps audio characteristics to mouth shapes:
        - High energy + low ZCR = Open vowels (A, E, D)
        - High ZCR = Consonants (B, C, F, G)
        - Low energy = Closed mouth (X)
        - Onsets = Mouth opening
        """
        
        # Normalize features
        energy_norm = energy / (np.max(energy) + 1e-6)
        zcr_norm = zcr / (np.max(zcr) + 1e-6)
        spectral_norm = spectral_centroids / (np.max(spectral_centroids) + 1e-6)
        
        # Thresholds
        energy_threshold = 0.15
        zcr_threshold = 0.3
        spectral_threshold = 0.4
        
        mouth_cues = []
        current_shape = 'X'
        current_start = 0.0
        
        for i, time in enumerate(times):
            # Determine mouth shape based on audio features
            e = energy_norm[i]
            z = zcr_norm[i]
            s = spectral_norm[i]
            
            # Check if there's an onset nearby
            has_onset = any(abs(onset - time) < 0.1 for onset in onset_frames)
            
            # Determine mouth shape
            if e < energy_threshold:
                # Low energy = closed mouth
                shape = 'X'
            elif z > zcr_threshold:
                # High zero crossing = consonants
                if s > spectral_threshold:
                    # Bright consonants (F, S, SH)
                    shape = 'F'
                elif has_onset:
                    # Plosives (P, B, T, D)
                    shape = 'B'
                else:
                    # Other consonants
                    shape = 'C'
            else:
                # Low zero crossing = vowels
                if e > 0.5:
                    # High energy vowels (A, AA)
                    shape = 'D'
                elif e > 0.3:
                    # Medium energy vowels (E, O)
                    shape = 'E'
                else:
                    # Low energy vowels
                    shape = 'A'
            
            # If shape changed, save previous cue
            if shape != current_shape:
                if current_start < time:
                    mouth_cues.append({
                        'start': current_start,
                        'end': time,
                        'value': current_shape
                    })
                current_shape = shape
                current_start = time
        
        # Add final cue
        if current_start < duration:
            mouth_cues.append({
                'start': current_start,
                'end': duration,
                'value': current_shape
            })
        
        # Merge very short cues (< 0.05s)
        merged_cues = []
        for cue in mouth_cues:
            if cue['end'] - cue['start'] >= 0.05:
                merged_cues.append(cue)
            elif merged_cues:
                # Extend previous cue
                merged_cues[-1]['end'] = cue['end']
        
        return merged_cues if merged_cues else mouth_cues


# Singleton
_audio_driven_instance = None

def get_audio_driven_lip_sync():
    """Get singleton instance"""
    global _audio_driven_instance
    if _audio_driven_instance is None:
        _audio_driven_instance = AudioDrivenLipSync()
    return _audio_driven_instance


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) >= 2:
        service = AudioDrivenLipSync()
        audio_path = sys.argv[1]
        text = sys.argv[2] if len(sys.argv) > 2 else ""
        language = sys.argv[3] if len(sys.argv) > 3 else 'en'
        
        result = service.generate_lip_sync_from_audio(audio_path, text, language)
        
        if result:
            print(f"\n✅ Success!")
            print(f"Duration: {result['metadata']['duration']:.2f}s")
            print(f"Mouth cues: {len(result['mouthCues'])}")
    else:
        print("Usage: python audio_driven_lip_sync.py <audio_path> [text] [language]")
        print("\nExample:")
        print("  python audio_driven_lip_sync.py audio.mp3 'नमस्ते' hi")
