"""
SQLAlchemy Models for Aphasia Therapy Database
"""

from sqlalchemy import Column, Integer, String, Text, DECIMAL, Enum, Boolean, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from .connection import Base


class User(Base):
    """User model for patients and clinicians"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    user_type = Column(Enum('patient', 'clinician'), nullable=False, index=True)
    phone = Column(String(20))
    date_of_birth = Column(Date)
    gender = Column(Enum('male', 'female', 'other'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False, foreign_keys="PatientProfile.user_id")
    therapy_sessions = relationship("TherapySession", back_populates="patient", foreign_keys="TherapySession.patient_id")
    exercise_attempts = relationship("ExerciseAttempt", back_populates="patient", foreign_keys="ExerciseAttempt.patient_id")
    progress_records = relationship("PatientProgress", back_populates="patient", foreign_keys="PatientProgress.patient_id")


class PatientProfile(Base):
    """Patient profile with medical information"""
    __tablename__ = 'patient_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), unique=True, nullable=False)
    wab_score = Column(DECIMAL(5, 2), default=0.00)
    severity_level = Column(Enum('Mild', 'Moderate', 'Severe', 'Very Severe'), default='Moderate', index=True)
    aphasia_type = Column(String(100))
    preferred_language = Column(String(10), default='en')
    assigned_clinician_id = Column(String(50), ForeignKey('users.user_id', ondelete='SET NULL'), index=True)
    medical_history = Column(Text)
    therapy_start_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="patient_profile", foreign_keys=[user_id], overlaps="patient_profile")
    clinician = relationship("User", foreign_keys=[assigned_clinician_id], overlaps="patient_profile")


class TherapySession(Base):
    """Therapy session records"""
    __tablename__ = 'therapy_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    patient_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    session_type = Column(Enum('sentence', 'picture', 'assessment'), nullable=False, index=True)
    language = Column(String(10), nullable=False)
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='easy')
    start_time = Column(DateTime, default=func.now(), index=True)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    total_exercises = Column(Integer, default=0)
    completed_exercises = Column(Integer, default=0)
    average_accuracy = Column(DECIMAL(5, 2), default=0.00)
    wab_score = Column(DECIMAL(5, 2))
    session_notes = Column(Text)
    
    # Relationships
    patient = relationship("User", back_populates="therapy_sessions")
    exercise_attempts = relationship("ExerciseAttempt", back_populates="session")


class ExerciseAttempt(Base):
    """Individual exercise attempt records"""
    __tablename__ = 'exercise_attempts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    attempt_id = Column(String(50), unique=True, nullable=False, index=True)
    session_id = Column(String(50), ForeignKey('therapy_sessions.session_id', ondelete='CASCADE'), nullable=False, index=True)
    patient_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    exercise_type = Column(Enum('sentence', 'picture'), nullable=False)
    target_text = Column(Text, nullable=False)
    transcription = Column(Text)
    accuracy = Column(DECIMAL(5, 2), default=0.00, index=True)
    wab_score = Column(DECIMAL(5, 2))
    severity_level = Column(String(50))
    feedback = Column(Text)
    word_corrections = Column(JSON)
    practice_suggestions = Column(JSON)
    audio_file_path = Column(String(500))
    attempt_number = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    # Relationships
    session = relationship("TherapySession", back_populates="exercise_attempts")
    patient = relationship("User", back_populates="exercise_attempts")


class PictureExercise(Base):
    """Picture exercise library"""
    __tablename__ = 'picture_exercises'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    picture_id = Column(String(50), unique=True, nullable=False, index=True)
    picture_name = Column(String(255), nullable=False)
    picture_url = Column(String(500), nullable=False)
    target_text_en = Column(String(255))
    target_text_hi = Column(String(255))
    target_text_kn = Column(String(255))
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='easy', index=True)
    category = Column(String(100), index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class SentenceExercise(Base):
    """Sentence exercise library"""
    __tablename__ = 'sentence_exercises'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sentence_id = Column(String(50), unique=True, nullable=False, index=True)
    text_en = Column(Text)
    text_hi = Column(Text)
    text_kn = Column(Text)
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='easy', index=True)
    category = Column(String(100), index=True)
    target_words = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class PatientProgress(Base):
    """Daily progress tracking"""
    __tablename__ = 'patient_progress'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    sessions_completed = Column(Integer, default=0)
    total_exercises = Column(Integer, default=0)
    average_accuracy = Column(DECIMAL(5, 2), default=0.00)
    wab_score = Column(DECIMAL(5, 2))
    severity_level = Column(String(50))
    streak_days = Column(Integer, default=0)
    notes = Column(Text)
    
    # Relationships
    patient = relationship("User", back_populates="progress_records")


class UserDifficultyProgress(Base):
    """Track user difficulty progression per language"""
    __tablename__ = 'user_difficulty_progress'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    language = Column(String(10), nullable=False, index=True)
    easy_completed = Column(Integer, default=0)
    medium_completed = Column(Integer, default=0)
    hard_completed = Column(Integer, default=0)
    current_difficulty = Column(Enum('easy', 'medium', 'hard'), default='easy')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ClinicianNote(Base):
    """Clinician notes for patients"""
    __tablename__ = 'clinician_notes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(String(50), unique=True, nullable=False, index=True)
    patient_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    clinician_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    session_id = Column(String(50), ForeignKey('therapy_sessions.session_id', ondelete='SET NULL'))
    note_type = Column(Enum('assessment', 'progress', 'recommendation', 'other'), default='other')
    title = Column(String(255))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AssessmentResult(Base):
    """Initial assessment results"""
    __tablename__ = 'assessment_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(String(50), unique=True, nullable=False, index=True)
    patient_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    wab_score = Column(DECIMAL(5, 2), nullable=False)
    severity_level = Column(String(50), nullable=False)
    detailed_scores = Column(JSON)
    recommendations = Column(Text)
    assessed_by = Column(String(50), ForeignKey('users.user_id', ondelete='SET NULL'))
    assessment_date = Column(DateTime, default=func.now(), index=True)


class LipAnimationExercise(Base):
    """Lip animation exercise library with phoneme/viseme data"""
    __tablename__ = 'lip_animation_exercises'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exercise_id = Column(String(50), unique=True, nullable=False, index=True)
    word_en = Column(String(255))
    word_hi = Column(String(255))
    word_kn = Column(String(255))
    phonemes_en = Column(JSON)  # Phoneme breakdown for English
    phonemes_hi = Column(JSON)  # Phoneme breakdown for Hindi
    phonemes_kn = Column(JSON)  # Phoneme breakdown for Kannada
    visemes_en = Column(JSON)  # Viseme mapping for English
    visemes_hi = Column(JSON)  # Viseme mapping for Hindi
    visemes_kn = Column(JSON)  # Viseme mapping for Kannada
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='easy', index=True)
    category = Column(String(100), index=True)
    video_path_en = Column(String(500))  # Path to lip animation video (English)
    video_path_hi = Column(String(500))  # Path to lip animation video (Hindi)
    video_path_kn = Column(String(500))  # Path to lip animation video (Kannada)
    audio_path_en = Column(String(500))  # Path to audio file (English)
    audio_path_hi = Column(String(500))  # Path to audio file (Hindi)
    audio_path_kn = Column(String(500))  # Path to audio file (Kannada)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class LipAnimationAttempt(Base):
    """User attempts at lip animation exercises with mouth tracking"""
    __tablename__ = 'lip_animation_attempts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    attempt_id = Column(String(50), unique=True, nullable=False, index=True)
    exercise_id = Column(String(50), ForeignKey('lip_animation_exercises.exercise_id', ondelete='CASCADE'), nullable=False, index=True)
    patient_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    session_id = Column(String(50), ForeignKey('therapy_sessions.session_id', ondelete='CASCADE'), index=True)
    language = Column(String(10), nullable=False)
    target_word = Column(String(255), nullable=False)
    transcription = Column(Text)
    accuracy = Column(DECIMAL(5, 2), default=0.00)
    lip_sync_score = Column(DECIMAL(5, 2), default=0.00)  # How well lips matched target
    mouth_tracking_data = Column(JSON)  # Frame-by-frame mouth tracking data
    phoneme_accuracy = Column(JSON)  # Accuracy per phoneme
    viseme_accuracy = Column(JSON)  # Accuracy per viseme
    errors_detected = Column(JSON)  # Specific errors in lip movements
    feedback = Column(Text)
    video_recording_path = Column(String(500))  # User's video recording
    audio_recording_path = Column(String(500))  # User's audio recording
    attempt_number = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now(), index=True)
