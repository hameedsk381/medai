from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
import os
import asyncio
from dotenv import load_dotenv

from app.services.intent_service import IntentService
from app.services.task_service import TaskService
from app.services.voice_service import VoiceService
from app.database import init_db, get_db
from app.models import (
    TaskStatus, UrgencyLevel, Token, TokenData, UserCreate,
    Doctor, Patient, Appointment, ConversationSession,
    ClinicKnowledge, ClinicKnowledgeCreate
)
from app.services.auth_service import AuthService
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, WebSocket, WebSocketDisconnect, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.realtime_pipeline import RealtimeVoicePipeline
from app.services.web_pipeline import WebVoicePipeline
from app.utils.safe_print import safe_print as print
import json

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    await init_db()
    print("✅ Database initialized")
    yield

app = FastAPI(
    title="AI Voice + Task Intelligence Platform",
    description="B2B operational tool for voice-based intake and task intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
intent_service = IntentService()
task_service = TaskService()
voice_service = VoiceService()
from app.services.worker_service import WorkerService
worker_service = WorkerService()
auth_service = AuthService()

# Security configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_business(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency to get the current business_id from JWT"""
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    business_id = payload.get("business_id")
    if not business_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing business_id")
    return business_id


# Request/Response Models
class VoiceCallRequest(BaseModel):
    phone_number: str
    audio_url: Optional[str] = None
    voice_text: Optional[str] = None  # For WhatsApp voice notes transcribed


class TaskResponse(BaseModel):
    task_id: str
    intent: str
    issue: str
    urgency: str
    location: Optional[str]
    preferred_time: Optional[str]
    confidence: float
    status: str
    created_at: datetime
    customer_phone: str


class EscalationRequest(BaseModel):
    task_id: str
    reason: str


class DashboardStats(BaseModel):
    total_calls: int
    tasks_created: int
    escalations: int
    failures: int
    appointments_count: int
    patients_count: int
    success_rate: float


class DoctorCreate(BaseModel):
    name: str
    specialization: Optional[str] = None
    phone: Optional[str] = None




@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "operational",
        "service": "AI Voice + Task Intelligence Platform (Multi-Tenant)",
        "version": "1.0.0"
    }


# ============================================
# Authentication Endpoints
# ============================================

@app.post("/api/auth/register", response_model=Dict)
async def register(user_data: UserCreate):
    """Register a new business account"""
    user = await auth_service.register_business(
        user_data.email, 
        user_data.password, 
        user_data.business_name
    )
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return {"message": "Business registered successfully", "id": user.id}


@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(
        data={"sub": user.email, "business_id": user.id}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me")
async def get_me(business_id: str = Depends(get_current_business)):
    """Get current business profile info"""
    # This would normally fetch from DB, simplified for now
    return {"business_id": business_id}


@app.post("/api/voice/inbound", response_model=TaskResponse)
async def handle_inbound_call(
    request: VoiceCallRequest,
    background_tasks: BackgroundTasks
):
    """
    Handle inbound phone calls or WhatsApp voice notes
    1. Transcribe audio (STT)
    2. Extract intent and entities
    3. Create task
    4. Trigger notifications
    """
    try:
        # Step 1: Get transcription
        if request.audio_url:
            transcript = await voice_service.transcribe_audio(request.audio_url)
        elif request.voice_text:
            transcript = request.voice_text
        else:
            raise HTTPException(400, "Either audio_url or voice_text required")
        
        # Step 2: Extract intent and entities
        intent_result = await intent_service.extract_intent(transcript)
        
        # Step 3: Check confidence threshold
        threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
        if intent_result["confidence"] < threshold:
            # Auto-escalate low confidence
            background_tasks.add_task(
                task_service.send_escalation_notification,
                intent_result,
                "Low confidence score",
                request.phone_number
            )
        
        # Step 4: Create task
        task = await task_service.create_task(
            intent=intent_result["intent"],
            issue=intent_result["issue"],
            urgency=intent_result["urgency"],
            location=intent_result.get("location"),
            preferred_time=intent_result.get("preferred_time"),
            confidence=intent_result["confidence"],
            customer_phone=request.phone_number,
            transcript=transcript
        )
        
        # Step 5: Send notification to operations team
        background_tasks.add_task(
            task_service.send_task_notification,
            task
        )
        
        return TaskResponse(
            task_id=task["id"],
            intent=task["intent"],
            issue=task["issue"],
            urgency=task["urgency"],
            location=task["location"],
            preferred_time=task["preferred_time"],
            confidence=task["confidence"],
            status=task["status"],
            created_at=task["created_at"],
            customer_phone=task["customer_phone"]
        )
        
    except Exception as e:
        # Log failure
        await task_service.log_failure(str(e), request.phone_number)
        raise HTTPException(500, f"Failed to process call: {str(e)}")


@app.get("/api/tasks", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    business_id: str = Depends(get_current_business)
):
    """Get tasks filtered by current business tenant"""
    tasks = await task_service.get_tasks(status=status, business_id=business_id, limit=limit)
    return tasks


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get specific task by ID"""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@app.patch("/api/tasks/{task_id}/status")
async def update_task_status(task_id: str, status: str):
    """Update task status"""
    valid_statuses = ["new", "in_progress", "escalated", "closed"]
    if status not in valid_statuses:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid_statuses}")
    
    task = await task_service.update_task_status(task_id, status)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@app.post("/api/tasks/{task_id}/escalate")
async def escalate_task(task_id: str, request: EscalationRequest):
    """Manually escalate a task"""
    task = await task_service.escalate_task(task_id, request.reason)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(business_id: str = Depends(get_current_business)):
    """Get dashboard statistics for current business"""
    stats = await task_service.get_dashboard_stats(business_id=business_id)
    return stats




@app.get("/api/logs/failures")
async def get_failures(limit: int = 50):
    """Get failure logs"""
    failures = await task_service.get_failures(limit=limit)
    return failures


# ============================================
# Worker Management API
# ============================================

@app.post("/api/workers")
async def create_worker(
    name: str,
    phone: str,
    skills: List[str],
    max_tasks: int = 5,
    business_id: str = Depends(get_current_business)
):
    """Create a new worker"""
    try:
        worker = await worker_service.create_worker(name, phone, skills, business_id, max_tasks)
        return worker
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/workers")
async def get_workers(
    status: Optional[str] = None,
    skill: Optional[str] = None,
    business_id: str = Depends(get_current_business)
):
    """Get all workers with optional filters"""
    workers = await worker_service.get_workers(business_id=business_id, status=status, skill=skill)
    return workers


@app.get("/api/workers/{worker_id}")
async def get_worker(worker_id: str, business_id: str = Depends(get_current_business)):
    """Get specific worker"""
    worker = await worker_service.get_worker(worker_id)
    if not worker or worker.get("business_id") != business_id:
        raise HTTPException(404, "Worker not found or access denied")
    return worker


@app.patch("/api/workers/{worker_id}")
async def update_worker(
    worker_id: str,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    skills: Optional[List[str]] = None,
    status: Optional[str] = None,
    max_tasks: Optional[int] = None,
    business_id: str = Depends(get_current_business)
):
    """Update worker details"""
    # Verify ownership
    existing = await worker_service.get_worker(worker_id)
    if not existing or existing.get("business_id") != business_id:
        raise HTTPException(404, "Worker not found or access denied")
        
    worker = await worker_service.update_worker(
        worker_id, name, phone, skills, status, max_tasks
    )
    return worker


@app.delete("/api/workers/{worker_id}")
async def delete_worker(worker_id: str, business_id: str = Depends(get_current_business)):
    """Delete a worker"""
    # Verify ownership
    existing = await worker_service.get_worker(worker_id)
    if not existing or existing.get("business_id") != business_id:
        raise HTTPException(404, "Worker not found or access denied")
        
    success = await worker_service.delete_worker(worker_id)
    return {"message": "Worker deleted successfully"}


@app.post("/api/tasks/{task_id}/assign")
async def assign_task(
    task_id: str,
    worker_id: Optional[str] = None
):
    """Assign task to worker (manual or auto)"""
    try:
        if worker_id:
            # Manual assignment
            result = await worker_service.assign_task_to_worker(task_id, worker_id)
        else:
            # Auto assignment
            result = await worker_service.auto_assign_task(task_id)
        
        if not result:
            raise HTTPException(404, "Task or worker not found, or no available worker")
        
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    rating: Optional[float] = None
):
    """Mark task as complete"""
    await worker_service.complete_task(task_id, rating)
    
    # Update task status
    await task_service.update_task_status(task_id, "closed")
    
    return {"message": "Task completed successfully"}

# ============================================
# Medical Management API (Phase 3)
# ============================================

@app.get("/api/doctors", response_model=List[Doctor])
async def get_doctors(
    business_id: str = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Get all doctors for a clinic"""
    from app.services.appointment_service import AppointmentService
    service = AppointmentService(db)
    return await service.get_all_doctors(business_id)

@app.post("/api/doctors", response_model=Doctor)
async def create_doctor(
    doctor_data: DoctorCreate,
    business_id: str = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Add a new doctor to the clinic"""
    from app.services.appointment_service import AppointmentService
    service = AppointmentService(db)
    return await service.create_doctor(
        name=doctor_data.name,
        specialization=doctor_data.specialization,
        phone=doctor_data.phone,
        business_id=business_id
    )

@app.get("/api/appointments", response_model=List[Appointment])
async def get_appointments(
    business_id: str = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Get all appointments for a clinic"""
    from app.services.appointment_service import AppointmentService
    service = AppointmentService(db)
    return await service.get_all_appointments(business_id)

@app.get("/api/patients", response_model=List[Patient])
async def get_patients(
    business_id: str = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Get all patients for a clinic"""
    from app.services.appointment_service import AppointmentService
    service = AppointmentService(db)
    return await service.get_all_patients(business_id)

@app.get("/api/conversations", response_model=List[ConversationSession])
async def get_conversations(
    business_id: str = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Get all conversation archival sessions"""
    from app.database import ConversationSessionDB
    from sqlalchemy import select
    result = await db.execute(
        select(ConversationSessionDB)
        .where(ConversationSessionDB.business_id == business_id)
        .order_by(ConversationSessionDB.created_at.desc())
    )
    return result.scalars().all()


@app.get("/api/audit-logs")
async def get_audit_logs(
    business_id: str = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Fetch administrative audit trails (Phase 4 HIPAA)"""
    from app.database import AuditLogDB
    from sqlalchemy import select
    result = await db.execute(
        select(AuditLogDB)
        .where(AuditLogDB.business_id == business_id)
        .order_by(AuditLogDB.created_at.desc())
        .limit(100)
    )
    return result.scalars().all()


# --- Clinic Knowledge API ---

@app.get("/api/knowledge", response_model=List[ClinicKnowledge])
async def get_clinic_knowledge(
    business_id: str = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all knowledge base items for the clinic"""
    from app.database import ClinicKnowledgeDB
    from sqlalchemy import select
    result = await db.execute(
        select(ClinicKnowledgeDB).where(ClinicKnowledgeDB.business_id == business_id)
    )
    return result.scalars().all()

@app.post("/api/knowledge", response_model=ClinicKnowledge)
async def create_knowledge_item(
    item: ClinicKnowledgeCreate,
    business_id: str = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Add or update a knowledge base item"""
    from app.database import ClinicKnowledgeDB
    from sqlalchemy import select
    import uuid
    
    # Check if key exists in category for this business
    existing_result = await db.execute(
        select(ClinicKnowledgeDB).where(
            ClinicKnowledgeDB.business_id == business_id,
            ClinicKnowledgeDB.category == item.category,
            ClinicKnowledgeDB.key == item.key
        )
    )
    existing = existing_result.scalars().first()
    
    if existing:
        existing.value = item.value
        await db.commit()
        await db.refresh(existing)
        return existing
    
    new_item = ClinicKnowledgeDB(
        id=str(uuid.uuid4()),
        business_id=business_id,
        category=item.category,
        key=item.key,
        value=item.value
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

@app.delete("/api/knowledge/{item_id}")
async def delete_knowledge_item(
    item_id: str,
    business_id: str = Depends(get_current_business),
    db: AsyncSession = Depends(get_db)
):
    """Delete a knowledge base item"""
    from app.database import ClinicKnowledgeDB
    from sqlalchemy import select, delete
    
    result = await db.execute(
        select(ClinicKnowledgeDB).where(
            ClinicKnowledgeDB.id == item_id,
            ClinicKnowledgeDB.business_id == business_id
        )
    )
    item = result.scalars().first()
    if not item:
        raise HTTPException(404, "Knowledge item not found")
        
    await db.delete(item)
    await db.commit()
    return {"message": "Knowledge item deleted"}


@app.get("/api/workers/stats")
async def get_worker_stats(business_id: str = Depends(get_current_business)):
    """Get worker statistics"""
    stats = await worker_service.get_worker_stats(business_id=business_id)
    return stats


# ============================================
# PHASE 2: Twilio Webhook Endpoints
# ============================================

@app.post("/api/twilio/voice-inbound")
async def twilio_voice_inbound(request: Request):
    """
    Twilio webhook for inbound phone calls
    Starts a real-time voice stream to our WebSocket
    """
    from app.services.twilio_service import TwilioService
    from app.database import AsyncSessionLocal, UserDB
    from sqlalchemy import select
    
    form_data = await request.form()
    caller_number = form_data.get("From", "Unknown")
    to_number = form_data.get("To", "Unknown")
    
    print(f"📞 Incoming call from: {caller_number} to {to_number}")
    
    # Lookup business by phone number
    business_id = "demo-clinic-1" # Default
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(UserDB).where(UserDB.twilio_phone == to_number))
        user = result.scalars().first()
        if user:
            business_id = user.id
    
    # We need the host to provide the WebSocket URL to Twilio
    host = request.headers.get("host", "localhost:8000")
    
    twilio = TwilioService()
    twiml = twilio.generate_stream_twiml(
        host=host,
        business_id=business_id,
        caller_phone=caller_number
    )
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/api/twilio/outbound-answer")
async def twilio_outbound_answer(request: Request, business_id: str = "c39a32dd-3045-4a1e-8265-a21315b9427d"):
    """
    Twilio webhook when an outbound call is answered
    """
    try:
        from app.services.twilio_service import TwilioService
        import os
        form_data = await request.form()
        caller_number = form_data.get("To", "Unknown")
        
        # Log all headers for debugging
        headers_log = "--- Inbound Headers ---\n"
        for k, v in request.headers.items():
            headers_log += f"{k}: {v}\n"
        headers_log += "----------------------\n"
        
        with open("call_log.txt", "a", encoding="utf-8") as f:
            f.write(headers_log)
            
        # Force use of public ngrok URL for Twilio callbacks
        base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        host = base_url.replace("https://", "").replace("http://", "")
        
        log_msg = f"📞 Outbound call answered. Host for Stream: {host}, Business: {business_id}\n"
        with open("call_log.txt", "a", encoding="utf-8") as f:
            f.write(log_msg)
        
        twilio = TwilioService()
        # Add is_outbound=true to the stream URL in the TwiML
        twiml = twilio.generate_stream_twiml(
            host=host,
            business_id=business_id,
            is_outbound=True,
            caller_phone=caller_number
        )
        
        with open("call_log.txt", "a", encoding="utf-8") as f:
            f.write(f"📢 Generated TwiML: {twiml}\n")
            
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        with open("call_log.txt", "a", encoding="utf-8") as f:
            f.write(f"❌ Error in outbound-answer: {e}\n")
        return Response(content=f"<Response><Say>Error: {str(e)}</Say></Response>", media_type="application/xml")

@app.post("/api/voice/trigger-outcall")
async def trigger_outbound_call(
    request: VoiceCallRequest,
    business_id: str = Depends(get_current_business)
):
    """
    Manually trigger an outbound call flow
    """
    from app.services.twilio_service import TwilioService
    
    twilio = TwilioService()
    # The callback URL Twilio will hit when the user answers
    # We use a public URL if available, otherwise assume local/tunnel
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    callback_url = f"{base_url}/api/twilio/outbound-answer?business_id={business_id}"
    
    call_sid = await twilio.initiate_outbound_call(
        to_phone=request.phone_number,
        callback_url=callback_url
    )
    
    if not call_sid:
        raise HTTPException(500, "Failed to initiate outbound call")
        
    return {"message": "Outbound call initiated", "call_sid": call_sid}

@app.websocket("/voice-stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Streams
    """
    try:
        await websocket.accept()
    except Exception as e:
        with open("call_log.txt", "a", encoding="utf-8") as f:
            f.write(f"❌ WebSocket Accept Failed: {e}\n")
        return

    # Create pipeline with error wrap
    try:
        pipeline = RealtimeVoicePipeline(websocket)
    except Exception as e:
        with open("call_log.txt", "a", encoding="utf-8") as f:
            f.write(f"❌ Pipeline Initialization Failed: {e}\n")
        await websocket.close()
        return
    
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data['event'] == 'start':
                print(f"⏩ Stream starting: {data['start']['streamSid']}")
                pipeline.stream_sid = data['start']['streamSid']
                pipeline.call_sid = data['start']['callSid']
                
                # Extract parameters from Twilio <Parameter> tags
                custom_params = data['start'].get('customParameters', {})
                pipeline.business_id = custom_params.get("business_id", "c39a32dd-3045-4a1e-8265-a21315b9427d")
                pipeline.is_outbound = custom_params.get("is_outbound", "false").lower() == "true"
                
                log_msg = f"🔌 WebSocket connected for Clinic: {pipeline.business_id} (Outbound: {pipeline.is_outbound})\n"
                with open("call_log.txt", "a", encoding="utf-8") as f:
                    f.write(log_msg)

                # Fetch caller phone and initialize state before any agent turn
                pipeline.caller_phone = custom_params.get('caller', "Unknown")
                if pipeline.state:
                    await pipeline.state.create_session(
                        pipeline.call_sid, 
                        pipeline.business_id, 
                        pipeline.caller_phone
                    )

                # Start the pipeline with the correct context
                await pipeline.start()
                
            elif data['event'] == 'media':
                # Process the audio chunk
                await pipeline.process_audio_chunk(data['media']['payload'])
                
            elif data['event'] == 'stop':
                print("🛑 Stream stopped")
                break
                
    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        await pipeline.stop()


@app.websocket("/web-voice-stream")
async def web_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for Browser-based Voice Interaction
    """
    try:
        await websocket.accept()
        # Small delay to ensure connection state is fully propagated
        await asyncio.sleep(0.1)
    except Exception as e:
        print(f"❌ WebSocket Accept Failed: {e}")
        return
    
    # Optional: verify token here if needed
    
    from app.services.web_pipeline import WebVoicePipeline
    pipeline = WebVoicePipeline(websocket)
    
    try:
        await pipeline.start()
        
        while True:
            # Browser sends JSON
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data['event'] == 'media':
                pass # Backend STT disabled for web. Using Web Speech API.
            
            elif data['event'] == 'transcript_input':
                is_final = data.get('is_final', False)
                await pipeline.process_transcript_input(data['payload'], is_final)
            
            elif data['event'] == 'stop':
                break
                
    except WebSocketDisconnect:
        print("🌐 Web WebSocket disconnected")
    except Exception as e:
        print(f"❌ Web WebSocket error: {e}")
    finally:
        await pipeline.stop()


@app.post("/api/twilio/process-recording")
async def twilio_process_recording(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Twilio webhook after recording is complete
    Process the audio and create task
    """
    from fastapi.responses import Response
    from app.services.twilio_service import TwilioService
    
    form_data = await request.form()
    recording_url = form_data.get("RecordingUrl")
    caller_number = form_data.get("From", "Unknown")
    to_number = form_data.get("To", "")
    recording_sid = form_data.get("RecordingSid")
    
    # Lookup business
    business = await auth_service.get_business_by_phone(to_number)
    business_id = business.id if business else "system"
    
    print(f"🎙️ Processing recording for {business_id} from {caller_number}: {recording_sid}")
    
    # Process in background
    background_tasks.add_task(
        process_voice_recording,
        recording_url,
        caller_number,
        recording_sid,
        business_id
    )
    
    # Return confirmation TwiML
    twilio = TwilioService()
    twiml = twilio.generate_confirmation_twiml()
    
    return Response(content=twiml, media_type="application/xml")


@app.post("/api/twilio/recording-status")
async def twilio_recording_status(request: Request):
    """
    Twilio callback for recording status updates
    """
    form_data = await request.form()
    recording_sid = form_data.get("RecordingSid")
    status = form_data.get("RecordingStatus")
    
    print(f"📹 Recording {recording_sid} status: {status}")
    return {"status": "received"}


@app.post("/api/twilio/whatsapp-inbound")
async def twilio_whatsapp_inbound(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Twilio webhook for inbound WhatsApp messages
    Handles voice notes and text messages
    """
    from fastapi.responses import Response
    
    form_data = await request.form()
    from_number = form_data.get("From", "").replace("whatsapp:", "")
    to_number = form_data.get("To", "").replace("whatsapp:", "")
    message_body = form_data.get("Body", "")
    media_url = form_data.get("MediaUrl0")  # Voice note or image
    media_type = form_data.get("MediaContentType0", "")
    
    # Lookup business
    business = await auth_service.get_business_by_phone(to_number)
    business_id = business.id if business else "system"
    
    print(f"💬 WhatsApp for {business_id} from {from_number}")
    
    try:
        # Handle voice notes
        if media_url and "audio" in media_type:
            print(f"🎙️ Voice note received: {media_url}")
            
            # Transcribe and process
            transcript = await voice_service.transcribe_audio(media_url)
            
            # Extract intent
            intent_result = await intent_service.extract_intent(transcript)
            
            # Create task
            task = await task_service.create_task(
                intent=intent_result["intent"],
                issue=intent_result["issue"],
                urgency=intent_result["urgency"],
                business_id=business_id,
                location=intent_result.get("location"),
                preferred_time=intent_result.get("preferred_time"),
                confidence=intent_result["confidence"],
                customer_phone=from_number,
                transcript=transcript
            )
            
            # Send confirmation to customer
            background_tasks.add_task(
                send_whatsapp_confirmation,
                from_number,
                task
            )
            
            # Notify operations team
            background_tasks.add_task(
                task_service.send_task_notification,
                task
            )
        
        # Handle text messages
        elif message_body:
            print(f"💬 Text message: {message_body}")
            
            # Extract intent from text
            intent_result = await intent_service.extract_intent(message_body)
            
            # Create task
            task = await task_service.create_task(
                intent=intent_result["intent"],
                issue=intent_result["issue"],
                urgency=intent_result["urgency"],
                location=intent_result.get("location"),
                preferred_time=intent_result.get("preferred_time"),
                confidence=intent_result["confidence"],
                customer_phone=from_number,
                transcript=message_body
            )
            
            # Send confirmation
            background_tasks.add_task(
                send_whatsapp_confirmation,
                from_number,
                task
            )
            
            # Notify operations team
            background_tasks.add_task(
                task_service.send_task_notification,
                task
            )
        
        return {"status": "processed"}
        
    except Exception as e:
        print(f"❌ Error processing WhatsApp message: {e}")
        await task_service.log_failure(str(e), from_number)
        return {"status": "error", "message": str(e)}


@app.post("/api/twilio/sms-inbound")
async def twilio_sms_inbound(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Twilio webhook for inbound SMS
    """
    form_data = await request.form()
    from_number = form_data.get("From", "")
    to_number = form_data.get("To", "")
    message_body = form_data.get("Body", "")
    
    # Lookup business
    business = await auth_service.get_business_by_phone(to_number)
    business_id = business.id if business else "system"
    
    print(f"📱 SMS for {business_id} from {from_number}: {message_body}")
    
    try:
        # Extract intent from SMS
        intent_result = await intent_service.extract_intent(message_body)
        
        # Create task
        task = await task_service.create_task(
            intent=intent_result["intent"],
            issue=intent_result["issue"],
            urgency=intent_result["urgency"],
            business_id=business_id,
            location=intent_result.get("location"),
            preferred_time=intent_result.get("preferred_time"),
            confidence=intent_result["confidence"],
            customer_phone=from_number,
            transcript=message_body
        )
        
        # Send SMS confirmation
        background_tasks.add_task(
            send_sms_confirmation,
            from_number,
            task
        )
        
        # Notify operations team
        background_tasks.add_task(
            task_service.send_task_notification,
            task
        )
        
        return {"status": "processed"}
        
    except Exception as e:
        print(f"❌ Error processing SMS: {e}")
        await task_service.log_failure(str(e), from_number)
        return {"status": "error", "message": str(e)}


# ============================================
# Helper Functions for Twilio Processing
# ============================================

async def process_voice_recording(
    recording_url: str,
    caller_number: str,
    recording_sid: str,
    business_id: str
):
    """Background task to process voice recording"""
    try:
        # Transcribe
        transcript = await voice_service.transcribe_audio(recording_url + ".mp3")
        
        # Extract intent
        intent_result = await intent_service.extract_intent(transcript)
        
        # Create task
        task = await task_service.create_task(
            intent=intent_result["intent"],
            issue=intent_result["issue"],
            urgency=intent_result["urgency"],
            business_id=business_id,
            location=intent_result.get("location"),
            preferred_time=intent_result.get("preferred_time"),
            confidence=intent_result["confidence"],
            customer_phone=caller_number,
            transcript=transcript
        )
        
        # Send confirmation to customer
        from app.services.twilio_service import TwilioService
        twilio = TwilioService()
        await twilio.send_customer_confirmation(
            caller_number,
            task,
            channel="sms"
        )
        
        # Notify operations team
        await task_service.send_task_notification(task)
        
        print(f"✅ Recording processed, task created: {task['id']}")
        
    except Exception as e:
        print(f"❌ Failed to process recording: {e}")
        await task_service.log_failure(str(e), caller_number)


async def send_whatsapp_confirmation(customer_phone: str, task: Dict):
    """Send WhatsApp confirmation to customer"""
    from app.services.twilio_service import TwilioService
    
    twilio = TwilioService()
    await twilio.send_customer_confirmation(
        customer_phone,
        task,
        language="en",  # TODO: Detect language from transcript
        channel="whatsapp"
    )


async def send_sms_confirmation(customer_phone: str, task: Dict):
    """Send SMS confirmation to customer"""
    from app.services.twilio_service import TwilioService
    
    twilio = TwilioService()
    await twilio.send_customer_confirmation(
        customer_phone,
        task,
        language="en",
        channel="sms"
    )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
