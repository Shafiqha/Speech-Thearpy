"""
Mouth Tracking and Analysis Service
Analyzes user's mouth movements from video/webcam feed
Compares with target visemes and provides feedback
Uses MediaPipe for facial landmark detection
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import tempfile
from pathlib import Path

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("⚠️ MediaPipe not available. Install with: pip install mediapipe")

from .phoneme_viseme_mapper import get_phoneme_viseme_mapper


class MouthTrackingAnalyzer:
    """Analyzes mouth movements and lip sync from video"""
    
    # MediaPipe face mesh landmark indices for mouth
    MOUTH_LANDMARKS = {
        'outer_lip': [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88],
        'inner_lip': [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95],
        'upper_lip': [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291],
        'lower_lip': [146, 91, 181, 84, 17, 314, 405, 321, 375, 291],
    }
    
    def __init__(self):
        """Initialize mouth tracking analyzer"""
        self.mapper = get_phoneme_viseme_mapper()
        
        if MEDIAPIPE_AVAILABLE:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        else:
            self.mp_face_mesh = None
            self.face_mesh = None
    
    def extract_mouth_features(self, landmarks, image_shape: Tuple[int, int]) -> Dict:
        """
        Extract mouth features from facial landmarks
        
        Args:
            landmarks: MediaPipe facial landmarks
            image_shape: (height, width) of image
            
        Returns:
            Dictionary of mouth features
        """
        if not landmarks:
            return None
        
        height, width = image_shape
        
        # Extract mouth landmark coordinates
        mouth_points = []
        for idx in self.MOUTH_LANDMARKS['outer_lip']:
            landmark = landmarks.landmark[idx]
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            mouth_points.append((x, y))
        
        mouth_points = np.array(mouth_points)
        
        # Calculate mouth features
        features = {}
        
        # 1. Mouth width (horizontal distance)
        left_corner = mouth_points[0]
        right_corner = mouth_points[10]
        features['width'] = np.linalg.norm(right_corner - left_corner)
        
        # 2. Mouth height (vertical distance)
        upper_center = mouth_points[5]
        lower_center = mouth_points[15]
        features['height'] = np.linalg.norm(lower_center - upper_center)
        
        # 3. Mouth aspect ratio
        features['aspect_ratio'] = features['height'] / (features['width'] + 1e-6)
        
        # 4. Mouth area
        features['area'] = cv2.contourArea(mouth_points)
        
        # 5. Lip rounding (circularity)
        perimeter = cv2.arcLength(mouth_points, True)
        features['circularity'] = 4 * np.pi * features['area'] / (perimeter ** 2 + 1e-6)
        
        # 6. Upper lip protrusion
        features['upper_lip_y'] = upper_center[1]
        
        # 7. Lower lip protrusion
        features['lower_lip_y'] = lower_center[1]
        
        # 8. Mouth center
        features['center_x'] = int(mouth_points[:, 0].mean())
        features['center_y'] = int(mouth_points[:, 1].mean())
        
        # 9. Mouth openness (normalized)
        features['openness'] = min(features['aspect_ratio'] * 10, 1.0)
        
        return features
    
    def classify_viseme_from_features(self, features: Dict) -> str:
        """
        Classify viseme from mouth features
        
        Args:
            features: Mouth feature dictionary
            
        Returns:
            Predicted viseme shape
        """
        if not features:
            return 'silence'
        
        aspect_ratio = features['aspect_ratio']
        circularity = features['circularity']
        openness = features['openness']
        
        # Rule-based classification (simplified)
        # In production, use a trained ML model
        
        # Closed mouth
        if openness < 0.15:
            return 'PP'  # or 'silence'
        
        # Wide open mouth
        elif openness > 0.6:
            return 'aa'
        
        # Rounded mouth
        elif circularity > 0.7:
            if openness > 0.4:
                return 'O'
            else:
                return 'U'
        
        # Narrow opening
        elif aspect_ratio < 0.3:
            return 'I'
        
        # Medium opening with smile
        elif aspect_ratio < 0.4:
            return 'E'
        
        # Default to neutral
        else:
            return 'E'
    
    def analyze_video_frame(self, frame: np.ndarray) -> Dict:
        """
        Analyze a single video frame for mouth tracking
        
        Args:
            frame: Video frame (BGR format)
            
        Returns:
            Analysis results with landmarks and features
        """
        if not MEDIAPIPE_AVAILABLE or self.face_mesh is None:
            return {
                'success': False,
                'error': 'MediaPipe not available',
                'features': None,
                'viseme': 'silence'
            }
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return {
                'success': False,
                'error': 'No face detected',
                'features': None,
                'viseme': 'silence'
            }
        
        # Get first face
        face_landmarks = results.multi_face_landmarks[0]
        
        # Extract mouth features
        features = self.extract_mouth_features(face_landmarks, frame.shape[:2])
        
        # Classify viseme
        viseme = self.classify_viseme_from_features(features)
        
        return {
            'success': True,
            'features': features,
            'viseme': viseme,
            'landmarks': face_landmarks
        }
    
    def analyze_video_file(self, video_path: str, target_visemes: List[Dict] = None) -> Dict:
        """
        Analyze entire video file for mouth tracking
        
        Args:
            video_path: Path to video file
            target_visemes: Expected viseme sequence (optional)
            
        Returns:
            Complete analysis with frame-by-frame tracking
        """
        if not MEDIAPIPE_AVAILABLE:
            return {
                'success': False,
                'error': 'MediaPipe not available'
            }
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return {
                'success': False,
                'error': f'Could not open video: {video_path}'
            }
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_analyses = []
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Analyze frame
            analysis = self.analyze_video_frame(frame)
            analysis['frame_number'] = frame_idx
            analysis['timestamp_ms'] = (frame_idx / fps) * 1000 if fps > 0 else 0
            
            frame_analyses.append(analysis)
            frame_idx += 1
        
        cap.release()
        
        # Calculate overall statistics
        detected_visemes = [a['viseme'] for a in frame_analyses if a['success']]
        
        result = {
            'success': True,
            'total_frames': total_frames,
            'analyzed_frames': len(frame_analyses),
            'fps': fps,
            'duration_ms': (total_frames / fps) * 1000 if fps > 0 else 0,
            'frame_analyses': frame_analyses,
            'detected_visemes': detected_visemes,
            'viseme_sequence': self._extract_viseme_sequence(frame_analyses),
        }
        
        # Compare with target if provided
        if target_visemes:
            result['comparison'] = self.compare_with_target(
                result['viseme_sequence'], 
                target_visemes
            )
        
        return result
    
    def _extract_viseme_sequence(self, frame_analyses: List[Dict]) -> List[Dict]:
        """Extract distinct viseme sequence from frame analyses"""
        if not frame_analyses:
            return []
        
        sequence = []
        current_viseme = None
        start_frame = 0
        
        for i, analysis in enumerate(frame_analyses):
            if not analysis['success']:
                continue
            
            viseme = analysis['viseme']
            
            if viseme != current_viseme:
                if current_viseme is not None:
                    sequence.append({
                        'viseme': current_viseme,
                        'start_frame': start_frame,
                        'end_frame': i - 1,
                        'start_time': frame_analyses[start_frame].get('timestamp_ms', 0),
                        'end_time': analysis.get('timestamp_ms', 0),
                        'duration': analysis.get('timestamp_ms', 0) - frame_analyses[start_frame].get('timestamp_ms', 0)
                    })
                
                current_viseme = viseme
                start_frame = i
        
        # Add last viseme
        if current_viseme is not None:
            sequence.append({
                'viseme': current_viseme,
                'start_frame': start_frame,
                'end_frame': len(frame_analyses) - 1,
                'start_time': frame_analyses[start_frame].get('timestamp_ms', 0),
                'end_time': frame_analyses[-1].get('timestamp_ms', 0),
                'duration': frame_analyses[-1].get('timestamp_ms', 0) - frame_analyses[start_frame].get('timestamp_ms', 0)
            })
        
        return sequence
    
    def compare_with_target(self, detected_sequence: List[Dict], 
                           target_visemes: List[Dict]) -> Dict:
        """
        Compare detected viseme sequence with target
        
        Args:
            detected_sequence: Detected viseme sequence
            target_visemes: Target viseme sequence
            
        Returns:
            Comparison results with accuracy and errors
        """
        if not detected_sequence or not target_visemes:
            return {
                'accuracy': 0.0,
                'lip_sync_score': 0.0,
                'errors': ['No visemes detected or no target provided']
            }
        
        # Extract just the viseme types
        detected_visemes = [v['viseme'] for v in detected_sequence]
        target_viseme_types = [v['viseme'] for v in target_visemes]
        
        # Calculate accuracy (simple matching)
        matches = 0
        total = min(len(detected_visemes), len(target_viseme_types))
        
        for i in range(total):
            if detected_visemes[i] == target_viseme_types[i]:
                matches += 1
        
        accuracy = (matches / len(target_viseme_types)) * 100 if target_viseme_types else 0
        
        # Calculate lip sync score (timing-based)
        timing_errors = []
        for i, target in enumerate(target_visemes):
            if i < len(detected_sequence):
                detected = detected_sequence[i]
                timing_diff = abs(detected['duration'] - target['duration'])
                timing_errors.append(timing_diff)
        
        avg_timing_error = np.mean(timing_errors) if timing_errors else 0
        lip_sync_score = max(0, 100 - (avg_timing_error / 10))  # Normalize
        
        # Identify specific errors
        errors = []
        for i, target in enumerate(target_viseme_types):
            if i >= len(detected_visemes):
                errors.append(f"Missing viseme '{target}' at position {i}")
            elif detected_visemes[i] != target:
                errors.append(f"Expected '{target}' but got '{detected_visemes[i]}' at position {i}")
        
        return {
            'accuracy': accuracy,
            'lip_sync_score': lip_sync_score,
            'matches': matches,
            'total_target': len(target_viseme_types),
            'total_detected': len(detected_visemes),
            'errors': errors,
            'timing_errors': timing_errors,
            'avg_timing_error_ms': avg_timing_error
        }
    
    def generate_feedback(self, comparison: Dict, language: str = 'en') -> str:
        """
        Generate human-readable feedback from comparison results
        
        Args:
            comparison: Comparison results
            language: Language for feedback
            
        Returns:
            Feedback text
        """
        accuracy = comparison.get('accuracy', 0)
        lip_sync = comparison.get('lip_sync_score', 0)
        errors = comparison.get('errors', [])
        
        feedback_parts = []
        
        # Overall assessment
        if accuracy >= 90:
            feedback_parts.append("Excellent pronunciation! Your lip movements match the target very well.")
        elif accuracy >= 70:
            feedback_parts.append("Good job! Your pronunciation is mostly correct with minor improvements needed.")
        elif accuracy >= 50:
            feedback_parts.append("Fair attempt. Keep practicing to improve your lip movements.")
        else:
            feedback_parts.append("Keep practicing. Focus on matching the mouth shapes shown in the video.")
        
        # Lip sync feedback
        if lip_sync >= 80:
            feedback_parts.append("Your timing is excellent!")
        elif lip_sync >= 60:
            feedback_parts.append("Try to match the timing of the mouth movements more closely.")
        else:
            feedback_parts.append("Focus on the speed and duration of each mouth shape.")
        
        # Specific errors (limit to top 3)
        if errors:
            feedback_parts.append("\nSpecific areas to improve:")
            for error in errors[:3]:
                feedback_parts.append(f"• {error}")
        
        return "\n".join(feedback_parts)
    
    def draw_mouth_overlay(self, frame: np.ndarray, landmarks) -> np.ndarray:
        """Draw mouth landmarks overlay on frame"""
        if not landmarks:
            return frame
        
        height, width = frame.shape[:2]
        
        # Draw mouth contour
        mouth_points = []
        for idx in self.MOUTH_LANDMARKS['outer_lip']:
            landmark = landmarks.landmark[idx]
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            mouth_points.append((x, y))
        
        mouth_points = np.array(mouth_points, np.int32)
        cv2.polylines(frame, [mouth_points], True, (0, 255, 0), 2)
        
        return frame


# Singleton instance
_analyzer_instance = None

def get_mouth_tracking_analyzer() -> MouthTrackingAnalyzer:
    """Get singleton instance of MouthTrackingAnalyzer"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = MouthTrackingAnalyzer()
    return _analyzer_instance
