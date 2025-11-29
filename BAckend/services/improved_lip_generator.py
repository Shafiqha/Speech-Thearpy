"""
Improved Lip Animation Generator
Uses actual mouth shape images for realistic animations
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .phoneme_viseme_mapper import get_phoneme_viseme_mapper


class ImprovedLipGenerator:
    """Generates lip animation videos using mouth shape images"""
    
    # Map visemes to mouth positions based on the reference image
    VISEME_TO_MOUTH_MAP = {
        'silence': 'closed',
        'PP': 'b_m_p',      # b, m, p - lips together
        'FF': 'f_v',        # f, v - teeth on lip
        'TH': 'th',         # th - tongue between teeth
        'DD': 'th',         # t, d - similar to th
        'kk': 'c_d_g_k',    # k, g - back of tongue
        'CH': 'ch_j_sh',    # ch, j, sh
        'SS': 'th',         # s, z - teeth together
        'nn': 'c_d_g_k',    # n - similar mouth shape
        'RR': 'r',          # r - specific r sound
        'aa': 'a',          # wide open
        'E': 'e_i',         # e, i - slight smile
        'I': 'e_i',         # i - narrow
        'O': 'o',           # o - rounded
        'U': 'u',           # u - pursed
        'WQ': 'w_q',        # w, q - rounded forward
        'L': 'l',           # l - tongue to roof
        'FV': 'f_v',        # f, v
    }
    
    def __init__(self, width: int = 640, height: int = 480, fps: int = 30):
        """Initialize the improved lip generator"""
        self.width = width
        self.height = height
        self.fps = fps
        self.mapper = get_phoneme_viseme_mapper()
        
        # Create mouth shapes directory (in api/media folder)
        api_dir = Path(__file__).parent.parent / 'api'
        self.mouth_dir = api_dir / 'media' / 'mouth_shapes'
        self.mouth_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Mouth shapes directory: {self.mouth_dir}")
        
        # Generate mouth shape images if they don't exist
        self._generate_mouth_shapes()
    
    def _generate_mouth_shapes(self):
        """Generate mouth shape images based on visemes"""
        
        # Define mouth shapes with coordinates (simplified version)
        mouth_shapes = {
            'closed': self._draw_closed_mouth,
            'a': self._draw_a_mouth,
            'e_i': self._draw_e_i_mouth,
            'o': self._draw_o_mouth,
            'u': self._draw_u_mouth,
            'b_m_p': self._draw_closed_mouth,
            'f_v': self._draw_f_v_mouth,
            'th': self._draw_th_mouth,
            'ch_j_sh': self._draw_ch_mouth,
            'r': self._draw_r_mouth,
            'l': self._draw_l_mouth,
            'w_q': self._draw_w_mouth,
            'c_d_g_k': self._draw_k_mouth,
        }
        
        for name, draw_func in mouth_shapes.items():
            img_path = self.mouth_dir / f"{name}.png"
            if not img_path.exists():
                img = draw_func()
                cv2.imwrite(str(img_path), img)
    
    def _create_base_canvas(self, bg_color=(255, 255, 255)):
        """Create base canvas for mouth drawing"""
        canvas = np.ones((200, 200, 3), dtype=np.uint8) * 255
        return canvas
    
    def _draw_closed_mouth(self):
        """Draw closed mouth (silence, b, m, p)"""
        canvas = self._create_base_canvas()
        # Draw lips closed
        cv2.ellipse(canvas, (100, 100), (60, 15), 0, 0, 360, (180, 100, 100), -1)
        cv2.ellipse(canvas, (100, 100), (60, 15), 0, 0, 360, (140, 80, 80), 2)
        return canvas
    
    def _draw_a_mouth(self):
        """Draw 'a' mouth (wide open)"""
        canvas = self._create_base_canvas()
        # Outer lip
        cv2.ellipse(canvas, (100, 100), (70, 50), 0, 0, 360, (180, 100, 100), -1)
        # Inner mouth (dark)
        cv2.ellipse(canvas, (100, 105), (50, 35), 0, 0, 360, (80, 40, 40), -1)
        # Teeth
        cv2.ellipse(canvas, (100, 85), (45, 15), 0, 0, 180, (255, 255, 255), -1)
        # Lip line
        cv2.ellipse(canvas, (100, 100), (70, 50), 0, 0, 360, (140, 80, 80), 2)
        return canvas
    
    def _draw_e_i_mouth(self):
        """Draw 'e' or 'i' mouth (slight smile)"""
        canvas = self._create_base_canvas()
        # Outer lip (wider, flatter)
        cv2.ellipse(canvas, (100, 100), (75, 20), 0, 0, 360, (180, 100, 100), -1)
        # Inner mouth
        cv2.ellipse(canvas, (100, 100), (55, 10), 0, 0, 360, (80, 40, 40), -1)
        # Teeth showing
        cv2.rectangle(canvas, (55, 95), (145, 105), (255, 255, 255), -1)
        # Lip line
        cv2.ellipse(canvas, (100, 100), (75, 20), 0, 0, 360, (140, 80, 80), 2)
        return canvas
    
    def _draw_o_mouth(self):
        """Draw 'o' mouth (rounded)"""
        canvas = self._create_base_canvas()
        # Outer lip (circular)
        cv2.circle(canvas, (100, 100), 40, (180, 100, 100), -1)
        # Inner mouth
        cv2.circle(canvas, (100, 100), 28, (80, 40, 40), -1)
        # Lip line
        cv2.circle(canvas, (100, 100), 40, (140, 80, 80), 2)
        return canvas
    
    def _draw_u_mouth(self):
        """Draw 'u' mouth (pursed)"""
        canvas = self._create_base_canvas()
        # Outer lip (small circle)
        cv2.circle(canvas, (100, 100), 30, (180, 100, 100), -1)
        # Inner mouth
        cv2.circle(canvas, (100, 100), 20, (80, 40, 40), -1)
        # Lip line
        cv2.circle(canvas, (100, 100), 30, (140, 80, 80), 2)
        return canvas
    
    def _draw_f_v_mouth(self):
        """Draw 'f' or 'v' mouth (teeth on lower lip)"""
        canvas = self._create_base_canvas()
        # Lower lip
        cv2.ellipse(canvas, (100, 110), (60, 20), 0, 0, 180, (180, 100, 100), -1)
        # Upper teeth
        cv2.rectangle(canvas, (55, 85), (145, 100), (255, 255, 255), -1)
        # Lip lines
        cv2.ellipse(canvas, (100, 110), (60, 20), 0, 0, 180, (140, 80, 80), 2)
        return canvas
    
    def _draw_th_mouth(self):
        """Draw 'th' mouth (tongue between teeth)"""
        canvas = self._create_base_canvas()
        # Outer lip
        cv2.ellipse(canvas, (100, 100), (65, 25), 0, 0, 360, (180, 100, 100), -1)
        # Teeth
        cv2.rectangle(canvas, (60, 90), (140, 100), (255, 255, 255), -1)
        # Tongue tip
        cv2.ellipse(canvas, (100, 105), (20, 10), 0, 0, 360, (220, 150, 150), -1)
        # Lip line
        cv2.ellipse(canvas, (100, 100), (65, 25), 0, 0, 360, (140, 80, 80), 2)
        return canvas
    
    def _draw_ch_mouth(self):
        """Draw 'ch', 'j', 'sh' mouth (lips forward)"""
        canvas = self._create_base_canvas()
        # Outer lip (protruding)
        cv2.ellipse(canvas, (100, 100), (50, 35), 0, 0, 360, (180, 100, 100), -1)
        # Inner mouth
        cv2.ellipse(canvas, (100, 100), (35, 20), 0, 0, 360, (80, 40, 40), -1)
        # Lip line
        cv2.ellipse(canvas, (100, 100), (50, 35), 0, 0, 360, (140, 80, 80), 2)
        return canvas
    
    def _draw_r_mouth(self):
        """Draw 'r' mouth"""
        canvas = self._create_base_canvas()
        # Similar to 'o' but slightly more open
        cv2.ellipse(canvas, (100, 100), (45, 30), 0, 0, 360, (180, 100, 100), -1)
        cv2.ellipse(canvas, (100, 100), (32, 18), 0, 0, 360, (80, 40, 40), -1)
        cv2.ellipse(canvas, (100, 100), (45, 30), 0, 0, 360, (140, 80, 80), 2)
        return canvas
    
    def _draw_l_mouth(self):
        """Draw 'l' mouth"""
        canvas = self._create_base_canvas()
        # Mouth slightly open
        cv2.ellipse(canvas, (100, 100), (60, 25), 0, 0, 360, (180, 100, 100), -1)
        cv2.ellipse(canvas, (100, 100), (45, 15), 0, 0, 360, (80, 40, 40), -1)
        # Tongue visible at top
        cv2.ellipse(canvas, (100, 90), (30, 8), 0, 0, 180, (220, 150, 150), -1)
        cv2.ellipse(canvas, (100, 100), (60, 25), 0, 0, 360, (140, 80, 80), 2)
        return canvas
    
    def _draw_w_mouth(self):
        """Draw 'w', 'q' mouth (rounded forward)"""
        canvas = self._create_base_canvas()
        # Very rounded and protruding
        cv2.circle(canvas, (100, 100), 35, (180, 100, 100), -1)
        cv2.circle(canvas, (100, 100), 25, (80, 40, 40), -1)
        cv2.circle(canvas, (100, 100), 35, (140, 80, 80), 2)
        return canvas
    
    def _draw_k_mouth(self):
        """Draw 'k', 'g' mouth"""
        canvas = self._create_base_canvas()
        # Mouth open, back of tongue raised
        cv2.ellipse(canvas, (100, 100), (65, 30), 0, 0, 360, (180, 100, 100), -1)
        cv2.ellipse(canvas, (100, 105), (48, 20), 0, 0, 360, (80, 40, 40), -1)
        cv2.ellipse(canvas, (100, 100), (65, 30), 0, 0, 360, (140, 80, 80), 2)
        return canvas
    
    def generate_animation(self, word: str, language: str = 'en', 
                          output_path: str = None) -> str:
        """Generate lip animation video"""
        
        # Get viseme sequence
        viseme_data = self.mapper.word_to_visemes(word, language)
        visemes = viseme_data['visemes']
        
        if not visemes:
            raise ValueError(f"No visemes generated for word: {word}")
        
        # Generate output path (in api/media folder)
        if output_path is None:
            api_dir = Path(__file__).parent.parent / 'api'
            output_dir = api_dir / 'media' / 'lip_animations'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{word}_{language}.mp4")
        
        print(f"🎬 Generating video: {output_path}")
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, 
                             (self.width, self.height))
        
        # Create frames
        for viseme_info in visemes:
            viseme = viseme_info['viseme']
            duration_ms = viseme_info['duration']
            num_frames = max(1, int((duration_ms / 1000.0) * self.fps))
            
            # Get mouth shape
            mouth_type = self.VISEME_TO_MOUTH_MAP.get(viseme, 'closed')
            mouth_img_path = self.mouth_dir / f"{mouth_type}.png"
            
            # Load mouth image
            if mouth_img_path.exists():
                mouth_img = cv2.imread(str(mouth_img_path))
            else:
                # Fallback to closed mouth
                mouth_img = self._draw_closed_mouth()
            
            # Create frame with face and mouth
            for _ in range(num_frames):
                frame = self._create_frame_with_mouth(
                    mouth_img, 
                    viseme_info['phoneme'],
                    self.mapper.get_viseme_description(viseme)
                )
                out.write(frame)
        
        out.release()
        
        print(f"✅ Generated lip animation: {output_path}")
        return output_path
    
    def _create_frame_with_mouth(self, mouth_img: np.ndarray, 
                                 phoneme: str, description: str) -> np.ndarray:
        """Create a complete frame with face, mouth, and labels"""
        
        # Create white background
        frame = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255
        
        # Draw face oval (skin tone)
        face_center = (self.width // 2, self.height // 2)
        cv2.ellipse(frame, face_center, (150, 200), 0, 0, 360, 
                   (220, 180, 160), -1)
        
        # Draw eyes
        left_eye = (face_center[0] - 60, face_center[1] - 60)
        right_eye = (face_center[0] + 60, face_center[1] - 60)
        
        # Eye whites
        cv2.circle(frame, left_eye, 20, (255, 255, 255), -1)
        cv2.circle(frame, right_eye, 20, (255, 255, 255), -1)
        
        # Pupils
        cv2.circle(frame, left_eye, 10, (80, 60, 40), -1)
        cv2.circle(frame, right_eye, 10, (80, 60, 40), -1)
        
        # Eyebrows
        cv2.ellipse(frame, (left_eye[0], left_eye[1] - 25), (25, 8), 
                   0, 0, 180, (80, 60, 40), 3)
        cv2.ellipse(frame, (right_eye[0], right_eye[1] - 25), (25, 8), 
                   0, 0, 180, (80, 60, 40), 3)
        
        # Nose
        nose_pts = np.array([
            [face_center[0], face_center[1] - 20],
            [face_center[0] - 15, face_center[1] + 20],
            [face_center[0] + 15, face_center[1] + 20]
        ], np.int32)
        cv2.polylines(frame, [nose_pts], False, (180, 140, 120), 2)
        
        # Place mouth image
        mouth_h, mouth_w = mouth_img.shape[:2]
        mouth_y = face_center[1] + 40
        mouth_x = face_center[0] - mouth_w // 2
        
        # Resize mouth to fit
        mouth_resized = cv2.resize(mouth_img, (160, 100))
        mouth_h, mouth_w = mouth_resized.shape[:2]
        mouth_x = face_center[0] - mouth_w // 2
        
        # Blend mouth onto face
        y1, y2 = mouth_y, mouth_y + mouth_h
        x1, x2 = mouth_x, mouth_x + mouth_w
        
        if y2 <= self.height and x2 <= self.width and y1 >= 0 and x1 >= 0:
            frame[y1:y2, x1:x2] = mouth_resized
        
        # Add text labels
        cv2.putText(frame, f"Phoneme: {phoneme}", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        # Add description at bottom (wrap text if too long)
        desc_text = description[:50]
        cv2.putText(frame, desc_text, (20, self.height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        
        return frame


# Singleton instance
_improved_generator = None

def get_improved_lip_generator() -> ImprovedLipGenerator:
    """Get singleton instance"""
    global _improved_generator
    if _improved_generator is None:
        _improved_generator = ImprovedLipGenerator()
    return _improved_generator
