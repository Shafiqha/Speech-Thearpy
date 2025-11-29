"""
Database API Routes for User Data and Session Management
Integrates with XAMPP MySQL database
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import text
import sys
import os
import uuid
import bcrypt

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db
from database.models import (
    User, PatientProfile, TherapySession, ExerciseAttempt,
    PatientProgress, LipAnimationAttempt
)

router = APIRouter(prefix="/api/db", tags=["Database"])
security = HTTPBearer()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    user_type: str  # 'patient' or 'clinician'
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    user_type: str
    is_active: bool
    created_at: datetime


class SessionCreate(BaseModel):
    patient_id: str
    session_type: str  # 'sentence', 'picture', 'assessment'
    language: str
    difficulty: Optional[str] = 'easy'


class SessionResponse(BaseModel):
    session_id: str
    patient_id: str
    session_type: str
    language: str
    difficulty: str
    start_time: datetime
    total_exercises: int
    completed_exercises: int
    average_accuracy: float


class ExerciseAttemptCreate(BaseModel):
    session_id: str
    patient_id: str
    exercise_type: str
    target_text: str
    transcription: Optional[str] = None
    accuracy: Optional[float] = 0.0
    wab_score: Optional[float] = None
    feedback: Optional[str] = None


class ExerciseAttemptResponse(BaseModel):
    attempt_id: str
    session_id: str
    exercise_type: str
    target_text: str
    transcription: Optional[str]
    accuracy: float
    created_at: datetime


class ProgressResponse(BaseModel):
    date: date
    sessions_completed: int
    total_exercises: int
    average_accuracy: float
    streak_days: int


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create user
    new_user = User(
        user_id=f"{user_data.user_type}_{uuid.uuid4().hex[:8]}",
        email=user_data.email,
        password_hash=password_hash,
        name=user_data.name,
        user_type=user_data.user_type,
        phone=user_data.phone,
        date_of_birth=user_data.date_of_birth,
        gender=user_data.gender,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create patient profile if user is a patient
    if user_data.user_type == 'patient':
        profile = PatientProfile(
            user_id=new_user.user_id,
            severity_level='Moderate',
            preferred_language='en',
            therapy_start_date=date.today()
        )
        db.add(profile)
        db.commit()
    
    return UserResponse(
        user_id=new_user.user_id,
        email=new_user.email,
        name=new_user.name,
        user_type=new_user.user_type,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )


@router.post("/login", response_model=UserResponse)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    
    # Find user
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login
    user.last_login = datetime.now()
    db.commit()
    
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        user_type=user.user_type,
        is_active=user.is_active,
        created_at=user.created_at
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID"""
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        user_type=user.user_type,
        is_active=user.is_active,
        created_at=user.created_at
    )


# ============================================================================
# SESSION ROUTES
# ============================================================================

@router.post("/sessions", response_model=SessionResponse)
async def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    """Create a new therapy session"""
    
    # Verify patient exists
    patient = db.query(User).filter(User.user_id == session_data.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Create session
    new_session = TherapySession(
        session_id=f"session_{uuid.uuid4().hex[:8]}",
        patient_id=session_data.patient_id,
        session_type=session_data.session_type,
        language=session_data.language,
        difficulty=session_data.difficulty,
        start_time=datetime.now(),
        total_exercises=0,
        completed_exercises=0,
        average_accuracy=0.0
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return SessionResponse(
        session_id=new_session.session_id,
        patient_id=new_session.patient_id,
        session_type=new_session.session_type,
        language=new_session.language,
        difficulty=new_session.difficulty,
        start_time=new_session.start_time,
        total_exercises=new_session.total_exercises,
        completed_exercises=new_session.completed_exercises,
        average_accuracy=float(new_session.average_accuracy)
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get session by ID"""
    
    session = db.query(TherapySession).filter(TherapySession.session_id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return SessionResponse(
        session_id=session.session_id,
        patient_id=session.patient_id,
        session_type=session.session_type,
        language=session.language,
        difficulty=session.difficulty,
        start_time=session.start_time,
        total_exercises=session.total_exercises,
        completed_exercises=session.completed_exercises,
        average_accuracy=float(session.average_accuracy)
    )


@router.get("/sessions/patient/{patient_id}", response_model=List[SessionResponse])
async def get_patient_sessions(patient_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """Get all sessions for a patient"""
    
    sessions = db.query(TherapySession)\
        .filter(TherapySession.patient_id == patient_id)\
        .order_by(TherapySession.start_time.desc())\
        .limit(limit)\
        .all()
    
    return [
        SessionResponse(
            session_id=s.session_id,
            patient_id=s.patient_id,
            session_type=s.session_type,
            language=s.language,
            difficulty=s.difficulty,
            start_time=s.start_time,
            total_exercises=s.total_exercises,
            completed_exercises=s.completed_exercises,
            average_accuracy=float(s.average_accuracy)
        )
        for s in sessions
    ]


@router.put("/sessions/{session_id}/complete")
async def complete_session_db(session_id: str, db: Session = Depends(get_db)):
    """Mark a session as complete and update progress"""
    
    session = db.query(TherapySession).filter(TherapySession.session_id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Mark session as complete
    session.end_time = datetime.now()
    session.duration_seconds = int((session.end_time - session.start_time).total_seconds())
    
    # Update or create daily progress record
    today = date.today()
    progress = db.query(PatientProgress).filter(
        PatientProgress.patient_id == session.patient_id,
        PatientProgress.date == today
    ).first()
    
    if not progress:
        progress = PatientProgress(
            patient_id=session.patient_id,
            date=today,
            sessions_completed=0,
            total_exercises=0,
            average_accuracy=0.0,
            streak_days=1
        )
        db.add(progress)
    
    # Update progress
    progress.sessions_completed += 1
    progress.total_exercises += session.completed_exercises
    
    # Recalculate average accuracy for the day
    all_attempts_today = db.query(ExerciseAttempt).filter(
        ExerciseAttempt.patient_id == session.patient_id,
        ExerciseAttempt.created_at >= datetime.combine(today, datetime.min.time())
    ).all()
    
    if all_attempts_today:
        total_accuracy = sum(float(a.accuracy) for a in all_attempts_today)
        progress.average_accuracy = total_accuracy / len(all_attempts_today)
    
    # Update WAB score if available
    if session.wab_score:
        progress.wab_score = session.wab_score
    
    db.commit()
    
    return {
        "session_id": session_id,
        "status": "completed",
        "duration_seconds": session.duration_seconds,
        "progress_updated": True
    }


# ============================================================================
# EXERCISE ATTEMPT ROUTES
# ============================================================================

@router.post("/attempts", response_model=ExerciseAttemptResponse)
async def create_exercise_attempt(attempt_data: ExerciseAttemptCreate, db: Session = Depends(get_db)):
    """Save an exercise attempt"""
    
    # Create attempt
    new_attempt = ExerciseAttempt(
        attempt_id=f"attempt_{uuid.uuid4().hex[:8]}",
        session_id=attempt_data.session_id,
        patient_id=attempt_data.patient_id,
        exercise_type=attempt_data.exercise_type,
        target_text=attempt_data.target_text,
        transcription=attempt_data.transcription,
        accuracy=attempt_data.accuracy,
        wab_score=attempt_data.wab_score,
        feedback=attempt_data.feedback,
        attempt_number=1
    )
    
    db.add(new_attempt)
    
    # Update session statistics
    session = db.query(TherapySession).filter(
        TherapySession.session_id == attempt_data.session_id
    ).first()
    
    if session:
        session.total_exercises += 1
        session.completed_exercises += 1
        
        # Recalculate average accuracy
        attempts = db.query(ExerciseAttempt).filter(
            ExerciseAttempt.session_id == attempt_data.session_id
        ).all()
        
        if attempts:
            total_accuracy = sum(float(a.accuracy) for a in attempts) + attempt_data.accuracy
            session.average_accuracy = total_accuracy / (len(attempts) + 1)
    
    db.commit()
    db.refresh(new_attempt)
    
    return ExerciseAttemptResponse(
        attempt_id=new_attempt.attempt_id,
        session_id=new_attempt.session_id,
        exercise_type=new_attempt.exercise_type,
        target_text=new_attempt.target_text,
        transcription=new_attempt.transcription,
        accuracy=float(new_attempt.accuracy),
        created_at=new_attempt.created_at
    )


@router.get("/attempts/session/{session_id}", response_model=List[ExerciseAttemptResponse])
async def get_session_attempts(session_id: str, db: Session = Depends(get_db)):
    """Get all attempts for a session"""
    
    attempts = db.query(ExerciseAttempt)\
        .filter(ExerciseAttempt.session_id == session_id)\
        .order_by(ExerciseAttempt.created_at)\
        .all()
    
    return [
        ExerciseAttemptResponse(
            attempt_id=a.attempt_id,
            session_id=a.session_id,
            exercise_type=a.exercise_type,
            target_text=a.target_text,
            transcription=a.transcription,
            accuracy=float(a.accuracy),
            created_at=a.created_at
        )
        for a in attempts
    ]


# ============================================================================
# PROGRESS ROUTES
# ============================================================================

@router.get("/progress/{patient_id}", response_model=List[ProgressResponse])
async def get_patient_progress(patient_id: str, days: int = 30, db: Session = Depends(get_db)):
    """Get patient progress over time"""
    
    progress_records = db.query(PatientProgress)\
        .filter(PatientProgress.patient_id == patient_id)\
        .order_by(PatientProgress.date.desc())\
        .limit(days)\
        .all()
    
    return [
        ProgressResponse(
            date=p.date,
            sessions_completed=p.sessions_completed,
            total_exercises=p.total_exercises,
            average_accuracy=float(p.average_accuracy),
            streak_days=p.streak_days
        )
        for p in progress_records
    ]


@router.get("/stats/{patient_id}")
async def get_patient_stats(patient_id: str, db: Session = Depends(get_db)):
    """Get overall patient statistics"""
    
    from sqlalchemy import func
    
    # Total sessions
    total_sessions = db.query(func.count(TherapySession.id))\
        .filter(TherapySession.patient_id == patient_id)\
        .scalar()
    
    # Total exercises
    total_exercises = db.query(func.count(ExerciseAttempt.id))\
        .filter(ExerciseAttempt.patient_id == patient_id)\
        .scalar()
    
    # Average accuracy
    avg_accuracy = db.query(func.avg(ExerciseAttempt.accuracy))\
        .filter(ExerciseAttempt.patient_id == patient_id)\
        .scalar()
    
    # Recent sessions
    recent_sessions = db.query(TherapySession)\
        .filter(TherapySession.patient_id == patient_id)\
        .order_by(TherapySession.start_time.desc())\
        .limit(5)\
        .all()
    
    return {
        "patient_id": patient_id,
        "total_sessions": total_sessions or 0,
        "total_exercises": total_exercises or 0,
        "average_accuracy": float(avg_accuracy) if avg_accuracy else 0.0,
        "recent_sessions": [
            {
                "session_id": s.session_id,
                "type": s.session_type,
                "date": s.start_time.isoformat(),
                "accuracy": float(s.average_accuracy),
                "difficulty": s.difficulty,
                "duration": s.duration_seconds if s.duration_seconds else 0
            }
            for s in recent_sessions
        ]
    }


@router.get("/category-performance/{patient_id}")
async def get_category_performance(patient_id: str, db: Session = Depends(get_db)):
    """Get performance by difficulty category"""
    
    from sqlalchemy import func
    
    # Get performance by difficulty level
    difficulty_stats = db.query(
        TherapySession.difficulty,
        func.count(ExerciseAttempt.id).label('total'),
        func.avg(ExerciseAttempt.accuracy).label('avg_accuracy')
    ).join(
        ExerciseAttempt, TherapySession.session_id == ExerciseAttempt.session_id
    ).filter(
        TherapySession.patient_id == patient_id
    ).group_by(
        TherapySession.difficulty
    ).all()
    
    # Format for frontend
    categories = []
    for difficulty, total, avg_accuracy in difficulty_stats:
        categories.append({
            "name": difficulty.capitalize() if difficulty else "Unknown",
            "value": float(avg_accuracy) if avg_accuracy else 0.0,
            "total_exercises": total or 0,
            "fill": "#ADD4EB" if difficulty == "easy" else "#A6BAA3" if difficulty == "medium" else "#B8A5D6"
        })
    
    # Add empty categories if missing
    existing_difficulties = [c["name"].lower() for c in categories]
    for diff in ["easy", "medium", "hard"]:
        if diff not in existing_difficulties:
            categories.append({
                "name": diff.capitalize(),
                "value": 0.0,
                "total_exercises": 0,
                "fill": "#ADD4EB" if diff == "easy" else "#A6BAA3" if diff == "medium" else "#B8A5D6"
            })
    
    return {
        "patient_id": patient_id,
        "categories": sorted(categories, key=lambda x: ["easy", "medium", "hard"].index(x["name"].lower()))
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def database_health(db: Session = Depends(get_db)):
    """Check database connection"""
    try:
        # Try a simple query
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "message": "Database is accessible"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
