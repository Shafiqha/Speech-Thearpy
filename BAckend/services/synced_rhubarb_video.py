"""
Synced Rhubarb Lip Sync Video Generator
- Audio and video perfectly synchronized
- Professional 2D avatar with Rhubarb mouth shapes
- Uses actual audio duration for timing
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pathlib import Path
from typing import List, Dict
import subprocess
import os
from .phoneme_viseme_mapper import get_phoneme_viseme_mapper


class SyncedRhubarbVideo:
    """Generate perfectly synced lip animation videos"""
    
    # Rhubarb Preston Blair mouth shapes (CORRECTED MAPPING)
    PHONEME_TO_RHUBARB = {
        # A - Rest/Silence
        'sil': 'A', '': 'A', 'silence': 'A',
        
        # B - Lips together (M, B, P)
        'm': 'B', 'b': 'B', 'p': 'B',
        
        # C - Tongue/teeth (S, Z, T, D, K, G, N, TH, Y, H)
        's': 'C', 'z': 'C', 't': 'C', 'd': 'C', 'k': 'C', 'g': 'C',
        'n': 'C', 'θ': 'C', 'ð': 'C', 'j': 'C', 'h': 'C', 'ʃ': 'C',
        'ʒ': 'C', 'tʃ': 'C', 'dʒ': 'C', 'ŋ': 'C', 'y': 'C',
        
        # D - Wide open (AA, AE) - Corrected for wider vowels
        'æ': 'D', 'ɑ': 'D', 'a': 'D', 'aɪ': 'D', 'aʊ': 'D', 'ā': 'D',
        
        # E - Rounded open (AH, AO, O sounds)
        'ʌ': 'E', 'ɔ': 'E', 'ɔɪ': 'E', 'o': 'E', 'au': 'E',
        
        # F - Slight open (EH, UH, IH, IY, EY)
        'ɛ': 'F', 'ə': 'F', 'ɪ': 'F', 'i': 'F', 'e': 'F', 'eɪ': 'F', 'ī': 'F', 'ai': 'F',
        
        # G - Teeth on lip (F, V)
        'f': 'G', 'v': 'G',
        
        # H - Tongue up (L)
        'l': 'H', 'ḷ': 'H',
        
        # X - Rounded forward (W, R, OO, OW, UW, U sounds)
        'w': 'X', 'r': 'X', 'ʊ': 'X', 'u': 'X', 'oʊ': 'X', 'ū': 'X',
    }
    
    def __init__(self, width: int = 800, height: int = 600, fps: int = 15):
        self.width = width
        self.height = height
        self.fps = fps
        self.mapper = get_phoneme_viseme_mapper()
    
    def generate_animation(self, word: str, language: str, output_path: str, audio_path: str = None) -> str:
        """
        Generate perfectly synced lip animation
        
        Args:
            word: Word to animate
            language: Language code
            output_path: Output video path
            audio_path: Path to audio file (for perfect sync)
        """
        
        print(f"\n{'='*70}")
        print(f"🎬 GENERATING SYNCED RHUBARB LIP ANIMATION")
        print(f"{'='*70}")
        print(f"Word: {word}")
        print(f"Language: {language}")
        print(f"Audio: {audio_path}")
        print(f"Output: {output_path}")
        
        # Get phoneme timing data
        viseme_data = self.mapper.word_to_visemes(word, language)
        visemes = viseme_data['visemes']
        
        # Get actual audio duration if audio file provided
        audio_duration_ms = viseme_data['total_duration']
        if audio_path and os.path.exists(audio_path):
            audio_duration_ms = self._get_audio_duration(audio_path)
            print(f"✅ Using actual audio duration: {audio_duration_ms}ms")
        
        print(f"Phonemes: {len(visemes)}")
        print(f"Total duration: {audio_duration_ms}ms")
        
        # Generate frames with proper timing
        frames = []
        total_frames = int((audio_duration_ms / 1000.0) * self.fps)
        
        # Calculate frame timing for each phoneme
        current_frame = 0
        for viseme_info in visemes:
            phoneme = viseme_info['phoneme']
            duration_ms = viseme_info['duration']
            
            # Calculate frames for this phoneme
            num_frames = max(1, int((duration_ms / 1000.0) * self.fps))
            
            # Get Rhubarb shape
            shape = self.PHONEME_TO_RHUBARB.get(phoneme, 'A')
            
            print(f"  {phoneme:4s} → {shape} ({num_frames} frames, {duration_ms}ms)")
            
            # Generate frames
            for _ in range(num_frames):
                frame = self._create_professional_frame(phoneme, shape, word)
                frames.append(frame)
                current_frame += 1
        
        # Pad to match audio duration exactly
        while len(frames) < total_frames:
            frames.append(frames[-1] if frames else self._create_professional_frame('', 'A', word))
        
        print(f"\nGenerated {len(frames)} frames ({len(frames)/self.fps:.2f}s)")
        
        # Save as video using moviepy
        try:
            import moviepy
            from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
            
            # Convert PIL images to numpy arrays
            frame_arrays = [np.array(frame) for frame in frames]
            
            # Create video clip
            clip = ImageSequenceClip(frame_arrays, fps=self.fps)
            
            # Add audio if provided
            if audio_path and os.path.exists(audio_path):
                try:
                    from moviepy.audio.io.AudioFileClip import AudioFileClip
                    audio_clip = AudioFileClip(audio_path)
                    clip = clip.set_audio(audio_clip)
                    print(f"✅ Audio track added")
                except Exception as e:
                    print(f"⚠️ Could not add audio: {e}")
                    print(f"   Video will be generated without audio track")
            
            # Write video with H.264 codec
            print(f"\n📹 Encoding video...")
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac' if audio_path else None,
                preset='ultrafast',
                ffmpeg_params=['-pix_fmt', 'yuv420p'],
                logger=None  # Suppress moviepy logs
            )
            
            print(f"\n✅ Video saved: {output_path}")
            print(f"✅ Codec: H.264 (browser-compatible)")
            print(f"✅ Audio: {'Synced' if audio_path else 'No audio'}")
            print(f"{'='*70}\n")
            
            return output_path
            
        except ImportError:
            print("❌ moviepy not installed!")
            raise
    
    def _get_audio_duration(self, audio_path: str) -> int:
        """Get audio duration in milliseconds"""
        try:
            import librosa
            audio, sr = librosa.load(audio_path, sr=None)
            duration_sec = len(audio) / sr
            return int(duration_sec * 1000)
        except:
            # Fallback: use ffprobe
            try:
                result = subprocess.run([
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    audio_path
                ], capture_output=True, text=True)
                duration_sec = float(result.stdout.strip())
                return int(duration_sec * 1000)
            except:
                return 1000  # Default 1 second
    
    def _create_professional_frame(self, phoneme: str, shape: str, word: str) -> Image.Image:
        """Create professional 2D animated frame"""
        
        # Create image with gradient background
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        # Gradient background (blue to white)
        for y in range(self.height):
            color_val = int(200 + (y / self.height) * 55)
            draw.rectangle([0, y, self.width, y+1], fill=(color_val-50, color_val-30, color_val))
        
        # Avatar position (centered)
        center_x = self.width // 2
        center_y = self.height // 2 - 30
        
        # Draw professional avatar
        self._draw_avatar(draw, center_x, center_y, shape)
        
        # Draw labels
        try:
            font_large = ImageFont.truetype("arial.ttf", 32)
            font_medium = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Word label at top
        word_text = f'"{word.upper()}"'
        bbox = draw.textbbox((0, 0), word_text, font=font_large)
        text_width = bbox[2] - bbox[0]
        draw.text((center_x - text_width//2, 30), word_text, 
                 fill=(50, 50, 50), font=font_large)
        
        # Phoneme and shape label at bottom
        label = f"Phoneme: {phoneme if phoneme else 'silence'} | Rhubarb Shape: {shape}"
        bbox = draw.textbbox((0, 0), label, font=font_small)
        text_width = bbox[2] - bbox[0]
        
        # Label background
        label_y = self.height - 50
        draw.rectangle([center_x - text_width//2 - 10, label_y - 5,
                       center_x + text_width//2 + 10, label_y + 25],
                      fill=(50, 50, 50, 230))
        
        draw.text((center_x - text_width//2, label_y), label,
                 fill=(255, 255, 255), font=font_small)
        
        return img
    
    def _draw_avatar(self, draw: ImageDraw.Draw, x: int, y: int, mouth_shape: str):
        """Draw professional 2D avatar with Rhubarb mouth"""
        
        # Face (larger, more realistic)
        face_w, face_h = 240, 300
        draw.ellipse([x - face_w//2, y - face_h//2, x + face_w//2, y + face_h//2],
                    fill=(235, 200, 180), outline=(200, 160, 140), width=3)
        
        # Eyes (more detailed)
        eye_y = y - 50
        eye_spacing = 60
        
        for eye_x in [x - eye_spacing, x + eye_spacing]:
            # Eye white
            draw.ellipse([eye_x - 18, eye_y - 12, eye_x + 18, eye_y + 12],
                        fill=(255, 255, 255), outline=(120, 120, 120), width=2)
            # Iris
            draw.ellipse([eye_x - 10, eye_y - 10, eye_x + 10, eye_y + 10],
                        fill=(80, 140, 200), outline=(50, 100, 150), width=1)
            # Pupil
            draw.ellipse([eye_x - 5, eye_y - 5, eye_x + 5, eye_y + 5],
                        fill=(20, 20, 20))
            # Highlight
            draw.ellipse([eye_x - 2, eye_y - 3, eye_x + 2, eye_y + 1],
                        fill=(255, 255, 255))
        
        # Eyebrows
        for brow_x in [x - eye_spacing, x + eye_spacing]:
            draw.arc([brow_x - 25, eye_y - 35, brow_x + 25, eye_y - 15],
                    start=180, end=360, fill=(100, 70, 50), width=4)
        
        # Nose
        nose_y = y + 10
        draw.ellipse([x - 12, nose_y - 20, x + 12, nose_y + 20],
                    fill=(220, 180, 160), outline=(200, 160, 140), width=2)
        # Nostrils
        draw.ellipse([x - 8, nose_y + 5, x - 3, nose_y + 10],
                    fill=(180, 140, 120))
        draw.ellipse([x + 3, nose_y + 5, x + 8, nose_y + 10],
                    fill=(180, 140, 120))
        
        # Mouth (Rhubarb shapes)
        mouth_y = y + 90
        self._draw_rhubarb_mouth(draw, x, mouth_y, mouth_shape)
    
    def _draw_rhubarb_mouth(self, draw: ImageDraw.Draw, x: int, y: int, shape: str):
        """Draw Rhubarb Preston Blair mouth shapes"""
        
        lip_color = (200, 100, 100)
        lip_outline = (160, 70, 70)
        teeth_color = (255, 255, 255)
        inner_mouth = (120, 40, 40)
        
        if shape == 'A':  # Rest - closed
            draw.ellipse([x - 45, y - 10, x + 45, y + 10],
                        fill=lip_color, outline=lip_outline, width=3)
        
        elif shape == 'B':  # Lips together (M, B, P)
            draw.line([x - 50, y, x + 50, y], fill=lip_outline, width=6)
            draw.ellipse([x - 50, y - 12, x + 50, y + 12],
                        fill=lip_color, outline=lip_outline, width=3)
        
        elif shape == 'C':  # Tongue/teeth (S, Z, T, D, K, G)
            draw.ellipse([x - 40, y - 18, x + 40, y + 18],
                        fill=lip_color, outline=lip_outline, width=3)
            # Teeth visible
            draw.rectangle([x - 25, y - 8, x + 25, y - 2], fill=teeth_color)
            draw.rectangle([x - 25, y + 2, x + 25, y + 8], fill=teeth_color)
        
        elif shape == 'D':  # Wide open (AA, AE)
            draw.ellipse([x - 50, y - 35, x + 50, y + 35],
                        fill=inner_mouth, outline=lip_outline, width=3)
            # Upper teeth
            draw.rectangle([x - 40, y - 30, x + 40, y - 20], fill=teeth_color)
            # Lower teeth
            draw.rectangle([x - 40, y + 20, x + 40, y + 30], fill=teeth_color)
        
        elif shape == 'E':  # Rounded open (AH, AO)
            draw.ellipse([x - 45, y - 28, x + 45, y + 28],
                        fill=inner_mouth, outline=lip_outline, width=3)
        
        elif shape == 'F':  # Slight open (EH, UH)
            draw.ellipse([x - 42, y - 15, x + 42, y + 15],
                        fill=lip_color, outline=lip_outline, width=3)
            # Small opening
            draw.ellipse([x - 20, y - 5, x + 20, y + 5],
                        fill=inner_mouth)
        
        elif shape == 'G':  # Teeth on lip (F, V)
            draw.ellipse([x - 40, y - 12, x + 40, y + 25],
                        fill=lip_color, outline=lip_outline, width=3)
            # Upper teeth on lower lip
            draw.rectangle([x - 30, y - 10, x + 30, y - 4], fill=teeth_color)
        
        elif shape == 'H':  # Tongue up (L)
            draw.ellipse([x - 40, y - 18, x + 40, y + 18],
                        fill=lip_color, outline=lip_outline, width=3)
            # Tongue visible
            draw.ellipse([x - 18, y - 12, x + 18, y + 2],
                        fill=(240, 120, 120))
        
        elif shape == 'X':  # Rounded forward (W, R)
            draw.ellipse([x - 28, y - 28, x + 28, y + 28],
                        fill=lip_color, outline=lip_outline, width=4)
            # Small circular opening
            draw.ellipse([x - 12, y - 12, x + 12, y + 12],
                        fill=inner_mouth)


# Singleton
_instance = None

def get_synced_rhubarb_video():
    global _instance
    if _instance is None:
        _instance = SyncedRhubarbVideo()
    return _instance
