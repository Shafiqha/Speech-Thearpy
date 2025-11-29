"""
Sentence Phoneme Alignment Service
Uses phoneme forced alignment (with audio-only for Hindi/Kannada)
"""

from .phoneme_forced_alignment import get_phoneme_aligner

def get_sentence_aligner():
    """
    Get sentence aligner
    Uses the same phoneme aligner which has audio-only mode for Hindi/Kannada
    """
    return get_phoneme_aligner()
