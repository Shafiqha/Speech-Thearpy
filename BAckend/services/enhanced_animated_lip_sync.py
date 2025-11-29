"""
Enhanced Animated Lip Sync
Uses Rhubarb audio-only analysis with audio feature enhancement
"""

from .true_audio_lip_mapping import get_true_audio_lip_mapper


def get_enhanced_animated_lip_sync():
    """
    Get enhanced animated lip sync service
    This is an alias for true_audio_lip_mapper
    """
    return get_true_audio_lip_mapper()
