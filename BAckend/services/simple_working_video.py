"""
Simple Working Video Generator
Generates browser-compatible MP4 videos using PIL and moviepy
NO OPENCV - NO CODEC ISSUES
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pathlib import Path
from typing import List, Dict
from .phoneme_viseme_mapper import get_phoneme_viseme_mapper

class SimpleWorkingVideo:
    """Generate videos that ACTUALLY WORK in browsers"""
    
    # Rhubarb mouth shapes mapping
    PHONEME_TO_SHAPE = {
        # Rest
        'sil': 'A', '': 'A',
        
        # B shape - Lips together (M, B, P)
        'm': 'B', 'b': 'B', 'p': 'B',
        
        # C shape - Tongue/teeth (S, Z, T, D, K, G, N, TH, Y, H)
        's': 'C', 'z': 'C', 't': 'C', 'd': 'C', 'k': 'C', 'g': 'C',
        'n': 'C', 'θ': 'C', 'ð': 'C', 'j': 'C', 'h': 'C', 'ʃ': 'C',
        'ʒ': 'C', 'tʃ': 'C', 'dʒ': 'C', 'ŋ': 'C',
        
        # D shape - Wide open (AA, AE)
        'æ': 'D', 'ɑ': 'D', 'a': 'D', 'aɪ': 'D', 'aʊ': 'D',
        
        # E shape - Rounded open (AH, AO)
        'ʌ': 'E', 'ɔ': 'E', 'ɔɪ': 'E',
        
        # F shape - Slight open (EH, UH, IH, IY, EY)
        'ɛ': 'F', 'ə': 'F', 'ɪ': 'F', 'i': 'F', 'e': 'F', 'eɪ': 'F',
        
        # G shape - Teeth on lip (F, V)
        'f': 'G', 'v': 'G',
        
        # H shape - Tongue up (L)
        'l': 'H',
        
        # X shape - Rounded forward (W, R, OO, OW, UW)
        'w': 'X', 'r': 'X', 'ʊ': 'X', 'u': 'X', 'oʊ': 'X', 'o': 'X',
    }
    
    def __init__(self, width: int = 800, height: int = 600, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.mapper = get_phoneme_viseme_mapper()
    
    def generate_animation(self, word: str, language: str, output_path: str) -> str:
        """Generate video animation using PIL and moviepy"""
        
        print(f"\n{'='*60}")
        print(f"🎬 GENERATING BROWSER-COMPATIBLE VIDEO")
        print(f"{'='*60}")
        print(f"Word: {word}")
        print(f"Language: {language}")
        print(f"Output: {output_path}")
        
        # Get phoneme data
        viseme_data = self.mapper.word_to_visemes(word, language)
        visemes = viseme_data['visemes']
        
        print(f"Phonemes: {len(visemes)}")
        print(f"Duration: {viseme_data['total_duration']}ms")
        
        # Generate frames as PIL images
        frames = []
        for viseme_info in visemes:
            phoneme = viseme_info['phoneme']
            duration_ms = viseme_info['duration']
            num_frames = max(1, int((duration_ms / 1000.0) * self.fps))
            
            # Get mouth shape
            shape = self.PHONEME_TO_SHAPE.get(phoneme, 'A')
            
            # Create frame
            for _ in range(num_frames):
                frame = self._create_frame(phoneme, shape)
                frames.append(frame)
        
        print(f"Generated {len(frames)} frames")
        
        # Save as video using moviepy
        try:
            import moviepy
            from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
            
            # Convert PIL images to numpy arrays
            frame_arrays = [np.array(frame) for frame in frames]
            
            # Create video clip
            clip = ImageSequenceClip(frame_arrays, fps=self.fps)
            
            # Write video with H.264 codec
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio=False,
                preset='ultrafast',
                ffmpeg_params=['-pix_fmt', 'yuv420p']
            )
            
            print(f"✅ Video saved: {output_path}")
            print(f"✅ Codec: H.264 (browser-compatible)")
            print(f"{'='*60}\n")
            
            return output_path
            
        except ImportError:
            print("❌ moviepy not installed!")
            print("Installing moviepy...")
            import subprocess
            subprocess.check_call(['pip', 'install', 'moviepy'])
            print("✅ moviepy installed, please try again")
            raise
    
    def _create_frame(self, phoneme: str, shape: str) -> Image.Image:
        """Create a single frame with animated face"""
        
        # Create image
        img = Image.new('RGB', (self.width, self.height), color=(240, 245, 250))
        draw = ImageDraw.Draw(img)
        
        # Face position
        face_x = self.width // 2
        face_y = self.height // 2 - 50
        
        # Draw face (ellipse)
        face_width = 200
        face_height = 260
        draw.ellipse(
            [face_x - face_width//2, face_y - face_height//2,
             face_x + face_width//2, face_y + face_height//2],
            fill=(220, 190, 170),
            outline=(180, 150, 130),
            width=2
        )
        
        # Draw eyes
        eye_y = face_y - 40
        eye_spacing = 50
        
        for eye_x in [face_x - eye_spacing, face_x + eye_spacing]:
            # Eye white
            draw.ellipse(
                [eye_x - 14, eye_y - 10, eye_x + 14, eye_y + 10],
                fill=(255, 255, 255),
                outline=(100, 100, 100),
                width=1
            )
            # Iris
            draw.ellipse(
                [eye_x - 8, eye_y - 8, eye_x + 8, eye_y + 8],
                fill=(70, 130, 180),
                outline=(40, 80, 120),
                width=1
            )
            # Pupil
            draw.ellipse(
                [eye_x - 4, eye_y - 4, eye_x + 4, eye_y + 4],
                fill=(0, 0, 0)
            )
        
        # Draw nose
        nose_y = face_y + 20
        draw.ellipse(
            [face_x - 10, nose_y - 15, face_x + 10, nose_y + 15],
            fill=(200, 170, 150),
            outline=(180, 150, 130),
            width=1
        )
        
        # Draw mouth based on shape
        mouth_y = face_y + 80
        self._draw_mouth(draw, face_x, mouth_y, shape)
        
        # Draw labels
        try:
            font = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Label text
        label = f"Phoneme: {phoneme} | Shape: {shape}"
        
        # Draw label background
        bbox = draw.textbbox((0, 0), label, font=font_small)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        label_x = face_x - text_width // 2
        label_y = self.height - 60
        
        draw.rectangle(
            [label_x - 10, label_y - 5,
             label_x + text_width + 10, label_y + text_height + 5],
            fill=(50, 50, 50, 200)
        )
        
        draw.text((label_x, label_y), label, fill=(255, 255, 255), font=font_small)
        
        return img
    
    def _draw_mouth(self, draw: ImageDraw.Draw, x: int, y: int, shape: str):
        """Draw mouth shape"""
        
        if shape == 'A':  # Rest - closed
            draw.ellipse([x - 40, y - 8, x + 40, y + 8],
                        fill=(180, 100, 100), outline=(140, 70, 70), width=2)
        
        elif shape == 'B':  # Lips together (M, B, P)
            draw.line([x - 40, y, x + 40, y], fill=(140, 70, 70), width=4)
        
        elif shape == 'C':  # Tongue/teeth (S, Z, T, D, K, G)
            draw.ellipse([x - 35, y - 15, x + 35, y + 15],
                        fill=(200, 120, 120), outline=(140, 70, 70), width=2)
            # Teeth
            draw.rectangle([x - 20, y - 5, x + 20, y], fill=(255, 255, 255))
        
        elif shape == 'D':  # Wide open (AA, AE)
            draw.ellipse([x - 45, y - 30, x + 45, y + 30],
                        fill=(100, 40, 40), outline=(140, 70, 70), width=2)
            # Teeth
            draw.rectangle([x - 35, y - 25, x + 35, y - 15], fill=(255, 255, 255))
        
        elif shape == 'E':  # Rounded open (AH, AO)
            draw.ellipse([x - 40, y - 25, x + 40, y + 25],
                        fill=(120, 50, 50), outline=(140, 70, 70), width=2)
        
        elif shape == 'F':  # Slight open (EH, UH)
            draw.ellipse([x - 38, y - 12, x + 38, y + 12],
                        fill=(180, 100, 100), outline=(140, 70, 70), width=2)
        
        elif shape == 'G':  # Teeth on lip (F, V)
            draw.ellipse([x - 35, y - 10, x + 35, y + 20],
                        fill=(200, 120, 120), outline=(140, 70, 70), width=2)
            # Upper teeth on lower lip
            draw.rectangle([x - 25, y - 8, x + 25, y - 3], fill=(255, 255, 255))
        
        elif shape == 'H':  # Tongue up (L)
            draw.ellipse([x - 35, y - 15, x + 35, y + 15],
                        fill=(200, 120, 120), outline=(140, 70, 70), width=2)
            # Tongue
            draw.ellipse([x - 15, y - 10, x + 15, y], fill=(220, 100, 100))
        
        elif shape == 'X':  # Rounded forward (W, R)
            draw.ellipse([x - 25, y - 25, x + 25, y + 25],
                        fill=(180, 100, 100), outline=(140, 70, 70), width=3)


# Singleton instance
_instance = None

def get_simple_working_video():
    global _instance
    if _instance is None:
        _instance = SimpleWorkingVideo()
    return _instance
