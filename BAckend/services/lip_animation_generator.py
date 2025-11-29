"""
Lip Animation Video Generator
Generates lip-sync animation videos from phoneme/viseme data
Creates visual representation of mouth movements for pronunciation practice
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import os
from pathlib import Path
from PIL import Image
from .phoneme_viseme_mapper import get_phoneme_viseme_mapper


class LipAnimationGenerator:
    """Generates lip animation videos from viseme sequences"""
    
    # Mapping from viseme codes to Rhubarb mouth shapes
    VISEME_TO_RHUBARB = {
        'silence': 'A',
        'PP': 'B',  # Lips together
        'FF': 'F',  # Lower lip to upper teeth
        'TH': 'G',  # Tongue between teeth
        'DD': 'D',  # Tongue to roof
        'kk': 'C',  # Back of tongue up
        'CH': 'F',  # Lips forward
        'SS': 'C',  # Teeth together
        'nn': 'D',  # Tongue to roof
        'RR': 'D',  # Tongue curled
        'aa': 'E',  # Wide open
        'E': 'D',   # Slight smile
        'I': 'B',   # Narrow opening
        'O': 'H',   # Rounded
        'U': 'H',   # Pursed
        'WQ': 'H',  # Rounded forward
        'L': 'D',   # Tongue to roof
        'FV': 'F',  # Teeth on lower lip
    }
    
    # Mouth shape coordinates for different visemes (fallback if sprites not available)
    MOUTH_SHAPES = {
        'silence': {  # Closed mouth
            'outer': [(100, 150), (120, 145), (140, 145), (160, 150), (140, 155), (120, 155)],
            'inner': None,
            'color': (180, 140, 120)
        },
        'PP': {  # Lips together (P, B, M)
            'outer': [(100, 150), (120, 148), (140, 148), (160, 150), (140, 152), (120, 152)],
            'inner': None,
            'color': (180, 140, 120)
        },
        'FF': {  # Lower lip to upper teeth (F, V)
            'outer': [(100, 150), (120, 145), (140, 145), (160, 150), (140, 158), (120, 158)],
            'inner': [(115, 148), (125, 148), (135, 148), (145, 148)],
            'color': (180, 140, 120)
        },
        'TH': {  # Tongue between teeth
            'outer': [(100, 150), (120, 145), (140, 145), (160, 150), (140, 158), (120, 158)],
            'inner': [(120, 150), (130, 148), (140, 150), (130, 152)],
            'color': (220, 180, 160)
        },
        'DD': {  # Tongue to roof (T, D)
            'outer': [(100, 150), (120, 145), (140, 145), (160, 150), (140, 160), (120, 160)],
            'inner': [(110, 152), (130, 150), (150, 152), (130, 155)],
            'color': (180, 140, 120)
        },
        'kk': {  # Back of tongue up (K, G)
            'outer': [(100, 150), (120, 145), (140, 145), (160, 150), (140, 160), (120, 160)],
            'inner': [(110, 155), (130, 153), (150, 155), (130, 157)],
            'color': (180, 140, 120)
        },
        'CH': {  # Lips forward (CH, SH)
            'outer': [(105, 150), (120, 142), (140, 142), (155, 150), (140, 158), (120, 158)],
            'inner': [(118, 148), (130, 147), (142, 148), (130, 152)],
            'color': (180, 140, 120)
        },
        'SS': {  # Teeth together (S, Z)
            'outer': [(100, 150), (120, 145), (140, 145), (160, 150), (140, 155), (120, 155)],
            'inner': [(115, 149), (130, 149), (145, 149), (130, 151)],
            'color': (180, 140, 120)
        },
        'nn': {  # Tongue to roof, mouth open (N)
            'outer': [(100, 150), (120, 143), (140, 143), (160, 150), (140, 162), (120, 162)],
            'inner': [(110, 152), (130, 148), (150, 152), (130, 156)],
            'color': (180, 140, 120)
        },
        'RR': {  # Tongue curled (R)
            'outer': [(100, 150), (120, 145), (140, 145), (160, 150), (140, 160), (120, 160)],
            'inner': [(115, 153), (130, 150), (145, 153), (130, 156)],
            'color': (180, 140, 120)
        },
        'aa': {  # Wide open (AH)
            'outer': [(100, 150), (120, 140), (140, 140), (160, 150), (140, 170), (120, 170)],
            'inner': [(110, 148), (130, 145), (150, 148), (130, 165)],
            'color': (180, 140, 120)
        },
        'E': {  # Slight smile (E)
            'outer': [(95, 150), (120, 143), (140, 143), (165, 150), (140, 157), (120, 157)],
            'inner': [(110, 148), (130, 147), (150, 148), (130, 152)],
            'color': (180, 140, 120)
        },
        'I': {  # Narrow opening (I)
            'outer': [(105, 150), (120, 146), (140, 146), (155, 150), (140, 154), (120, 154)],
            'inner': [(118, 149), (130, 149), (142, 149), (130, 151)],
            'color': (180, 140, 120)
        },
        'O': {  # Rounded (O)
            'outer': [(110, 145), (125, 140), (135, 140), (150, 145), (135, 160), (125, 160)],
            'inner': [(120, 147), (130, 145), (140, 147), (130, 155)],
            'color': (180, 140, 120)
        },
        'U': {  # Pursed (U)
            'outer': [(115, 145), (125, 142), (135, 142), (145, 145), (135, 155), (125, 155)],
            'inner': [(122, 147), (130, 146), (138, 147), (130, 150)],
            'color': (180, 140, 120)
        },
        'WQ': {  # Rounded forward (W)
            'outer': [(110, 145), (125, 138), (135, 138), (150, 145), (135, 158), (125, 158)],
            'inner': [(120, 145), (130, 143), (140, 145), (130, 153)],
            'color': (180, 140, 120)
        },
        'L': {  # Tongue to roof, open (L)
            'outer': [(100, 150), (120, 143), (140, 143), (160, 150), (140, 160), (120, 160)],
            'inner': [(110, 150), (130, 147), (150, 150), (130, 155)],
            'color': (180, 140, 120)
        },
        'FV': {  # Teeth on lower lip (F, V)
            'outer': [(100, 150), (120, 145), (140, 145), (160, 150), (140, 158), (120, 158)],
            'inner': [(115, 148), (125, 148), (135, 148), (145, 148)],
            'color': (180, 140, 120)
        },
    }
    
    def __init__(self, width: int = 800, height: int = 600, fps: int = 24, sprites_dir: str = None):
        """
        Initialize lip animation generator
        
        Args:
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second (default 24 for smoother, slower animation)
            sprites_dir: Directory containing mouth shape sprite images
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.mapper = get_phoneme_viseme_mapper()
        
        # Load sprite images
        self.sprites_dir = self._find_sprites_dir(sprites_dir)
        self.sprites = self._load_sprites()
        
        if self.sprites:
            print(f"✅ Loaded {len(self.sprites)} mouth shape sprites for video generation")
        else:
            print(f"⚠️ No sprite images found. Using generated graphics.")
    
    def _find_sprites_dir(self, sprites_dir: str = None) -> Optional[str]:
        """Find directory containing mouth shape sprites"""
        possible_dirs = [
            sprites_dir,
            r"C:\Users\Shafiqha\Desktop\backup\backup\media\rhubarb_mouths",
            os.path.join(os.path.dirname(__file__), "..", "..", "media", "rhubarb_mouths"),
            os.path.join(os.path.dirname(__file__), "..", "media", "rhubarb_mouths"),
            "./media/rhubarb_mouths",
            "./rhubarb_mouths",
        ]
        
        for dir_path in possible_dirs:
            if dir_path and os.path.exists(dir_path):
                # Check if it has mouth shape images
                test_files = ["A.png", "mouth-A.png", "lisa-A.png"]
                for test_file in test_files:
                    if os.path.exists(os.path.join(dir_path, test_file)):
                        return dir_path
        
        return None
    
    def _load_sprites(self) -> Dict[str, Image.Image]:
        """Load mouth shape sprite images"""
        sprites = {}
        
        if not self.sprites_dir:
            return sprites
        
        # Load Rhubarb mouth shapes (A-H, X)
        for shape in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'X']:
            possible_names = [
                f"{shape}.png",
                f"mouth-{shape}.png",
                f"mouth_{shape}.png",
                f"lisa-{shape}.png",
            ]
            
            for name in possible_names:
                sprite_path = os.path.join(self.sprites_dir, name)
                if os.path.exists(sprite_path):
                    try:
                        img = Image.open(sprite_path).convert('RGBA')
                        sprites[shape] = img
                        break
                    except Exception as e:
                        print(f"⚠️ Failed to load {name}: {e}")
        
        return sprites
    
    def draw_face_base(self, frame: np.ndarray) -> np.ndarray:
        """Draw base face structure"""
        # Face oval (skin tone)
        cv2.ellipse(frame, (self.width // 2, self.height // 2), 
                   (80, 110), 0, 0, 360, (220, 180, 160), -1)
        
        # Eyes
        cv2.circle(frame, (self.width // 2 - 40, self.height // 2 - 30), 
                  15, (255, 255, 255), -1)
        cv2.circle(frame, (self.width // 2 + 40, self.height // 2 - 30), 
                  15, (255, 255, 255), -1)
        cv2.circle(frame, (self.width // 2 - 40, self.height // 2 - 30), 
                  8, (80, 60, 40), -1)
        cv2.circle(frame, (self.width // 2 + 40, self.height // 2 - 30), 
                  8, (80, 60, 40), -1)
        
        # Nose
        nose_points = np.array([
            [self.width // 2, self.height // 2 - 10],
            [self.width // 2 - 8, self.height // 2 + 10],
            [self.width // 2 + 8, self.height // 2 + 10]
        ], np.int32)
        cv2.polylines(frame, [nose_points], False, (180, 140, 120), 2)
        
        return frame
    
    def draw_mouth_sprite(self, pil_image: Image.Image, viseme: str, 
                          word: str = "", phoneme: str = "") -> Image.Image:
        """
        Draw mouth shape sprite for a specific viseme
        
        Args:
            pil_image: PIL Image to draw on
            viseme: Viseme shape identifier
            word: Word being spoken (for display)
            phoneme: Phoneme being spoken (for display)
            
        Returns:
            PIL Image with mouth sprite
        """
        # Map viseme to Rhubarb shape
        rhubarb_shape = self.VISEME_TO_RHUBARB.get(viseme, 'A')
        
        if self.sprites and rhubarb_shape in self.sprites:
            # Use sprite image
            sprite = self.sprites[rhubarb_shape]
            
            # Resize sprite to fit nicely (60% of width)
            sprite_width = int(self.width * 0.6)
            sprite_height = int(sprite.height * (sprite_width / sprite.width))
            sprite_resized = sprite.resize((sprite_width, sprite_height), Image.Resampling.LANCZOS)
            
            # Center sprite
            x = (self.width - sprite_width) // 2
            y = (self.height - sprite_height) // 2
            
            # Paste sprite (with alpha channel)
            pil_image.paste(sprite_resized, (x, y), sprite_resized)
        else:
            # Fallback to drawn graphics
            cv_frame = np.array(pil_image)
            cv_frame = self.draw_face_base(cv_frame)
            cv_frame = self.draw_mouth(cv_frame, viseme)
            pil_image = Image.fromarray(cv_frame)
        
        # Add text labels
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(pil_image)
        
        try:
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 20)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Word at top
        if word:
            word_text = f'"{word.upper()}"'
            bbox = draw.textbbox((0, 0), word_text, font=font_large)
            text_width = bbox[2] - bbox[0]
            draw.text((self.width//2 - text_width//2, 30), word_text, fill=(50, 50, 50), font=font_large)
        
        # Phoneme/viseme info at bottom
        if phoneme:
            label = f"Phoneme: {phoneme} | Viseme: {viseme} | Shape: {rhubarb_shape}"
            bbox = draw.textbbox((0, 0), label, font=font_small)
            text_width = bbox[2] - bbox[0]
            draw.text((self.width//2 - text_width//2, self.height - 50), label, fill=(100, 100, 100), font=font_small)
        
        return pil_image
    
    def draw_mouth(self, frame: np.ndarray, viseme: str, 
                   transition_progress: float = 1.0) -> np.ndarray:
        """
        Draw mouth shape for a specific viseme (fallback method)
        
        Args:
            frame: Video frame to draw on
            viseme: Viseme shape identifier
            transition_progress: Transition progress (0-1) for smooth animation
        """
        if viseme not in self.MOUTH_SHAPES:
            viseme = 'silence'
        
        mouth_data = self.MOUTH_SHAPES[viseme]
        
        # Offset to center mouth on face
        offset_x = self.width // 2 - 130
        offset_y = self.height // 2 - 50
        
        # Draw outer mouth shape
        outer_points = np.array([
            [p[0] + offset_x, p[1] + offset_y] for p in mouth_data['outer']
        ], np.int32)
        
        # Apply transition scaling
        if transition_progress < 1.0:
            center = outer_points.mean(axis=0)
            outer_points = center + (outer_points - center) * transition_progress
            outer_points = outer_points.astype(np.int32)
        
        cv2.fillPoly(frame, [outer_points], mouth_data['color'])
        cv2.polylines(frame, [outer_points], True, (140, 100, 80), 2)
        
        # Draw inner mouth (if exists)
        if mouth_data['inner'] is not None:
            inner_points = np.array([
                [p[0] + offset_x, p[1] + offset_y] for p in mouth_data['inner']
            ], np.int32)
            
            if transition_progress < 1.0:
                center = inner_points.mean(axis=0)
                inner_points = center + (inner_points - center) * transition_progress
                inner_points = inner_points.astype(np.int32)
            
            cv2.fillPoly(frame, [inner_points], (100, 50, 50))
        
        return frame
    
    def interpolate_viseme(self, viseme1: str, viseme2: str, 
                          progress: float) -> str:
        """
        Interpolate between two visemes for smooth transitions
        For simplicity, returns the target viseme when progress > 0.5
        """
        return viseme2 if progress > 0.5 else viseme1
    
    def generate_animation(self, word: str, language: str = 'en', 
                          output_path: str = None) -> str:
        """
        Generate lip animation video for a word
        
        Args:
            word: Word to animate
            language: Language code
            output_path: Path to save video (auto-generated if None)
            
        Returns:
            Path to generated video file
        """
        # Get viseme sequence
        viseme_data = self.mapper.word_to_visemes(word, language)
        visemes = viseme_data['visemes']
        
        if not visemes:
            raise ValueError(f"No visemes generated for word: {word}")
        
        # Generate output path if not provided
        if output_path is None:
            output_dir = Path('media/lip_animations')
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{word}_{language}.mp4")
        
        # Generate frames as PIL Images
        frames = []
        
        # Add silence at start (longer for slower pace)
        for _ in range(int(self.fps * 0.5)):  # 500ms silence
            pil_frame = Image.new('RGB', (self.width, self.height), color=(240, 240, 250))
            pil_frame = self.draw_mouth_sprite(pil_frame, 'silence', word=word)
            frames.append(pil_frame)
        
        # Generate frames for each viseme with smooth transitions
        for i, viseme_info in enumerate(visemes):
            viseme = viseme_info['viseme']
            phoneme = viseme_info['phoneme']
            duration_ms = viseme_info['duration']
            
            # Increase duration by 50% for slower animation
            duration_ms = int(duration_ms * 1.5)
            num_frames = int((duration_ms / 1000.0) * self.fps)
            
            # Get next viseme for smooth transition
            next_viseme = visemes[i + 1]['viseme'] if i + 1 < len(visemes) else 'silence'
            
            for frame_idx in range(num_frames):
                pil_frame = Image.new('RGB', (self.width, self.height), color=(240, 240, 250))
                
                # Add smooth transition in last 30% of frames
                transition_start = int(num_frames * 0.7)
                if frame_idx >= transition_start:
                    # Blend between current and next viseme
                    progress = (frame_idx - transition_start) / (num_frames - transition_start)
                    current_viseme = viseme if progress < 0.5 else next_viseme
                    pil_frame = self.draw_mouth_sprite(pil_frame, current_viseme, word=word, phoneme=phoneme)
                else:
                    pil_frame = self.draw_mouth_sprite(pil_frame, viseme, word=word, phoneme=phoneme)
                
                frames.append(pil_frame)
        
        # Add silence at end (longer for slower pace)
        for _ in range(int(self.fps * 0.7)):  # 700ms silence
            pil_frame = Image.new('RGB', (self.width, self.height), color=(240, 240, 250))
            pil_frame = self.draw_mouth_sprite(pil_frame, 'silence', word=word)
            frames.append(pil_frame)
        
        # Encode video using moviepy
        try:
            from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
            
            frame_arrays = [np.array(frame) for frame in frames]
            clip = ImageSequenceClip(frame_arrays, fps=self.fps)
            
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                preset='slow',  # Better quality, smoother output
                bitrate='2000k',  # Higher bitrate for smoother video
                ffmpeg_params=['-pix_fmt', 'yuv420p', '-crf', '18'],  # Lower CRF = better quality
                logger=None
            )
            
            clip.close()
        except ImportError:
            # Fallback to cv2 if moviepy not available
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, self.fps, 
                                 (self.width, self.height))
            
            for frame in frames:
                cv_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
                out.write(cv_frame)
            
            out.release()
        
        print(f"✅ Generated lip animation: {output_path}")
        print(f"   Word: {word} ({language})")
        print(f"   Phonemes: {len(visemes)}")
        print(f"   Duration: {viseme_data['total_duration']}ms")
        
        return output_path
    
    def generate_with_audio(self, word: str, language: str = 'en',
                           audio_path: str = None, output_path: str = None) -> Tuple[str, str]:
        """
        Generate lip animation with synchronized audio
        
        Args:
            word: Word to animate
            language: Language code
            audio_path: Path to audio file (generated if None)
            output_path: Path to save video
            
        Returns:
            Tuple of (video_path, audio_path)
        """
        # Generate audio if not provided
        if audio_path is None:
            from core.simple_tts import text_to_speech_file
            audio_dir = Path('media/lip_audio')
            audio_dir.mkdir(parents=True, exist_ok=True)
            audio_path = str(audio_dir / f"{word}_{language}.mp3")
            text_to_speech_file(word, audio_path, language)
        
        # Generate video
        video_path = self.generate_animation(word, language, output_path)
        
        return video_path, audio_path


# Singleton instance
_generator_instance = None

def get_lip_animation_generator() -> LipAnimationGenerator:
    """Get singleton instance of LipAnimationGenerator"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = LipAnimationGenerator()
    return _generator_instance
