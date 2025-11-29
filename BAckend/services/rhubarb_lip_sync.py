"""
Rhubarb Lip Sync Integration
Uses Preston Blair phoneme mouth shapes for realistic 2D lip animation
Based on: https://github.com/scaredyfish/blender-rhubarb-lipsync
"""

import cv2
import numpy as np
import os
from typing import List, Dict, Tuple
from pathlib import Path
from .phoneme_viseme_mapper import get_phoneme_viseme_mapper


class RhubarbLipSync:
    """
    Rhubarb Lip Sync uses 9 mouth shapes (A-H + X):
    - A: Rest position (closed mouth)
    - B: Consonants: M, B, P
    - C: Consonants: S, Z, T, D, K, G, N, TH, Y, H
    - D: Vowels: AA, AE (as in "bat")
    - E: Vowels: AH, AO (as in "hot")
    - F: Vowels: EH, AE, UH (as in "bed", "but")
    - G: Consonants: F, V
    - H: Consonants: L
    - X: Consonants: W, Q, R
    """
    
    # Map phonemes to Rhubarb mouth shapes
    PHONEME_TO_RHUBARB = {
        # Rest/Silence
        'silence': 'A',
        
        # B shape - Lips together (M, B, P)
        'm': 'B', 'b': 'B', 'p': 'B',
        
        # C shape - Tongue/teeth consonants (S, Z, T, D, K, G, N, TH, Y, H)
        's': 'C', 'z': 'C', 't': 'C', 'd': 'C', 
        'k': 'C', 'g': 'C', 'n': 'C', 'θ': 'C', 
        'ð': 'C', 'j': 'C', 'h': 'C', 'ŋ': 'C',
        
        # D shape - Wide open (AA, AE)
        'æ': 'D', 'ɑ': 'D', 'a': 'D',
        
        # E shape - Rounded open (AH, AO)
        'ʌ': 'E', 'ɔ': 'E', 'ɒ': 'E',
        
        # F shape - Slight open (EH, UH)
        'ɛ': 'F', 'ə': 'F', 'ɪ': 'F', 'e': 'F',
        
        # G shape - Teeth on lip (F, V)
        'f': 'G', 'v': 'G',
        
        # H shape - Tongue up (L)
        'l': 'H',
        
        # X shape - Rounded forward (W, Q, R)
        'w': 'X', 'r': 'X', 'ʊ': 'X', 'u': 'X', 'oʊ': 'X', 'o': 'X',
        
        # Additional mappings
        'i': 'F', 'ʃ': 'C', 'ʒ': 'C', 'tʃ': 'C', 'dʒ': 'C',
    }
    
    def __init__(self, width: int = 640, height: int = 480, fps: int = 30):
        """Initialize Rhubarb Lip Sync generator"""
        self.width = width
        self.height = height
        self.fps = fps
        self.mapper = get_phoneme_viseme_mapper()
        
        # Create mouth shapes directory
        api_dir = Path(__file__).parent.parent / 'api'
        self.mouth_dir = api_dir / 'media' / 'rhubarb_mouths'
        self.mouth_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Rhubarb mouth shapes directory: {self.mouth_dir}")
        
        # Generate mouth shape images if they don't exist
        try:
            existing_shapes = list(self.mouth_dir.glob("*.png"))
            if len(existing_shapes) < 9:
                print(f"⚠️ Found only {len(existing_shapes)} mouth shapes, generating all 9...")
                self._generate_rhubarb_mouths()
            else:
                print(f"✅ Found {len(existing_shapes)} mouth shapes")
        except Exception as e:
            print(f"⚠️ Error checking mouth shapes: {e}, generating...")
            self._generate_rhubarb_mouths()
    
    def _generate_rhubarb_mouths(self):
        """Generate all 9 Rhubarb mouth shapes"""
        
        mouth_generators = {
            'A': self._draw_mouth_A,  # Rest
            'B': self._draw_mouth_B,  # M, B, P
            'C': self._draw_mouth_C,  # S, Z, T, D, K, G
            'D': self._draw_mouth_D,  # AA, AE (wide)
            'E': self._draw_mouth_E,  # AH, AO (rounded)
            'F': self._draw_mouth_F,  # EH, UH (slight)
            'G': self._draw_mouth_G,  # F, V (teeth)
            'H': self._draw_mouth_H,  # L (tongue)
            'X': self._draw_mouth_X,  # W, R (rounded forward)
        }
        
        for shape_name, generator_func in mouth_generators.items():
            img_path = self.mouth_dir / f"{shape_name}.png"
            if not img_path.exists():
                img = generator_func()
                cv2.imwrite(str(img_path), img)
                print(f"✅ Generated mouth shape: {shape_name}")
    
    def _create_mouth_canvas(self):
        """Create base canvas for mouth drawing"""
        canvas = np.ones((300, 300, 3), dtype=np.uint8) * 255
        return canvas
    
    def _draw_mouth_A(self):
        """A - Rest position (closed mouth)"""
        canvas = self._create_mouth_canvas()
        center = (150, 150)
        
        # Draw closed lips
        cv2.ellipse(canvas, center, (80, 18), 0, 0, 360, (200, 120, 120), -1)
        cv2.ellipse(canvas, center, (80, 18), 0, 0, 360, (150, 80, 80), 3)
        
        # Lip line
        cv2.line(canvas, (70, 150), (230, 150), (120, 60, 60), 2)
        
        return canvas
    
    def _draw_mouth_B(self):
        """B - Lips together (M, B, P)"""
        canvas = self._create_mouth_canvas()
        center = (150, 150)
        
        # Lips pressed together
        cv2.ellipse(canvas, center, (75, 25), 0, 0, 360, (200, 120, 120), -1)
        cv2.ellipse(canvas, center, (75, 25), 0, 0, 360, (150, 80, 80), 3)
        
        # Strong center line
        cv2.line(canvas, (75, 150), (225, 150), (100, 50, 50), 4)
        
        return canvas
    
    def _draw_mouth_C(self):
        """C - Tongue/teeth consonants (S, Z, T, D, K, G)"""
        canvas = self._create_mouth_canvas()
        center = (150, 150)
        
        # Slightly open mouth
        cv2.ellipse(canvas, center, (85, 30), 0, 0, 360, (200, 120, 120), -1)
        
        # Inner mouth (dark)
        cv2.ellipse(canvas, (150, 155), (65, 18), 0, 0, 360, (80, 40, 40), -1)
        
        # Teeth showing
        cv2.rectangle(canvas, (85, 145), (215, 155), (255, 255, 255), -1)
        
        # Lip outline
        cv2.ellipse(canvas, center, (85, 30), 0, 0, 360, (150, 80, 80), 3)
        
        return canvas
    
    def _draw_mouth_D(self):
        """D - Wide open (AA, AE as in 'bat')"""
        canvas = self._create_mouth_canvas()
        center = (150, 150)
        
        # Wide open mouth
        cv2.ellipse(canvas, center, (90, 55), 0, 0, 360, (200, 120, 120), -1)
        
        # Inner mouth (very dark)
        cv2.ellipse(canvas, (150, 160), (70, 40), 0, 0, 360, (60, 30, 30), -1)
        
        # Upper teeth
        cv2.ellipse(canvas, (150, 125), (65, 18), 0, 0, 180, (255, 255, 255), -1)
        
        # Lower teeth hint
        cv2.ellipse(canvas, (150, 175), (60, 15), 0, 180, 360, (240, 240, 240), -1)
        
        # Lip outline
        cv2.ellipse(canvas, center, (90, 55), 0, 0, 360, (150, 80, 80), 3)
        
        return canvas
    
    def _draw_mouth_E(self):
        """E - Rounded open (AH, AO as in 'hot')"""
        canvas = self._create_mouth_canvas()
        center = (150, 150)
        
        # Rounded open mouth
        cv2.ellipse(canvas, center, (70, 50), 0, 0, 360, (200, 120, 120), -1)
        
        # Inner mouth
        cv2.ellipse(canvas, (150, 155), (50, 35), 0, 0, 360, (70, 35, 35), -1)
        
        # Upper teeth
        cv2.ellipse(canvas, (150, 130), (45, 15), 0, 0, 180, (255, 255, 255), -1)
        
        # Lip outline
        cv2.ellipse(canvas, center, (70, 50), 0, 0, 360, (150, 80, 80), 3)
        
        return canvas
    
    def _draw_mouth_F(self):
        """F - Slight open (EH, UH as in 'bed', 'but')"""
        canvas = self._create_mouth_canvas()
        center = (150, 150)
        
        # Slightly open, wider than C
        cv2.ellipse(canvas, center, (90, 28), 0, 0, 360, (200, 120, 120), -1)
        
        # Inner mouth
        cv2.ellipse(canvas, (150, 153), (70, 16), 0, 0, 360, (80, 40, 40), -1)
        
        # Teeth showing
        cv2.rectangle(canvas, (80, 145), (220, 155), (255, 255, 255), -1)
        
        # Lip outline
        cv2.ellipse(canvas, center, (90, 28), 0, 0, 360, (150, 80, 80), 3)
        
        return canvas
    
    def _draw_mouth_G(self):
        """G - Teeth on lower lip (F, V)"""
        canvas = self._create_mouth_canvas()
        
        # Lower lip
        cv2.ellipse(canvas, (150, 165), (80, 25), 0, 0, 180, (200, 120, 120), -1)
        cv2.ellipse(canvas, (150, 165), (80, 25), 0, 0, 180, (150, 80, 80), 3)
        
        # Upper teeth on lower lip
        cv2.rectangle(canvas, (80, 135), (220, 150), (255, 255, 255), -1)
        
        # Teeth outline
        for x in range(80, 220, 20):
            cv2.line(canvas, (x, 135), (x, 150), (230, 230, 230), 1)
        
        return canvas
    
    def _draw_mouth_H(self):
        """H - Tongue up (L)"""
        canvas = self._create_mouth_canvas()
        center = (150, 150)
        
        # Mouth open
        cv2.ellipse(canvas, center, (80, 35), 0, 0, 360, (200, 120, 120), -1)
        
        # Inner mouth
        cv2.ellipse(canvas, (150, 155), (60, 25), 0, 0, 360, (80, 40, 40), -1)
        
        # Tongue visible at top
        cv2.ellipse(canvas, (150, 135), (50, 15), 0, 0, 180, (220, 150, 150), -1)
        
        # Teeth
        cv2.rectangle(canvas, (90, 130), (210, 140), (255, 255, 255), -1)
        
        # Lip outline
        cv2.ellipse(canvas, center, (80, 35), 0, 0, 360, (150, 80, 80), 3)
        
        return canvas
    
    def _draw_mouth_X(self):
        """X - Rounded forward (W, R)"""
        canvas = self._create_mouth_canvas()
        center = (150, 150)
        
        # Small rounded mouth protruding forward
        cv2.circle(canvas, center, 45, (200, 120, 120), -1)
        
        # Inner mouth (dark circle)
        cv2.circle(canvas, center, 32, (70, 35, 35), -1)
        
        # Lip outline (thick to show protrusion)
        cv2.circle(canvas, center, 45, (150, 80, 80), 4)
        
        # Highlight to show roundness
        cv2.ellipse(canvas, (140, 140), (15, 15), 0, 0, 180, (220, 140, 140), -1)
        
        return canvas
    
    def phoneme_to_rhubarb(self, phoneme: str) -> str:
        """Convert phoneme to Rhubarb mouth shape"""
        return self.PHONEME_TO_RHUBARB.get(phoneme.lower(), 'A')
    
    def generate_animation(self, word: str, language: str = 'en', 
                          output_path: str = None) -> str:
        """Generate lip sync animation using Rhubarb mouth shapes"""
        
        # Get phoneme sequence
        viseme_data = self.mapper.word_to_visemes(word, language)
        visemes = viseme_data['visemes']
        
        if not visemes:
            raise ValueError(f"No visemes generated for word: {word}")
        
        # Generate output path
        if output_path is None:
            api_dir = Path(__file__).parent.parent / 'api'
            output_dir = api_dir / 'media' / 'lip_animations'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{word}_{language}_rhubarb.mp4")
        
        print(f"🎬 Generating Rhubarb animation: {output_path}")
        
        # Initialize video writer with H.264 codec (browser-compatible)
        # Try different codecs in order of preference
        codecs_to_try = [
            ('avc1', 'H.264'),  # Best for browsers
            ('H264', 'H.264'),  # Alternative H.264
            ('X264', 'H.264'),  # Another H.264 variant
            ('mp4v', 'MPEG-4'), # Fallback
        ]
        
        out = None
        for codec_code, codec_name in codecs_to_try:
            try:
                fourcc = cv2.VideoWriter_fourcc(*codec_code)
                out = cv2.VideoWriter(output_path, fourcc, self.fps, 
                                     (self.width, self.height))
                if out.isOpened():
                    print(f"✅ Using codec: {codec_name} ({codec_code})")
                    break
                else:
                    out.release()
                    out = None
            except Exception as e:
                print(f"⚠️ Codec {codec_name} ({codec_code}) failed: {e}")
                continue
        
        if out is None or not out.isOpened():
            raise RuntimeError("Failed to initialize video writer with any codec")
        
        # Create frames
        for viseme_info in visemes:
            phoneme = viseme_info['phoneme']
            duration_ms = viseme_info['duration']
            num_frames = max(1, int((duration_ms / 1000.0) * self.fps))
            
            # Get Rhubarb mouth shape
            rhubarb_shape = self.phoneme_to_rhubarb(phoneme)
            mouth_img_path = self.mouth_dir / f"{rhubarb_shape}.png"
            
            # Load mouth image
            if mouth_img_path.exists():
                mouth_img = cv2.imread(str(mouth_img_path))
            else:
                # Fallback to rest position
                mouth_img = self._draw_mouth_A()
            
            # Create frame with face and mouth
            for _ in range(num_frames):
                frame = self._create_frame_with_mouth(
                    mouth_img,
                    phoneme,
                    rhubarb_shape
                )
                out.write(frame)
        
        out.release()
        
        print(f"✅ Generated Rhubarb lip animation: {output_path}")
        print(f"   Word: {word} ({language})")
        print(f"   Phonemes: {len(visemes)}")
        print(f"   Duration: {viseme_data['total_duration']}ms")
        
        # Convert to browser-compatible format using ffmpeg if available
        try:
            import subprocess
            output_path_h264 = output_path.replace('.mp4', '_h264.mp4')
            
            # Try to convert with ffmpeg
            result = subprocess.run([
                'ffmpeg', '-y', '-i', output_path,
                '-c:v', 'libx264',  # H.264 codec
                '-pix_fmt', 'yuv420p',  # Compatible pixel format
                '-movflags', '+faststart',  # Enable streaming
                output_path_h264
            ], capture_output=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(output_path_h264):
                print(f"✅ Converted to H.264: {output_path_h264}")
                # Replace original with H.264 version
                os.remove(output_path)
                os.rename(output_path_h264, output_path)
                print(f"✅ Video is now browser-compatible")
            else:
                print(f"⚠️ ffmpeg conversion failed, using original")
                print(f"   Error: {result.stderr.decode() if result.stderr else 'Unknown'}")
        except FileNotFoundError:
            print(f"⚠️ ffmpeg not found, video may not play in all browsers")
            print(f"   Install ffmpeg for best compatibility")
        except Exception as e:
            print(f"⚠️ Video conversion failed: {e}")
            print(f"   Using original video")
        
        return output_path
    
    def _create_frame_with_mouth(self, mouth_img: np.ndarray, 
                                 phoneme: str, rhubarb_shape: str) -> np.ndarray:
        """Create a complete frame with face, mouth, and labels"""
        
        # Create gradient background
        frame = np.ones((self.height, self.width, 3), dtype=np.uint8)
        for i in range(self.height):
            color = int(240 - (i / self.height) * 40)
            frame[i, :] = [color, color, 255]
        
        # Draw face oval (skin tone)
        face_center = (self.width // 2, self.height // 2)
        cv2.ellipse(frame, face_center, (200, 260), 0, 0, 360, 
                   (220, 190, 170), -1)
        
        # Draw face outline
        cv2.ellipse(frame, face_center, (200, 260), 0, 0, 360, 
                   (180, 150, 130), 3)
        
        # Draw eyes
        left_eye = (face_center[0] - 70, face_center[1] - 70)
        right_eye = (face_center[0] + 70, face_center[1] - 70)
        
        # Eye whites
        cv2.ellipse(frame, left_eye, (28, 20), 0, 0, 360, (255, 255, 255), -1)
        cv2.ellipse(frame, right_eye, (28, 20), 0, 0, 360, (255, 255, 255), -1)
        
        # Iris
        cv2.circle(frame, left_eye, 12, (100, 180, 220), -1)
        cv2.circle(frame, right_eye, 12, (100, 180, 220), -1)
        
        # Pupils
        cv2.circle(frame, left_eye, 6, (40, 40, 40), -1)
        cv2.circle(frame, right_eye, 6, (40, 40, 40), -1)
        
        # Eye highlights
        cv2.circle(frame, (left_eye[0] - 3, left_eye[1] - 3), 3, (255, 255, 255), -1)
        cv2.circle(frame, (right_eye[0] - 3, right_eye[1] - 3), 3, (255, 255, 255), -1)
        
        # Eyebrows
        cv2.ellipse(frame, (left_eye[0], left_eye[1] - 30), (35, 10), 
                   0, 0, 180, (80, 60, 40), 4)
        cv2.ellipse(frame, (right_eye[0], right_eye[1] - 30), (35, 10), 
                   0, 0, 180, (80, 60, 40), 4)
        
        # Nose
        nose_tip = (face_center[0], face_center[1] + 30)
        cv2.ellipse(frame, nose_tip, (20, 30), 0, 0, 360, (200, 170, 150), -1)
        cv2.ellipse(frame, nose_tip, (20, 30), 0, 0, 360, (180, 150, 130), 2)
        
        # Nostrils
        cv2.ellipse(frame, (nose_tip[0] - 10, nose_tip[1] + 10), (6, 8), 
                   0, 0, 360, (150, 120, 100), -1)
        cv2.ellipse(frame, (nose_tip[0] + 10, nose_tip[1] + 10), (6, 8), 
                   0, 0, 360, (150, 120, 100), -1)
        
        # Place mouth image
        mouth_h, mouth_w = mouth_img.shape[:2]
        mouth_y = face_center[1] + 80
        mouth_x = face_center[0] - mouth_w // 2
        
        # Resize mouth to fit
        mouth_resized = cv2.resize(mouth_img, (200, 200))
        mouth_h, mouth_w = mouth_resized.shape[:2]
        mouth_x = face_center[0] - mouth_w // 2
        
        # Blend mouth onto face
        y1, y2 = mouth_y, mouth_y + mouth_h
        x1, x2 = mouth_x, mouth_x + mouth_w
        
        if y2 <= self.height and x2 <= self.width and y1 >= 0 and x1 >= 0:
            # Alpha blend for smooth integration
            alpha = 0.9
            frame[y1:y2, x1:x2] = cv2.addWeighted(
                frame[y1:y2, x1:x2], 1 - alpha,
                mouth_resized, alpha, 0
            )
        
        # Add text labels with background
        label_text = f"Phoneme: {phoneme}  |  Shape: {rhubarb_shape}"
        
        # Text background
        cv2.rectangle(frame, (10, 10), (self.width - 10, 60), 
                     (255, 255, 255), -1)
        cv2.rectangle(frame, (10, 10), (self.width - 10, 60), 
                     (100, 100, 100), 2)
        
        # Text
        cv2.putText(frame, label_text, (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (50, 50, 50), 2)
        
        return frame


# Singleton instance
_rhubarb_generator = None

def get_rhubarb_lip_sync() -> RhubarbLipSync:
    """Get singleton instance"""
    global _rhubarb_generator
    if _rhubarb_generator is None:
        _rhubarb_generator = RhubarbLipSync()
    return _rhubarb_generator
