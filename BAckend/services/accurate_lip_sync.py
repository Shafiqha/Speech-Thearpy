"""
Accurate Lip Sync Service
Wrapper for true audio-to-lip mapping
"""

from .true_audio_lip_mapping import get_true_audio_lip_mapper


def get_accurate_lip_sync_service():
    """
    Get accurate lip sync service
    This is an alias for true_audio_lip_mapper
    """
    return get_true_audio_lip_mapper()
