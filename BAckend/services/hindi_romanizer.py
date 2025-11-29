"""
Hindi Romanization Service
Converts Hindi Devanagari script to romanized text for accurate lip sync
This helps Rhubarb's phonetic recognizer understand Hindi pronunciation
"""

import re
from typing import Dict, List


class HindiRomanizer:
    """
    Romanizes Hindi text for accurate phonetic lip sync
    Maps Devanagari characters to their pronunciation in Roman script
    """
    
    def __init__(self):
        """Initialize Hindi to Roman mapping"""
        
        # Vowels (स्वर)
        self.vowels = {
            'अ': 'a',
            'आ': 'aa',
            'इ': 'i',
            'ई': 'ee',
            'उ': 'u',
            'ऊ': 'oo',
            'ऋ': 'ri',
            'ॠ': 'ree',
            'ऌ': 'lri',
            'ॡ': 'lree',
            'ए': 'e',
            'ऐ': 'ai',
            'ओ': 'o',
            'औ': 'au'
        }
        
        # Consonants (व्यंजन)
        self.consonants = {
            'क': 'ka', 'ख': 'kha', 'ग': 'ga', 'घ': 'gha', 'ङ': 'nga',
            'च': 'cha', 'छ': 'chha', 'ज': 'ja', 'झ': 'jha', 'ञ': 'nya',
            'ट': 'ta', 'ठ': 'tha', 'ड': 'da', 'ढ': 'dha', 'ण': 'na',
            'त': 'tha', 'थ': 'thha', 'द': 'dha', 'ध': 'dhha', 'न': 'na',
            'प': 'pa', 'फ': 'pha', 'ब': 'ba', 'भ': 'bha', 'म': 'ma',
            'य': 'ya', 'र': 'ra', 'ल': 'la', 'व': 'va',
            'श': 'sha', 'ष': 'shha', 'स': 'sa', 'ह': 'ha',
            'क़': 'qa', 'ख़': 'kha', 'ग़': 'gha', 'ज़': 'za',
            'ड़': 'da', 'ढ़': 'dha', 'फ़': 'fa', 'य़': 'ya',
            'ऱ': 'ra', 'ळ': 'la', 'ऴ': 'zha'
        }
        
        # Vowel signs (मात्राएँ)
        self.vowel_signs = {
            'ा': 'aa',
            'ि': 'i',
            'ी': 'ee',
            'ु': 'u',
            'ू': 'oo',
            'ृ': 'ri',
            'ॄ': 'ree',
            'ॢ': 'lri',
            'ॣ': 'lree',
            'े': 'e',
            'ै': 'ai',
            'ो': 'o',
            'ौ': 'au',
            '्': ''  # Virama (halant) - removes inherent vowel
        }
        
        # Special characters
        self.special = {
            'ं': 'm',  # Anusvara
            'ः': 'h',  # Visarga
            'ँ': 'n',  # Chandrabindu
            '़': '',   # Nukta
            'ॐ': 'om',
            '।': '.',
            '॥': '..'
        }
        
        print("✅ Hindi Romanizer initialized")
        print("   Vowels: 14 | Consonants: 36 | Signs: 13")
    
    def romanize(self, hindi_text: str) -> str:
        """
        Convert Hindi text to romanized pronunciation
        
        Args:
            hindi_text: Devanagari script text
            
        Returns:
            Romanized text for phonetic recognition
        """
        if not hindi_text:
            return ""
        
        romanized = []
        i = 0
        text = hindi_text.strip()
        
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
                        if next_char == '्':  # Virama - remove inherent 'a'
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
    
    def romanize_with_mapping(self, hindi_text: str) -> Dict:
        """
        Romanize with detailed character mapping
        
        Args:
            hindi_text: Devanagari script text
            
        Returns:
            Dict with romanized text and character mappings
        """
        romanized = self.romanize(hindi_text)
        
        return {
            'original': hindi_text,
            'romanized': romanized,
            'length_original': len(hindi_text),
            'length_romanized': len(romanized),
            'mapping': self._create_mapping(hindi_text, romanized)
        }
    
    def _create_mapping(self, original: str, romanized: str) -> List[Dict]:
        """Create character-by-character mapping"""
        mappings = []
        
        for i, char in enumerate(original):
            if char in self.vowels:
                mappings.append({
                    'hindi': char,
                    'roman': self.vowels[char],
                    'type': 'vowel'
                })
            elif char in self.consonants:
                mappings.append({
                    'hindi': char,
                    'roman': self.consonants[char],
                    'type': 'consonant'
                })
            elif char in self.vowel_signs:
                mappings.append({
                    'hindi': char,
                    'roman': self.vowel_signs[char],
                    'type': 'vowel_sign'
                })
            elif char in self.special:
                mappings.append({
                    'hindi': char,
                    'roman': self.special[char],
                    'type': 'special'
                })
        
        return mappings


# Singleton instance
_romanizer_instance = None

def get_hindi_romanizer():
    """Get singleton instance of Hindi romanizer"""
    global _romanizer_instance
    if _romanizer_instance is None:
        _romanizer_instance = HindiRomanizer()
    return _romanizer_instance


# Test examples
if __name__ == "__main__":
    romanizer = get_hindi_romanizer()
    
    test_words = [
        "नमस्ते",     # namaste
        "धन्यवाद",    # dhanyavaad
        "पानी",      # paanee
        "मदद",       # madad
        "अच्छा"      # achchhaa
    ]
    
    print("\n🔤 Hindi Romanization Tests:")
    print("=" * 50)
    
    for word in test_words:
        result = romanizer.romanize(word)
        print(f"Hindi:      {word}")
        print(f"Romanized:  {result}")
        print("-" * 50)
