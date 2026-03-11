from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, Text
import os
from datetime import datetime
import uuid

# Production-grade engine configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/receptionist.db")

# Engine options for stability and performance
engine_args = {
    "echo": False,
    "pool_pre_ping": True,  # Prevent stale connections (Phase 4 Hardening)
}

if "postgresql" in DATABASE_URL:
    engine_args.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
    })

engine = create_async_engine(DATABASE_URL, **engine_args)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class UserDB(Base):
    """Database model for registered businesses/users"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    business_name = Column(String, nullable=False)
    twilio_phone = Column(String, index=True, nullable=True)  # Map incoming calls to this business
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskDB(Base):
    """Database model for tasks"""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, index=True, nullable=False)
    intent = Column(String, nullable=False)
    issue = Column(Text, nullable=False)
    urgency = Column(String, nullable=False)
    location = Column(String, nullable=True)
    preferred_time = Column(String, nullable=True)
    confidence = Column(Float, nullable=False)
    status = Column(String, default="new")
    customer_phone = Column(String, nullable=False)
    customer_name = Column(String, nullable=True)
    transcript = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    escalation_reason = Column(String, nullable=True)
    assigned_to = Column(String, nullable=True)  # Worker ID
    assigned_worker_name = Column(String, nullable=True)  # Worker name for quick display


class WorkerDB(Base):
    """Database model for workers/service providers"""
    __tablename__ = "workers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    skills = Column(Text, nullable=False)  # JSON string of skills array
    status = Column(String, default="available")  # available, busy, offline
    current_tasks = Column(Integer, default=0)
    max_tasks = Column(Integer, default=5)
    rating = Column(Float, nullable=True)
    total_jobs = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatientDB(Base):
    """Database model for clinical patients"""
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, index=True, nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    medical_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DoctorDB(Base):
    """Database model for doctors/medical staff"""
    __tablename__ = "doctors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    specialization = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    schedule = Column(Text, nullable=True)  # JSON string of availability
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppointmentDB(Base):
    """Database model for medical appointments"""
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, index=True, nullable=False)
    patient_id = Column(String, index=True, nullable=False)
    doctor_id = Column(String, index=True, nullable=False)
    date = Column(DateTime, nullable=False)
    time_slot = Column(String, nullable=False)
    status = Column(String, default="scheduled")  # scheduled, completed, cancelled, no_show
    notes = Column(Text, nullable=True)
    created_via = Column(String, default="ai_call")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationSessionDB(Base):
    """Database model for multi-turn conversation sessions (archival)"""
    __tablename__ = "conversation_sessions"

    id = Column(String, primary_key=True)  # Using Twilio call SID
    business_id = Column(String, index=True, nullable=False)
    caller_phone = Column(String, nullable=False)
    patient_id = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)  # Full interaction JSON
    intent = Column(String, nullable=True)
    outcome = Column(String, nullable=True)  # booked, transferred, dropped
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CallLogDB(Base):
    """Database model for call logs"""
    __tablename__ = "call_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    audio_url = Column(String, nullable=True)
    transcript = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    task_id = Column(String, nullable=True)
    success = Column(Boolean, default=True)


class FailureLogDB(Base):
    """Database model for failure logs"""
    __tablename__ = "failure_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, index=True, nullable=True)
    error_message = Column(Text, nullable=False)
    phone_number = Column(String, nullable=True)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    """Initialize database tables"""
    # Create data directory only for SQLite
    if "sqlite" in DATABASE_URL:
        os.makedirs("./data", exist_ok=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session


class PatientVerificationDB(Base):
    """Database model for clinical patient verification (OTP/ID) (Phase 4)"""
    __tablename__ = "patient_verifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, index=True, nullable=False)
    verification_code = Column(String, nullable=False)
    verified = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLogDB(Base):
    """Database model for administrative audit trails (HIPAA requirement) (Phase 4)"""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, index=True, nullable=False)
    user_id = Column(String, nullable=True)  # Admin who performed action
    action = Column(String, nullable=False)  # VIEW_PATIENT, BOOK_APPT, etc.
    resource_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ClinicKnowledgeDB(Base):
    """Database model for clinic-specific knowledge, FAQs, and policies (Phase 3)"""
    __tablename__ = "clinic_knowledge"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False)  # 'general', 'hours', 'policy', 'faq'
    key = Column(String, nullable=False)       # 'phone', 'address', 'cancellation_policy', etc.
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
