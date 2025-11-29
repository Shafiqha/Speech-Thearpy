"""
TRUE Audio-to-Lip Mapping
Uses speech recognition to detect ACTUAL sounds in audio
Then maps those sounds to correct mouth shapes
"""

import os
import json
import librosa
import numpy as np
from pathlib import Path
from typing import Dict, List
import subprocess
from pydub import AudioSegment


class TrueAudioLipMapping:
    """
    Maps lip movements to ACTUAL pronunciation in audio
    Uses Rhubarb's audio analysis WITHOUT text bias
    """
    
    def __init__(self):
        """Initialize true audio-lip mapper"""
        self.rhubarb_path = r"C:\Users\Shafiqha\Downloads\Rhubarb-Lip-Sync-1.13.0-Windows\Rhubarb-Lip-Sync-1.13.0-Windows\rhubarb.exe"
        print(f"✅ True Audio-Lip Mapping initialized")
        print(f"   Method: Pure audio analysis (no text)")
        print(f"   Works for: ALL languages")
    
    def map_audio_to_lips(
        self,
        audio_path: str,
        text: str = "",
        language: str = 'en'
    ) -> Dict:
        """
        Map lip movements to ACTUAL audio pronunciation
        
        Args:
            audio_path: Path to audio file
            text: Text (for display only, NOT used for alignment)
            language: Language code
            
        Returns:
            Lip sync data mapped to actual audio
        """
        try:
            print(f"\n{'='*70}")
            print(f"🎯 TRUE AUDIO-TO-LIP MAPPING")
            print(f"{'='*70}")
            print(f"Text: {text}")
            print(f"Language: {language}")
            print(f"Audio: {audio_path}")
            print(f"Method: Analyzing ACTUAL audio (ignoring text)")
            
            # Convert to WAV if needed
            wav_path = audio_path
            if not audio_path.endswith('.wav'):
                wav_path = audio_path.replace(Path(audio_path).suffix, '.wav')
                audio = AudioSegment.from_file(audio_path)
                audio.export(wav_path, format='wav')
                print(f"✅ Converted to WAV")
            
            # Output JSON path
            output_json = wav_path.replace('.wav', '_true_mapping.json')
            
            # Run Rhubarb WITHOUT text - pure audio analysis
            print(f"🔄 Running Rhubarb in AUDIO-ONLY mode...")
            print(f"   (No text input = maps to ACTUAL sounds)")
            
            cmd = [
                self.rhubarb_path,
                "-f", "json",
                wav_path,
                "-o", output_json,
                "--extendedShapes", "GHX"
                # NO --dialogFile = Rhubarb analyzes actual audio!
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120
            )
            
            if result.returncode == 0 and os.path.exists(output_json):
                with open(output_json, 'r', encoding='utf-8') as f:
                    alignment_data = json.load(f)
                
                print(f"✅ Audio analysis complete!")
                print(f"   Duration: {alignment_data['metadata']['duration']:.2f}s")
                print(f"   Mouth cues: {len(alignment_data['mouthCues'])}")
                
                # Enhance with audio features
                enhanced_data = self._enhance_with_audio_features(
                    alignment_data,
                    wav_path
                )
                
                # Show sample cues
                print(f"\n📊 Mouth cues (mapped to ACTUAL audio):")
                for i, cue in enumerate(enhanced_data['mouthCues'][:15]):
                    print(f"   {i+1}. {cue['value']} ({cue['start']:.2f}s - {cue['end']:.2f}s)")
                if len(enhanced_data['mouthCues']) > 15:
                    print(f"   ... and {len(enhanced_data['mouthCues']) - 15} more")
                
                print(f"{'='*70}\n")
                
                return enhanced_data
            else:
                error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else "Unknown error"
                print(f"❌ Audio analysis failed: {error_msg}")
                return None
                
        except Exception as e:
            print(f"❌ Mapping error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _enhance_with_audio_features(
        self,
        alignment_data: Dict,
        audio_path: str
    ) -> Dict:
        """
        Enhance Rhubarb's audio analysis with additional features
        
        Args:
            alignment_data: Rhubarb's audio-only analysis
            audio_path: Path to audio file
            
        Returns:
            Enhanced alignment data
        """
        try:
            print(f"🔬 Enhancing with audio features...")
            
            # Load audio
            y, sr = librosa.load(audio_path, sr=22050)
            
            # Detect onsets (sound starts)
            onset_frames = librosa.onset.onset_detect(
                y=y,
                sr=sr,
                units='time',
                backtrack=True
            )
            
            # Calculate energy
            hop_length = 512
            energy = librosa.feature.rms(y=y, hop_length=hop_length)[0]
            times = librosa.frames_to_time(np.arange(len(energy)), sr=sr, hop_length=hop_length)
            
            # Energy threshold for silence
            energy_threshold = np.mean(energy) * 0.2
            
            enhanced_cues = []
            
            for i, cue in enumerate(alignment_data['mouthCues']):
                start_time = cue['start']
                end_time = cue['end']
                mouth_shape = cue['value']
                
                # Check for onset
                has_onset = any(abs(onset - start_time) < 0.08 for onset in onset_frames)
                
                # Get energy during this cue
                cue_energy_mask = (times >= start_time) & (times <= end_time)
                if cue_energy_mask.any():
                    avg_energy = np.mean(energy[cue_energy_mask])
                    max_energy = np.max(energy[cue_energy_mask])
                    is_silence = avg_energy < energy_threshold
                else:
                    avg_energy = 0.0
                    max_energy = 0.0
                    is_silence = True
                
                # Refine mouth shape based on energy
                if is_silence:
                    # Force closed mouth during silence
                    mouth_shape = 'X'
                elif has_onset and mouth_shape == 'X':
                    # Open mouth at sound start
                    mouth_shape = 'A'
                elif max_energy > 0.3 and mouth_shape in ['A', 'X']:
                    # Wider opening for loud sounds
                    mouth_shape = 'D'
                
                enhanced_cues.append({
                    'start': start_time,
                    'end': end_time,
                    'value': mouth_shape,
                    'has_onset': has_onset,
                    'energy': float(avg_energy),
                    'is_silence': is_silence
                })
            
            alignment_data['mouthCues'] = enhanced_cues
            
            print(f"✅ Enhanced {len(enhanced_cues)} mouth cues")
            
            return alignment_data
            
        except Exception as e:
            print(f"⚠️ Enhancement failed: {e}, using original")
            return alignment_data


# Singleton
_true_mapper_instance = None

def get_true_audio_lip_mapper():
    """Get singleton instance"""
    global _true_mapper_instance
    if _true_mapper_instance is None:
        _true_mapper_instance = TrueAudioLipMapping()
    return _true_mapper_instance


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) >= 2:
        mapper = TrueAudioLipMapping()
        audio_path = sys.argv[1]
        text = sys.argv[2] if len(sys.argv) > 2 else ""
        language = sys.argv[3] if len(sys.argv) > 3 else 'en'
        
        result = mapper.map_audio_to_lips(audio_path, text, language)
        
        if result:
            print(f"\n✅ Success!")
            print(f"Duration: {result['metadata']['duration']:.2f}s")
            print(f"Mouth cues: {len(result['mouthCues'])}")
    else:
        print("Usage: python true_audio_lip_mapping.py <audio_path> [text] [language]")
        print("\nExample:")
        print("  python true_audio_lip_mapping.py audio.mp3 'नमस्ते' hi")
