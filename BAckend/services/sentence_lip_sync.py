"""
Sentence Lip Sync Service
Handles full sentence lip sync generation
"""

from .true_audio_lip_mapping import get_true_audio_lip_mapper


def get_sentence_lip_sync():
    """
    Get sentence lip sync service
    This uses the same audio-to-lip mapper
    """
    return get_true_audio_lip_mapper()
