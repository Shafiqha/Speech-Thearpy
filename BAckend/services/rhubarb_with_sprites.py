"""
Rhubarb Lip Sync with Sprite Images
Uses external mouth shape images (PNG sprites) for each Rhubarb shape
"""

import subprocess
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image
import numpy as np


class RhubarbWithSprites:
    """
    Uses Rhubarb Lip Sync with external sprite images
    Supports custom mouth shape images for professional animations
    """
    
    def __init__(self, 
                 rhubarb_path: str = None,
                 sprites_dir: str = None,
                 width: int = 800, 
                 height: int = 600, 
                 fps: int = 15):
        """
        Args:
            rhubarb_path: Path to rhubarb executable
            sprites_dir: Directory containing mouth shape images (A.png, B.png, etc.)
            width: Video width
            height: Video height
            fps: Frames per second
        """
        # Find Rhubarb
        possible_paths = [
            rhubarb_path,
            r"C:\Users\Shafiqha\Downloads\Rhubarb-Lip-Sync-1.13.0-Windows\Rhubarb-Lip-Sync-1.13.0-Windows\rhubarb.exe",
            "rhubarb",
            r"C:\rhubarb\rhubarb.exe",
        ]
        
        self.rhubarb_path = None
        for path in possible_paths:
            if path and self._check_rhubarb_path(path):
                self.rhubarb_path = path
                break
        
        self.width = width
        self.height = height
        self.fps = fps
        
        # Find sprites directory
        self.sprites_dir = self._find_sprites_dir(sprites_dir)
        self.sprites = self._load_sprites()
        
        self.rhubarb_available = self.rhubarb_path is not None
        
        if not self.rhubarb_available:
            print(f"⚠️ Rhubarb not found. Using fallback.")
        
        if not self.sprites:
            print(f"⚠️ No sprite images found. Using generated graphics.")
        else:
            print(f"✅ Loaded {len(self.sprites)} mouth shape sprites")
    
    def _check_rhubarb_path(self, path: str) -> bool:
        """Check if Rhubarb is accessible"""
        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Rhubarb found: {result.stdout.strip()}")
                return True
            return False
        except:
            return False
    
    def _find_sprites_dir(self, sprites_dir: str = None) -> Optional[str]:
        """Find directory containing mouth shape sprites"""
        possible_dirs = [
            sprites_dir,
            r"C:\Users\Shafiqha\Desktop\backup\backup\media\rhubarb_mouths",
            r"C:\Users\Shafiqha\Desktop\backup\backup\BAckend\media\rhubarb_mouths",
            r"C:\Users\Shafiqha\Downloads\Rhubarb-Lip-Sync-1.13.0-Windows\Rhubarb-Lip-Sync-1.13.0-Windows\res",
            r"C:\Users\Shafiqha\Downloads\Rhubarb-Lip-Sync-1.13.0-Windows\Rhubarb-Lip-Sync-1.13.0-Windows\extras",
            os.path.join(os.path.dirname(__file__), "..", "media", "rhubarb_mouths"),
            os.path.join(os.path.dirname(__file__), "..", "..", "media", "rhubarb_mouths"),
            "./media/rhubarb_mouths",
            "./rhubarb_mouths",
        ]
        
        for dir_path in possible_dirs:
            if dir_path and os.path.exists(dir_path):
                # Check if it has mouth shape images (try multiple naming patterns)
                test_files = [
                    "A.png", "mouth_A.png", "lisa-A.png", 
                    "character-A.png", "avatar-A.png"
                ]
                for test_file in test_files:
                    if os.path.exists(os.path.join(dir_path, test_file)):
                        print(f"✅ Found sprites directory: {dir_path}")
                        return dir_path
        
        return None
    
    def _load_sprites(self) -> Dict[str, Image.Image]:
        """Load mouth shape sprite images"""
        sprites = {}
        
        if not self.sprites_dir:
            return sprites
        
        # Try different naming conventions
        for shape in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'X']:
            possible_names = [
                f"{shape}.png",
                f"mouth_{shape}.png",
                f"mouth-{shape}.png",
                f"{shape.lower()}.png",
                f"lisa-{shape}.png",  # Lisa character sprites
                f"character-{shape}.png",
                f"avatar-{shape}.png",
            ]
            
            for name in possible_names:
                sprite_path = os.path.join(self.sprites_dir, name)
                if os.path.exists(sprite_path):
                    try:
                        img = Image.open(sprite_path).convert('RGBA')
                        sprites[shape] = img
                        print(f"  ✅ Loaded sprite: {shape} ({name})")
                        break
                    except Exception as e:
                        print(f"  ⚠️ Failed to load {name}: {e}")
        
        return sprites
    
    def generate_animation(self, audio_path: str, word: str, output_path: str, language: str = "en") -> str:
        """
        Generate lip sync animation using Rhubarb and sprite images
        
        Args:
            audio_path: Path to audio file
            word: Word being spoken
            output_path: Output video path
            language: Language code
        """
        print(f"\n{'='*70}")
        print(f"🎬 GENERATING RHUBARB ANIMATION WITH SPRITES")
        print(f"{'='*70}")
        print(f"Word: {word}")
        print(f"Audio: {audio_path}")
        print(f"Sprites: {len(self.sprites)} loaded")
        
        # Run Rhubarb to get timing
        try:
            lip_sync_data = self._run_rhubarb(audio_path, word)
        except Exception as e:
            print(f"⚠️ Rhubarb failed: {e}, using fallback")
            lip_sync_data = self._create_fallback_timing(word)
        
        # Generate frames
        frames = self._generate_frames(lip_sync_data, word)
        
        print(f"Generated {len(frames)} frames ({len(frames)/self.fps:.2f}s)")
        
        # Encode video
        self._encode_video(frames, audio_path, output_path)
        
        return output_path
    
    def _run_rhubarb(self, audio_path: str, dialog: str) -> Dict:
        """Run Rhubarb to get timing data"""
        if not self.rhubarb_available:
            raise RuntimeError("Rhubarb not available")
        
        # Convert MP3 to WAV if needed (Rhubarb only supports WAV/OGG)
        if audio_path.endswith('.mp3'):
            wav_path = audio_path.replace('.mp3', '.wav')
            print(f"🔄 Converting MP3 to WAV for Rhubarb...")
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_mp3(audio_path)
                audio.export(wav_path, format='wav')
                audio_path = wav_path
                print(f"✅ Converted to: {wav_path}")
            except Exception as e:
                print(f"⚠️ Conversion failed: {e}, trying direct...")
        
        output_json = audio_path.replace(Path(audio_path).suffix, "_rhubarb.json")
        
        cmd = [self.rhubarb_path, "-f", "json", audio_path, "-o", output_json]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise RuntimeError(f"Rhubarb failed: {result.stderr}")
        
        with open(output_json, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Rhubarb analysis: {data['metadata']['duration']:.2f}s, {len(data['mouthCues'])} cues")
        
        return data
    
    def _generate_frames(self, lip_sync_data: Dict, word: str) -> List[Image.Image]:
        """Generate video frames from Rhubarb data"""
        mouth_cues = lip_sync_data['mouthCues']
        duration = lip_sync_data['metadata']['duration']
        total_frames = int(duration * self.fps)
        
        frames = []
        
        for frame_idx in range(total_frames):
            time_sec = frame_idx / self.fps
            
            # Find mouth shape for this time
            mouth_shape = 'A'
            for cue in mouth_cues:
                if cue['start'] <= time_sec < cue['end']:
                    mouth_shape = cue['value']
                    break
            
            # Create frame
            if self.sprites and mouth_shape in self.sprites:
                frame = self._create_frame_with_sprite(mouth_shape, word, time_sec)
            else:
                frame = self._create_frame_generated(mouth_shape, word, time_sec)
            
            frames.append(frame)
        
        return frames
    
    def _create_frame_with_sprite(self, mouth_shape: str, word: str, time_sec: float) -> Image.Image:
        """Create frame using sprite image"""
        # Create background
        img = Image.new('RGB', (self.width, self.height), color=(240, 240, 250))
        
        # Get sprite
        sprite = self.sprites[mouth_shape]
        
        # Resize sprite to fit nicely
        sprite_width = int(self.width * 0.6)
        sprite_height = int(sprite.height * (sprite_width / sprite.width))
        sprite_resized = sprite.resize((sprite_width, sprite_height), Image.Resampling.LANCZOS)
        
        # Center sprite
        x = (self.width - sprite_width) // 2
        y = (self.height - sprite_height) // 2
        
        # Paste sprite (with alpha channel)
        img.paste(sprite_resized, (x, y), sprite_resized)
        
        # Add labels
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("arial.ttf", 32)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Word at top
        word_text = f'"{word.upper()}"'
        bbox = draw.textbbox((0, 0), word_text, font=font_large)
        text_width = bbox[2] - bbox[0]
        draw.text((self.width//2 - text_width//2, 30), word_text, fill=(50, 50, 50), font=font_large)
        
        # Shape label at bottom
        label = f"Rhubarb Shape: {mouth_shape} | Time: {time_sec:.2f}s"
        bbox = draw.textbbox((0, 0), label, font=font_small)
        text_width = bbox[2] - bbox[0]
        draw.text((self.width//2 - text_width//2, self.height - 40), label, fill=(100, 100, 100), font=font_small)
        
        return img
    
    def _create_frame_generated(self, mouth_shape: str, word: str, time_sec: float) -> Image.Image:
        """Fallback: create frame with generated graphics"""
        # Use the enhanced avatar from real_rhubarb_integration
        from .real_rhubarb_integration import RealRhubarbLipSync
        generator = RealRhubarbLipSync(width=self.width, height=self.height, fps=self.fps)
        return generator._create_professional_frame(mouth_shape, word, time_sec)
    
    def _encode_video(self, frames: List[Image.Image], audio_path: str, output_path: str):
        """Encode frames to video with audio"""
        try:
            from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
            from moviepy.audio.io.AudioFileClip import AudioFileClip
            
            frame_arrays = [np.array(frame) for frame in frames]
            clip = ImageSequenceClip(frame_arrays, fps=self.fps)
            
            # Add audio if available
            audio_clip = None
            if audio_path and os.path.exists(audio_path):
                try:
                    audio_clip = AudioFileClip(audio_path)
                    clip.audio = audio_clip
                    print(f"✅ Audio track added")
                except Exception as e:
                    print(f"⚠️ Could not add audio: {e}")
            
            print(f"\n📹 Encoding video...")
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac' if audio_clip else None,
                preset='ultrafast',
                ffmpeg_params=['-pix_fmt', 'yuv420p'],
                logger=None
            )
            
            # Close clips
            clip.close()
            if audio_path and os.path.exists(audio_path):
                try:
                    audio_clip.close()
                except:
                    pass
            
            print(f"\n✅ Video saved: {output_path}")
            print(f"✅ Using: {'Sprite images' if self.sprites else 'Generated graphics'}")
            print(f"✅ Audio: {'Embedded' if (audio_path and os.path.exists(audio_path)) else 'None'}")
            print(f"{'='*70}\n")
            
        except ImportError:
            raise RuntimeError("moviepy not installed")
    
    def _create_fallback_timing(self, word: str) -> Dict:
        """Create fallback timing"""
        duration = len(word) * 0.2
        return {
            'metadata': {'duration': duration},
            'mouthCues': [{'start': 0.0, 'end': duration, 'value': 'A'}]
        }


# Singleton
_instance = None

def get_rhubarb_with_sprites():
    global _instance
    if _instance is None:
        _instance = RhubarbWithSprites()
    return _instance
