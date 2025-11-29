"""
Database Package
Exports database components for easy import
"""

from .connection import engine, SessionLocal, Base, get_db, get_db_context, init_db, test_connection
from .models import (
    User, PatientProfile, TherapySession, ExerciseAttempt,
    PictureExercise, SentenceExercise, PatientProgress,
    ClinicianNote, AssessmentResult, LipAnimationAttempt,
    UserDifficultyProgress
)
from .config import DB_CONFIG, DATABASE_URL

__all__ = [
    'engine',
    'SessionLocal',
    'Base',
    'get_db',
    'get_db_context',
    'init_db',
    'test_connection',
    'User',
    'PatientProfile',
    'TherapySession',
    'ExerciseAttempt',
    'PictureExercise',
    'SentenceExercise',
    'PatientProgress',
    'ClinicianNote',
    'AssessmentResult',
    'DB_CONFIG',
    'DATABASE_URL'
]
