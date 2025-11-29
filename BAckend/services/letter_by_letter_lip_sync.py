"""
Letter-by-Letter Lip Sync Service
For detailed phoneme-by-phoneme practice
"""

from .true_audio_lip_mapping import TrueAudioLipMapping
from typing import Dict, List


class LetterByLetterLipSync(TrueAudioLipMapping):
    """
    Letter-by-letter lip sync for detailed practice
    """
    
    def __init__(self):
        """Initialize letter-by-letter service"""
        super().__init__()
        print(f"✅ Letter-by-Letter Lip Sync initialized")
    
    def generate_letter_by_letter(
        self,
        audio_path: str,
        text: str,
        language: str = 'en'
    ) -> Dict:
        """
        Generate letter-by-letter lip sync
        
        Args:
            audio_path: Path to audio file
            text: Text to analyze
            language: Language code
            
        Returns:
            Lip sync data with detailed timing
        """
        # Use parent's audio-to-lip mapping
        result = self.map_audio_to_lips(audio_path, text, language)
        
        if result:
            # Add letter-by-letter metadata
            result['mode'] = 'letter_by_letter'
            result['text'] = text
            result['letters'] = list(text)
        
        return result


# Singleton
_letter_service_instance = None

def get_letter_by_letter_service():
    """Get singleton instance"""
    global _letter_service_instance
    if _letter_service_instance is None:
        _letter_service_instance = LetterByLetterLipSync()
    return _letter_service_instance
