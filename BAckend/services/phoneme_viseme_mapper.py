"""
Phoneme and Viseme Mapping Service
Maps words to phonemes and visemes for lip animation exercises
Supports English, Hindi, and Kannada
"""

from typing import List, Dict, Tuple
import re


class PhonemeVisemeMapper:
    """Maps words to phonemes and corresponding visemes for lip animation"""
    
    # Viseme types based on mouth shapes (Disney/Preston Blair classification)
    VISEME_SHAPES = {
        'silence': 0,      # Mouth closed
        'PP': 1,           # P, B, M - lips together
        'FF': 2,           # F, V - lower lip to upper teeth
        'TH': 3,           # TH - tongue between teeth
        'DD': 4,           # T, D, S, Z - tongue to roof
        'kk': 5,           # K, G - back of tongue up
        'CH': 6,           # CH, J, SH - lips forward
        'SS': 7,           # S, Z - teeth together
        'nn': 8,           # N, NG - tongue to roof, mouth open
        'RR': 9,           # R - tongue curled
        'aa': 10,          # AA - mouth wide open
        'E': 11,           # E, I - slight smile
        'I': 12,           # I - narrow mouth
        'O': 13,           # O - mouth rounded
        'U': 14,           # U - lips pursed
        'WQ': 15,          # W, Q - lips forward rounded
        'L': 16,           # L - tongue to roof, mouth open
        'FV': 17,          # F, V - teeth on lower lip
    }
    
    # English phoneme to viseme mapping (IPA-based)
    ENGLISH_PHONEME_VISEME = {
        # Consonants
        'p': 'PP', 'b': 'PP', 'm': 'PP',
        'f': 'FF', 'v': 'FV',
        'θ': 'TH', 'ð': 'TH',  # th sounds
        't': 'DD', 'd': 'DD', 's': 'SS', 'z': 'SS', 'n': 'nn',
        'k': 'kk', 'g': 'kk', 'ŋ': 'nn',  # ng sound
        'tʃ': 'CH', 'dʒ': 'CH', 'ʃ': 'CH', 'ʒ': 'CH',  # ch, j, sh sounds
        'r': 'RR', 'l': 'L',
        'w': 'WQ', 'j': 'I',  # y sound
        'h': 'silence',
        
        # Vowels
        'æ': 'aa', 'ɑ': 'aa', 'ʌ': 'aa',  # a sounds
        'e': 'E', 'ɛ': 'E', 'eɪ': 'E',
        'i': 'I', 'ɪ': 'I', 'iː': 'I',
        'o': 'O', 'ɔ': 'O', 'oʊ': 'O',
        'u': 'U', 'ʊ': 'U', 'uː': 'U',
        'ə': 'E',  # schwa
        'aɪ': 'aa', 'aʊ': 'aa', 'ɔɪ': 'O',
    }
    
    # Hindi phoneme to viseme mapping (Devanagari romanized)
    HINDI_PHONEME_VISEME = {
        # Consonants
        'k': 'kk', 'kh': 'kk', 'g': 'kk', 'gh': 'kk',
        'ch': 'CH', 'chh': 'CH', 'j': 'CH', 'jh': 'CH',
        't': 'DD', 'th': 'DD', 'd': 'DD', 'dh': 'DD',
        'ṭ': 'DD', 'ṭh': 'DD', 'ḍ': 'DD', 'ḍh': 'DD',  # Retroflex
        'p': 'PP', 'ph': 'PP', 'b': 'PP', 'bh': 'PP',
        'n': 'nn', 'ṇ': 'nn', 'ñ': 'nn', 'ṅ': 'nn',
        'm': 'PP',
        'y': 'I', 'r': 'RR', 'l': 'L', 'v': 'FV', 'w': 'WQ',
        'ś': 'CH', 'ṣ': 'SS', 's': 'SS', 'h': 'silence',
        
        # Vowels
        'a': 'aa', 'ā': 'aa', 'i': 'I', 'ī': 'I',
        'u': 'U', 'ū': 'U', 'e': 'E', 'ai': 'E',
        'o': 'O', 'au': 'O',
    }
    
    # Kannada phoneme to viseme mapping
    KANNADA_PHONEME_VISEME = {
        # Consonants
        'k': 'kk', 'kh': 'kk', 'g': 'kk', 'gh': 'kk',
        'c': 'CH', 'ch': 'CH', 'j': 'CH', 'jh': 'CH',
        't': 'DD', 'th': 'DD', 'd': 'DD', 'dh': 'DD',
        'ṭ': 'DD', 'ṭh': 'DD', 'ḍ': 'DD', 'ḍh': 'DD',
        'p': 'PP', 'ph': 'PP', 'b': 'PP', 'bh': 'PP',
        'n': 'nn', 'ṇ': 'nn', 'ñ': 'nn', 'ṅ': 'nn',
        'm': 'PP',
        'y': 'I', 'r': 'RR', 'l': 'L', 'ḷ': 'L', 'v': 'FV', 'w': 'WQ',
        'ś': 'CH', 'ṣ': 'SS', 's': 'SS', 'h': 'silence',
        
        # Vowels
        'a': 'aa', 'ā': 'aa', 'i': 'I', 'ī': 'I',
        'u': 'U', 'ū': 'U', 'e': 'E', 'ē': 'E',
        'ai': 'E', 'o': 'O', 'ō': 'O', 'au': 'O',
    }
    
    # Simple word to phoneme mappings for common words
    ENGLISH_WORD_PHONEMES = {
        'hello': ['h', 'ɛ', 'l', 'oʊ'],
        'water': ['w', 'ɔ', 't', 'ə', 'r'],
        'food': ['f', 'u', 'd'],
        'home': ['h', 'oʊ', 'm'],
        'yes': ['j', 'ɛ', 's'],
        'no': ['n', 'oʊ'],
        'thank': ['θ', 'æ', 'ŋ', 'k'],
        'you': ['j', 'u'],
        'good': ['g', 'ʊ', 'd'],
        'morning': ['m', 'ɔ', 'r', 'n', 'ɪ', 'ŋ'],
        'night': ['n', 'aɪ', 't'],
        'please': ['p', 'l', 'i', 'z'],
        'sorry': ['s', 'ɔ', 'r', 'i'],
        'help': ['h', 'ɛ', 'l', 'p'],
        'love': ['l', 'ʌ', 'v'],
    }
    
    HINDI_WORD_PHONEMES = {
        'नमस्ते': ['n', 'a', 'm', 'a', 's', 't', 'e'],  # namaste
        'धन्यवाद': ['dh', 'a', 'n', 'y', 'a', 'v', 'ā', 'd'],  # dhanyavaad
        'हाँ': ['h', 'ā', 'ṅ'],  # haan
        'नहीं': ['n', 'a', 'h', 'ī', 'ṅ'],  # nahin
        'पानी': ['p', 'ā', 'n', 'ī'],  # paani
        'खाना': ['kh', 'ā', 'n', 'ā'],  # khaana
        'घर': ['gh', 'a', 'r'],  # ghar
        'अच्छा': ['a', 'ch', 'ch', 'ā'],  # accha
        'बुरा': ['b', 'u', 'r', 'ā'],  # bura
    }
    
    KANNADA_WORD_PHONEMES = {
        'ನಮಸ್ಕಾರ': ['n', 'a', 'm', 'a', 's', 'k', 'ā', 'r'],  # namaskara
        'ಧನ್ಯವಾದ': ['dh', 'a', 'n', 'y', 'a', 'v', 'ā', 'd'],  # dhanyavaada
        'ಹೌದು': ['h', 'au', 'd', 'u'],  # haudu
        'ಇಲ್ಲ': ['i', 'l', 'l', 'a'],  # illa
        'ನೀರು': ['n', 'ī', 'r', 'u'],  # neeru
        'ಅನ್ನ': ['a', 'n', 'n', 'a'],  # anna
        'ಮನೆ': ['m', 'a', 'n', 'e'],  # mane
        'ಒಳ್ಳೆಯದು': ['o', 'ḷ', 'ḷ', 'e', 'y', 'a', 'd', 'u'],  # olleyadu
    }
    
    def __init__(self):
        """Initialize the phoneme-viseme mapper"""
        pass
    
    def word_to_phonemes(self, word: str, language: str = 'en') -> List[str]:
        """
        Convert a word to its phoneme sequence
        
        Args:
            word: The word to convert
            language: Language code ('en', 'hi', 'kn')
            
        Returns:
            List of phonemes
        """
        word_lower = word.lower().strip()
        
        # Check predefined mappings first
        if language == 'en':
            if word_lower in self.ENGLISH_WORD_PHONEMES:
                return self.ENGLISH_WORD_PHONEMES[word_lower]
            # Fallback: simple letter-based approximation
            return self._approximate_english_phonemes(word_lower)
        
        elif language == 'hi':
            if word in self.HINDI_WORD_PHONEMES:
                return self.HINDI_WORD_PHONEMES[word]
            # Fallback: romanized approximation
            return self._approximate_hindi_phonemes(word)
        
        elif language == 'kn':
            if word in self.KANNADA_WORD_PHONEMES:
                return self.KANNADA_WORD_PHONEMES[word]
            # Fallback: romanized approximation
            return self._approximate_kannada_phonemes(word)
        
        return list(word_lower)  # Ultimate fallback
    
    def _approximate_english_phonemes(self, word: str) -> List[str]:
        """Approximate English phonemes from spelling"""
        phonemes = []
        i = 0
        while i < len(word):
            # Check for digraphs
            if i < len(word) - 1:
                digraph = word[i:i+2]
                if digraph == 'th':
                    phonemes.append('θ')
                    i += 2
                    continue
                elif digraph == 'sh':
                    phonemes.append('ʃ')
                    i += 2
                    continue
                elif digraph == 'ch':
                    phonemes.append('tʃ')
                    i += 2
                    continue
                elif digraph == 'ng':
                    phonemes.append('ŋ')
                    i += 2
                    continue
            
            # Single letters
            char = word[i]
            if char in 'aeiou':
                phonemes.append(char)
            elif char in self.ENGLISH_PHONEME_VISEME:
                phonemes.append(char)
            else:
                # Map to closest phoneme
                phoneme_map = {
                    'c': 'k', 'q': 'k', 'x': 'k',
                    'ph': 'f', 'gh': 'g'
                }
                phonemes.append(phoneme_map.get(char, char))
            
            i += 1
        
        return phonemes
    
    def _approximate_hindi_phonemes(self, word: str) -> List[str]:
        """Approximate Hindi phonemes from Devanagari or romanized text"""
        # Simple character-based approximation
        # In production, use a proper Hindi phonetic analyzer
        return list(word)
    
    def _approximate_kannada_phonemes(self, word: str) -> List[str]:
        """Approximate Kannada phonemes from Kannada script or romanized text"""
        # Simple character-based approximation
        # In production, use a proper Kannada phonetic analyzer
        return list(word)
    
    def phonemes_to_visemes(self, phonemes: List[str], language: str = 'en') -> List[Dict]:
        """
        Convert phonemes to visemes with timing information
        
        Args:
            phonemes: List of phonemes
            language: Language code
            
        Returns:
            List of viseme dictionaries with shape, duration, and timing
        """
        viseme_map = {
            'en': self.ENGLISH_PHONEME_VISEME,
            'hi': self.HINDI_PHONEME_VISEME,
            'kn': self.KANNADA_PHONEME_VISEME
        }.get(language, self.ENGLISH_PHONEME_VISEME)
        
        visemes = []
        total_duration = 0
        
        for i, phoneme in enumerate(phonemes):
            # Get viseme shape
            viseme_shape = viseme_map.get(phoneme, 'silence')
            
            # Estimate duration (in milliseconds)
            # Vowels are typically longer than consonants
            if phoneme in 'aeiouāīūēō':
                duration = 150  # ms
            else:
                duration = 100  # ms
            
            visemes.append({
                'phoneme': phoneme,
                'viseme': viseme_shape,
                'viseme_id': self.VISEME_SHAPES.get(viseme_shape, 0),
                'start_time': total_duration,
                'duration': duration,
                'end_time': total_duration + duration
            })
            
            total_duration += duration
        
        return visemes
    
    def word_to_visemes(self, word: str, language: str = 'en') -> Dict:
        """
        Complete pipeline: word -> phonemes -> visemes
        
        Args:
            word: The word to analyze
            language: Language code
            
        Returns:
            Dictionary with phonemes, visemes, and metadata
        """
        phonemes = self.word_to_phonemes(word, language)
        visemes = self.phonemes_to_visemes(phonemes, language)
        
        return {
            'word': word,
            'language': language,
            'phonemes': phonemes,
            'visemes': visemes,
            'total_duration': sum(v['duration'] for v in visemes),
            'phoneme_count': len(phonemes),
            'viseme_count': len(visemes)
        }
    
    def get_viseme_description(self, viseme_shape: str) -> str:
        """Get human-readable description of a viseme shape"""
        descriptions = {
            'silence': 'Mouth closed, relaxed',
            'PP': 'Lips pressed together (P, B, M)',
            'FF': 'Lower lip touches upper teeth (F, V)',
            'TH': 'Tongue between teeth (TH)',
            'DD': 'Tongue touches roof of mouth (T, D)',
            'kk': 'Back of tongue raised (K, G)',
            'CH': 'Lips pushed forward (CH, SH)',
            'SS': 'Teeth together, slight opening (S, Z)',
            'nn': 'Tongue to roof, mouth open (N)',
            'RR': 'Tongue curled back (R)',
            'aa': 'Mouth wide open (AH)',
            'E': 'Slight smile, teeth visible (E)',
            'I': 'Narrow mouth opening (I)',
            'O': 'Mouth rounded (O)',
            'U': 'Lips pursed forward (U)',
            'WQ': 'Lips rounded and forward (W)',
            'L': 'Tongue to roof, mouth open (L)',
            'FV': 'Teeth on lower lip (F, V)',
        }
        return descriptions.get(viseme_shape, 'Unknown mouth shape')


# Singleton instance
_mapper_instance = None

def get_phoneme_viseme_mapper() -> PhonemeVisemeMapper:
    """Get singleton instance of PhonemeVisemeMapper"""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = PhonemeVisemeMapper()
    return _mapper_instance
