from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TaskStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    CLOSED = "closed"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServiceIntent(str, Enum):
    # --- Medical Intents ---
    APPOINTMENT_BOOKING = "Appointment Booking"
    APPOINTMENT_STATUS = "Appointment Status"
    APPOINTMENT_RESCHEDULE = "Appointment Reschedule"
    APPOINTMENT_CANCEL = "Appointment Cancel"
    PRESCRIPTION_RENEWAL = "Prescription Renewal"
    TEST_RESULTS = "Test Results Inquiry"
    DOCTOR_AVAILABILITY = "Doctor Availability"
    GENERAL_INQUIRY = "General Inquiry"
    EMERGENCY = "Emergency"
    
    # --- Legacy Service Intents (For backward compatibility) ---
    AC_REPAIR = "AC Repair"
    PLUMBING = "Plumbing"
    ELECTRICAL = "Electrical"
    GENERAL_MAINTENANCE = "General Maintenance"
    OTHER = "Other"


class WorkerStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class Patient(BaseModel):
    """Patient model representation"""
    id: str
    business_id: str
    name: str
    phone: str
    date_of_birth: Optional[datetime] = None
    medical_id: Optional[str] = None
    created_at: datetime


class Doctor(BaseModel):
    """Doctor model representation"""
    id: str
    business_id: str
    name: str
    specialization: Optional[str] = None
    phone: Optional[str] = None
    schedule: Optional[str] = None  # JSON string
    status: str
    created_at: datetime


class Appointment(BaseModel):
    """Medical appointment representation"""
    id: str
    business_id: str
    patient_id: str
    doctor_id: str
    date: datetime
    time_slot: str
    status: str
    notes: Optional[str] = None
    created_via: str
    created_at: datetime


class ConversationSession(BaseModel):
    """Voice interaction session representation"""
    id: str
    business_id: str
    caller_phone: str
    patient_id: Optional[str] = None
    transcript: Optional[str] = None
    intent: Optional[str] = None
    outcome: Optional[str] = None
    duration_seconds: Optional[int] = None
    created_at: datetime


class Task(BaseModel):
    """Task model representing a service request"""
    id: str
    business_id: str  # Tenant identifier
    intent: str
    issue: str
    urgency: str
    location: Optional[str] = None
    preferred_time: Optional[str] = None
    confidence: float
    status: str
    customer_phone: str
    customer_name: Optional[str] = None
    transcript: str
    created_at: datetime
    updated_at: datetime
    escalation_reason: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_worker_name: Optional[str] = None


class CallLog(BaseModel):
    """Log of all voice interactions"""
    id: str
    business_id: str
    phone_number: str
    audio_url: Optional[str] = None
    transcript: str
    confidence_score: float
    duration_seconds: Optional[int] = None
    created_at: datetime
    task_id: Optional[str] = None
    success: bool


class FailureLog(BaseModel):
    """Log of system failures"""
    id: str
    business_id: Optional[str] = None
    error_message: str
    phone_number: Optional[str] = None
    context: Optional[str] = None
    created_at: datetime


class Worker(BaseModel):
    """Worker model for service providers"""
    id: str
    business_id: str
    name: str
    phone: str
    skills: list[str]
    status: str
    current_tasks: int
    max_tasks: int
    rating: Optional[float] = None
    total_jobs: int
    created_at: datetime
    updated_at: datetime


# --- Authentication Models ---

class UserBase(BaseModel):
    email: str
    business_name: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: datetime


class ClinicKnowledge(BaseModel):
    """Clinic specific knowledge item"""
    id: str
    business_id: str
    category: str
    key: str
    value: str
    updated_at: datetime

class ClinicKnowledgeCreate(BaseModel):
    """Schema for creating/updating knowledge items"""
    category: str
    key: str
    value: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    business_id: Optional[str] = None
