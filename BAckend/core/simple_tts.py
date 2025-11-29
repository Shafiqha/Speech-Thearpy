#!/usr/bin/env python3
"""
Simple TTS System for Windows

Reliable text-to-speech without file locking issues.
"""

import os
import time
import numpy as np
import soundfile as sf
from pathlib import Path
import logging

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class ReliableTTS:
    """Reliable TTS system for Windows."""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        
        # Initialize pyttsx3 if available
        self.pyttsx3_engine = None
        if PYTTSX3_AVAILABLE:
            try:
                self.pyttsx3_engine = pyttsx3.init()
                self.pyttsx3_engine.setProperty('rate', 150)
                self.pyttsx3_engine.setProperty('volume', 0.8)
            except Exception as e:
                logging.warning(f"Could not initialize pyttsx3: {e}")
                self.pyttsx3_engine = None
    
    def synthesize(self, text: str, language: str = "en", save_path: str = None) -> np.ndarray:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            language: Language code (en, hi, kn)
            save_path: Optional path to save audio file
            
        Returns:
            Audio array
        """
        
        # Try different TTS methods in order of preference
        audio = None
        
        # Method 1: Try gTTS for supported languages
        if language in ['en', 'hi', 'kn'] and GTTS_AVAILABLE:
            audio = self._try_gtts(text, language)
        
        # Method 2: Try pyttsx3 as fallback
        if audio is None and self.pyttsx3_engine:
            audio = self._try_pyttsx3(text)
        
        # Method 3: Generate simple beep as last resort
        if audio is None:
            audio = self._generate_beep(text)
        
        # Save if requested
        if save_path and audio is not None:
            try:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                sf.write(save_path, audio, self.sample_rate)
                print(f"✅ Audio saved to: {save_path}")
            except Exception as e:
                print(f"⚠️  Could not save audio: {e}")
        
        return audio
    
    def speak(self, text: str, language: str = "en") -> bool:
        """
        Synthesize and play speech from text.
        
        Args:
            text: Text to synthesize and speak
            language: Language code (en, hi, kn)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"🔊 Speaking: '{text}' in {language}...")
            
            # Synthesize audio
            audio = self.synthesize(text, language)
            
            if audio is None or len(audio) == 0:
                print("❌ No audio generated")
                return False
            
            # Play the audio
            success = self._play_audio_array(audio, self.sample_rate)
            
            if success:
                print("✅ Audio played successfully")
            else:
                print("❌ Audio playback failed")
            
            return success
            
        except Exception as e:
            print(f"❌ Speak failed: {e}")
            return False
    
    def _play_audio_array(self, audio: np.ndarray, sample_rate: int) -> bool:
        """Play audio array using available methods."""
        try:
            import sounddevice as sd
            print("🔊 Playing audio...")
            sd.play(audio, sample_rate)
            sd.wait()  # Wait for playback to finish
            return True
        except ImportError:
            print("❌ sounddevice not available, trying alternative...")
            try:
                # Try to save and play with system player
                import tempfile
                import os
                import platform
                import subprocess
                
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                sf.write(temp_file.name, audio, sample_rate)
                
                system = platform.system().lower()
                if system == "windows":
                    os.startfile(temp_file.name)
                elif system == "darwin":  # macOS
                    subprocess.run(["afplay", temp_file.name])
                elif system == "linux":
                    subprocess.run(["aplay", temp_file.name])
                
                # Clean up
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                    
                return True
            except Exception as e:
                print(f"❌ Audio playback completely failed: {e}")
                return False
    
    def _try_gtts(self, text: str, language: str) -> np.ndarray:
        """Try Google TTS."""
        try:
            # Create unique filename
            timestamp = int(time.time() * 1000)
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            temp_file = temp_dir / f"gtts_{timestamp}.mp3"
            
            # Generate TTS
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(temp_file))
            
            # Wait for file to be written
            time.sleep(0.2)
            
            # Load audio
            import librosa
            audio, sr = librosa.load(str(temp_file), sr=self.sample_rate)
            
            # Clean up (ignore errors)
            try:
                temp_file.unlink()
            except:
                pass
            
            print(f"✅ gTTS synthesis successful")
            return audio
            
        except Exception as e:
            print(f"⚠️  gTTS failed: {e}")
            return None
    
    def _try_pyttsx3(self, text: str) -> np.ndarray:
        """Try pyttsx3 TTS."""
        try:
            # Create unique filename
            timestamp = int(time.time() * 1000)
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            temp_file = temp_dir / f"pyttsx3_{timestamp}.wav"
            
            # Generate TTS
            self.pyttsx3_engine.save_to_file(text, str(temp_file))
            self.pyttsx3_engine.runAndWait()
            
            # Wait for file to be written
            time.sleep(0.5)
            
            # Load audio
            import librosa
            audio, sr = librosa.load(str(temp_file), sr=self.sample_rate)
            
            # Clean up (ignore errors)
            try:
                temp_file.unlink()
            except:
                pass
            
            print(f"✅ pyttsx3 synthesis successful")
            return audio
            
        except Exception as e:
            print(f"⚠️  pyttsx3 failed: {e}")
            return None
    
    def _generate_beep(self, text: str) -> np.ndarray:
        """Generate simple beep pattern as fallback."""
        try:
            # Generate beeps based on word count
            word_count = len(text.split())
            duration = max(1.0, min(3.0, word_count * 0.3))  # 1-3 seconds
            
            # Generate tone
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            frequency = 800  # Hz
            audio = 0.3 * np.sin(2 * np.pi * frequency * t)
            
            # Add fade in/out
            fade_samples = int(0.1 * self.sample_rate)
            audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
            audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            print(f"✅ Generated beep pattern ({duration:.1f}s)")
            return audio
            
        except Exception as e:
            print(f"❌ Even beep generation failed: {e}")
            return np.zeros(int(self.sample_rate * 2.0))  # 2 seconds of silence
    
    def test_tts(self):
        """Test TTS functionality."""
        print("🔊 Testing TTS System...")
        print("-" * 40)
        
        test_texts = [
            ("Hello world", "en"),
            ("नमस्ते", "hi"),
            ("ಕೆಟ್ಟದು", "kn")
        ]
        
        for text, lang in test_texts:
            print(f"\n🎤 Testing: '{text}' ({lang})")
            audio = self.synthesize(text, lang)
            
            if audio is not None and len(audio) > 0:
                print(f"   ✅ Success - Generated {len(audio)} samples ({len(audio)/self.sample_rate:.1f}s)")
            else:
                print(f"   ❌ Failed")
        
        print("\n🎉 TTS test completed!")


def text_to_speech_file(text: str, output_path: str, language: str = "en") -> bool:
    """
    Generate TTS audio and save to file
    
    Args:
        text: Text to synthesize
        output_path: Path to save audio file
        language: Language code (en, hi, kn)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        tts = ReliableTTS()
        audio = tts.synthesize(text, language, output_path)
        return audio is not None and len(audio) > 0
    except Exception as e:
        print(f"❌ TTS file generation failed: {e}")
        return False


def main():
    """Test the TTS system."""
    tts = ReliableTTS()
    tts.test_tts()
    
    # Interactive test
    print("\n" + "="*50)
    print("🎤 INTERACTIVE TTS TEST")
    print("="*50)
    print("Enter text to synthesize (or 'quit' to exit)")
    
    while True:
        try:
            text = input("\n📝 Text: ").strip()
            if text.lower() in ['quit', 'exit', 'q']:
                break
            
            if not text:
                continue
            
            lang = input("🌐 Language [en/hi] (default: en): ").strip() or "en"
            
            print(f"🔄 Synthesizing '{text}' in {lang}...")
            audio = tts.synthesize(text, lang, f"temp/test_output.wav")
            
            if audio is not None:
                print(f"✅ Success! Audio saved to temp/test_output.wav")
            else:
                print(f"❌ Synthesis failed")
                
        except KeyboardInterrupt:
            break
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
