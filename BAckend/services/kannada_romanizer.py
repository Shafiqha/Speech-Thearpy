"""
Kannada Romanization Service
Converts Kannada script to romanized text for accurate lip sync
This helps Rhubarb's phonetic recognizer understand Kannada pronunciation
"""

import re
from typing import Dict, List


class KannadaRomanizer:
    """
    Romanizes Kannada text for accurate phonetic lip sync
    Maps Kannada characters to their pronunciation in Roman script
    """
    
    def __init__(self):
        """Initialize Kannada to Roman mapping"""
        
        # Vowels (ಸ್ವರಗಳು)
        self.vowels = {
            'ಅ': 'a',
            'ಆ': 'aa',
            'ಇ': 'i',
            'ಈ': 'ee',
            'ಉ': 'u',
            'ಊ': 'oo',
            'ಋ': 'ru',
            'ೠ': 'ruu',
            'ಎ': 'e',
            'ಏ': 'ae',
            'ಐ': 'ai',
            'ಒ': 'o',
            'ಓ': 'oa',
            'ಔ': 'au'
        }
        
        # Consonants (ವ್ಯಂಜನಗಳು)
        self.consonants = {
            'ಕ': 'ka', 'ಖ': 'kha', 'ಗ': 'ga', 'ಘ': 'gha', 'ಙ': 'nga',
            'ಚ': 'cha', 'ಛ': 'chha', 'ಜ': 'ja', 'ಝ': 'jha', 'ಞ': 'nya',
            'ಟ': 'ta', 'ಠ': 'tha', 'ಡ': 'da', 'ಢ': 'dha', 'ಣ': 'na',
            'ತ': 'tha', 'ಥ': 'thha', 'ದ': 'dha', 'ಧ': 'dhha', 'ನ': 'na',
            'ಪ': 'pa', 'ಫ': 'pha', 'ಬ': 'ba', 'ಭ': 'bha', 'ಮ': 'ma',
            'ಯ': 'ya', 'ರ': 'ra', 'ಲ': 'la', 'ವ': 'va',
            'ಶ': 'sha', 'ಷ': 'shha', 'ಸ': 'sa', 'ಹ': 'ha',
            'ಳ': 'la', 'ೞ': 'zha', 'ಱ': 'rra'
        }
        
        # Vowel signs (ಮಾತ್ರೆಗಳು)
        self.vowel_signs = {
            'ಾ': 'aa',
            'ಿ': 'i',
            'ೀ': 'ee',
            'ು': 'u',
            'ೂ': 'oo',
            'ೃ': 'ru',
            'ೄ': 'ruu',
            'ೆ': 'e',
            'ೇ': 'ae',
            'ೈ': 'ai',
            'ೊ': 'o',
            'ೋ': 'oa',
            'ೌ': 'au',
            '್': ''  # Virama (halant) - removes inherent vowel
        }
        
        # Special characters
        self.special = {
            'ಂ': 'm',  # Anusvara
            'ಃ': 'h',  # Visarga
            '಼': '',   # Nukta
            'ೱ': 'va',
            'ೲ': 'va'
        }
        
        print("✅ Kannada Romanizer initialized")
        print("   Vowels: 14 | Consonants: 34 | Signs: 13")
    
    def romanize(self, kannada_text: str) -> str:
        """
        Convert Kannada text to romanized pronunciation
        
        Args:
            kannada_text: Kannada script text
            
        Returns:
            Romanized text for phonetic recognition
        """
        if not kannada_text:
            return ""
        
        romanized = []
        i = 0
        text = kannada_text.strip()
        
        while i < len(text):
            char = text[i]
            
            # Check for spaces and punctuation
            if char in ' .,!?;:':
                romanized.append(char)
                i += 1
                continue
            
            # Check for vowels
            if char in self.vowels:
                romanized.append(self.vowels[char])
                i += 1
                continue
            
            # Check for consonants
            if char in self.consonants:
                base = self.consonants[char]
                
                # Look ahead for vowel signs or virama
                if i + 1 < len(text):
                    next_char = text[i + 1]
                    
                    if next_char in self.vowel_signs:
                        if next_char == '್':  # Virama - remove inherent 'a'
                            romanized.append(base[:-1] if base.endswith('a') else base)
                        else:
                            # Replace inherent 'a' with vowel sign
                            romanized.append(base[:-1] + self.vowel_signs[next_char])
                        i += 2
                        continue
                    elif next_char in self.special:
                        romanized.append(base + self.special[next_char])
                        i += 2
                        continue
                
                # No vowel sign, use inherent 'a'
                romanized.append(base)
                i += 1
                continue
            
            # Check for special characters
            if char in self.special:
                romanized.append(self.special[char])
                i += 1
                continue
            
            # Unknown character, keep as is
            romanized.append(char)
            i += 1
        
        result = ''.join(romanized)
        return result
    
    def romanize_with_mapping(self, kannada_text: str) -> Dict:
        """
        Romanize with detailed character mapping
        
        Args:
            kannada_text: Kannada script text
            
        Returns:
            Dict with romanized text and character mappings
        """
        romanized = self.romanize(kannada_text)
        
        return {
            'original': kannada_text,
            'romanized': romanized,
            'length_original': len(kannada_text),
            'length_romanized': len(romanized),
            'mapping': self._create_mapping(kannada_text, romanized)
        }
    
    def _create_mapping(self, original: str, romanized: str) -> List[Dict]:
        """Create character-by-character mapping"""
        mappings = []
        
        # Simple mapping for now
        for i, char in enumerate(original):
            if char in self.vowels:
                mappings.append({
                    'kannada': char,
                    'roman': self.vowels[char],
                    'type': 'vowel'
                })
            elif char in self.consonants:
                mappings.append({
                    'kannada': char,
                    'roman': self.consonants[char],
                    'type': 'consonant'
                })
            elif char in self.vowel_signs:
                mappings.append({
                    'kannada': char,
                    'roman': self.vowel_signs[char],
                    'type': 'vowel_sign'
                })
            elif char in self.special:
                mappings.append({
                    'kannada': char,
                    'roman': self.special[char],
                    'type': 'special'
                })
        
        return mappings


# Singleton instance
_romanizer_instance = None

def get_kannada_romanizer():
    """Get singleton instance of Kannada romanizer"""
    global _romanizer_instance
    if _romanizer_instance is None:
        _romanizer_instance = KannadaRomanizer()
    return _romanizer_instance


# Test examples
if __name__ == "__main__":
    romanizer = get_kannada_romanizer()
    
    test_words = [
        "ನಮಸ್ಕಾರ",  # namaskara
        "ಧನ್ಯವಾದ",  # dhanyavaada
        "ನೀರು",     # neeru
        "ಸಹಾಯ",     # sahaaya
        "ಚೆನ್ನಾಗಿದೆ"  # chennaagide
    ]
    
    print("\n🔤 Kannada Romanization Tests:")
    print("=" * 50)
    
    for word in test_words:
        result = romanizer.romanize(word)
        print(f"Kannada:    {word}")
        print(f"Romanized:  {result}")
        print("-" * 50)
