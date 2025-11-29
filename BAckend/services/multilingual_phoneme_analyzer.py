"""
Lightweight Kannada phoneme analyzer used by phoneme_viseme_mapper.
Provides a conservative split of Kannada words into phoneme-like units and
utilities for mapping to visemes and durations. This is not a full phonetic
segmenter but fixes the previous character-split approximation.
"""
from typing import List
from pathlib import Path


class MultilingualPhonemeAnalyzer:
    KANNADA_VOWELS = {
        'ಅ': ['a'], 'ಆ': ['aa'], 'ಇ': ['i'], 'ಈ': ['ii'],
        'ಉ': ['u'], 'ಊ': ['uu'], 'ಋ': ['ru'], 'ಎ': ['e'],
        'ಏ': ['ee'], 'ಐ': ['ai'], 'ಓ': ['oo'], 'ಒ': ['o'], 'ಔ': ['au']
    }

    KANNADA_CONSONANTS = {
        'ಕ': 'ka', 'ಖ': 'kha', 'ಗ': 'ga', 'ಘ': 'gha', 'ಙ': 'nga',
        'ಚ': 'ca', 'ಛ': 'cha', 'ಜ': 'ja', 'ಝ': 'jha', 'ಞ': 'nya',
        'ಟ': 'ta', 'ಠ': 'tha', 'ಡ': 'da', 'ಢ': 'dha', 'ಣ': 'nna',
        'ತ': 'tha2', 'ಥ': 'thha', 'ದ': 'dha2', 'ಧ': 'dhha', 'ನ': 'na',
        'ಪ': 'pa', 'ಫ': 'pha', 'ಬ': 'ba', 'ಭ': 'bha', 'ಮ': 'ma',
        'ಯ': 'ya', 'ರ': 'ra', 'ಲ': 'la', 'ವ': 'va', 'ಳ': 'lla',
        'ಶ': 'sha', 'ಷ': 'ssa', 'ಸ': 'sa', 'ಹ': 'ha'
    }

    KANNADA_VOWEL_SIGNS = {
        'ಾ': 'aa', 'ಿ': 'i', 'ೀ': 'ii', 'ು': 'u', 'ೂ': 'uu',
        'ೃ': 'ru', 'ೆ': 'e', 'ೇ': 'ee', 'ೈ': 'ai', 'ೊ': 'o', 'ೋ': 'oo', 'ೌ': 'au'
    }

    # Conservative viseme mapping for Kannada phoneme tokens
    KANNADA_VISEME_MAP = {
        'ka': 'kk', 'kha': 'kk', 'ga': 'kk', 'gha': 'kk', 'nga': 'nn',
        'ca': 'CH', 'cha': 'CH', 'ja': 'CH', 'jha': 'CH', 'nya': 'nn',
        'ta': 'DD', 'tha': 'DD', 'da': 'DD', 'dha': 'DD', 'nna': 'nn',
        'pa': 'PP', 'pha': 'PP', 'ba': 'PP', 'bha': 'PP', 'ma': 'PP',
        'ya': 'I', 'ra': 'RR', 'la': 'L', 'va': 'FV', 'lla': 'L',
        'sha': 'CH', 'ssa': 'SS', 'sa': 'SS', 'ha': 'silence',
        'a': 'aa', 'aa': 'aa', 'i': 'I', 'ii': 'I', 'u': 'U', 'uu': 'U',
        'e': 'E', 'ee': 'E', 'ai': 'E', 'o': 'O', 'oo': 'O', 'au': 'O'
    }

    @staticmethod
    def split_kannada_word(word: str) -> List[str]:
        """Split Kannada word into a list of phoneme-like tokens.

        This is heuristic-based and aims to be better than per-character
        splitting. It handles common consonant+vowel combinations and
        independent vowels.
        """
        phonemes = []
        i = 0
        while i < len(word):
            ch = word[i]
            # independent vowel
            if ch in MultilingualPhonemeAnalyzer.KANNADA_VOWELS:
                phonemes.extend(MultilingualPhonemeAnalyzer.KANNADA_VOWELS[ch])
                i += 1
                continue

            # consonant
            if ch in MultilingualPhonemeAnalyzer.KANNADA_CONSONANTS:
                base = MultilingualPhonemeAnalyzer.KANNADA_CONSONANTS[ch]
                # lookahead for vowel sign (matra)
                next_i = i + 1
                if next_i < len(word) and word[next_i] in MultilingualPhonemeAnalyzer.KANNADA_VOWEL_SIGNS:
                    vowel = MultilingualPhonemeAnalyzer.KANNADA_VOWEL_SIGNS[word[next_i]]
                    # remove trailing inherent 'a' if present in base
                    token = base.rstrip('a') + vowel
                    phonemes.append(token)
                    i += 2
                    continue
                else:
                    # consonant with inherent 'a'
                    phonemes.append(base)
                    i += 1
                    continue

            # virama (halant) - suppress inherent vowel: treat next consonant as cluster
            if ch == '್':
                # skip explicit halant marker; cluster handling already implicit
                i += 1
                continue

            # fallback: treat as glyph gap -> silence
            phonemes.append('silence')
            i += 1

        return phonemes

    @staticmethod
    def get_viseme_duration(phoneme: str) -> int:
        # heuristics: vowels longer than consonants
        if any(v in phoneme for v in ['aa', 'ii', 'uu', 'ee', 'oo']):
            return 200
        if any(v in phoneme for v in ['a', 'e', 'i', 'o', 'u', 'ai', 'au']):
            return 150
        if any(asp in phoneme for asp in ['kh', 'gh', 'ch', 'jh', 'th', 'dh', 'ph', 'bh']):
            return 120
        return 80

    @staticmethod
    def get_viseme_for_phoneme(phoneme: str) -> str:
        return MultilingualPhonemeAnalyzer.KANNADA_VISEME_MAP.get(phoneme, 'silence')
