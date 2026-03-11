"""
Task Service - Handles task creation, updates, and orchestration
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import select, func, desc
from app.database import AsyncSessionLocal, TaskDB, CallLogDB, FailureLogDB
from ..utils.safe_print import safe_print as print


class TaskService:
    """Service for managing tasks and orchestration"""
    
    async def create_task(
        self,
        intent: str,
        issue: str,
        urgency: str,
        customer_phone: str,
        transcript: str,
        confidence: float,
        business_id: str,
        location: Optional[str] = None,
        preferred_time: Optional[str] = None,
        customer_name: Optional[str] = None
    ) -> Dict:
        """Create a new task from extracted intent"""
        
        async with AsyncSessionLocal() as session:
            task = TaskDB(
                id=str(uuid.uuid4()),
                business_id=business_id,
                intent=intent,
                issue=issue,
                urgency=urgency,
                location=location,
                preferred_time=preferred_time,
                confidence=confidence,
                status="new",
                customer_phone=customer_phone,
                customer_name=customer_name,
                transcript=transcript,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(task)
            await session.commit()
            await session.refresh(task)
            
            # Also log the call
            call_log = CallLogDB(
                id=str(uuid.uuid4()),
                business_id=business_id,
                phone_number=customer_phone,
                transcript=transcript,
                confidence_score=confidence,
                task_id=task.id,
                success=True,
                created_at=datetime.utcnow()
            )
            session.add(call_log)
            await session.commit()
            
            return {
                "task_id": task.id,
                "intent": task.intent,
                "issue": task.issue,
                "urgency": task.urgency,
                "location": task.location,
                "preferred_time": task.preferred_time,
                "confidence": task.confidence,
                "status": task.status,
                "customer_phone": task.customer_phone,
                "customer_name": task.customer_name,
                "transcript": task.transcript,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            }
    
    async def get_tasks(
        self,
        business_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get tasks with optional status filter"""
        
        async with AsyncSessionLocal() as session:
            query = select(TaskDB).where(TaskDB.business_id == business_id).order_by(desc(TaskDB.created_at)).limit(limit)
            
            if status:
                query = query.where(TaskDB.status == status)
            
            result = await session.execute(query)
            tasks = result.scalars().all()
            
            return [
                {
                    "task_id": task.id,
                    "intent": task.intent,
                    "issue": task.issue,
                    "urgency": task.urgency,
                    "location": task.location,
                    "preferred_time": task.preferred_time,
                    "confidence": task.confidence,
                    "status": task.status,
                    "customer_phone": task.customer_phone,
                    "created_at": task.created_at
                }
                for task in tasks
            ]
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a specific task by ID"""
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TaskDB).where(TaskDB.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                return None
            
            return {
                "task_id": task.id,
                "intent": task.intent,
                "issue": task.issue,
                "urgency": task.urgency,
                "location": task.location,
                "preferred_time": task.preferred_time,
                "confidence": task.confidence,
                "status": task.status,
                "customer_phone": task.customer_phone,
                "customer_name": task.customer_name,
                "transcript": task.transcript,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "escalation_reason": task.escalation_reason
            }
    
    async def update_task_status(self, task_id: str, status: str) -> Optional[Dict]:
        """Update task status"""
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TaskDB).where(TaskDB.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                return None
            
            task.status = status
            task.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(task)
            
            return {
                "task_id": task.id,
                "status": task.status,
                "updated_at": task.updated_at
            }
    
    async def escalate_task(self, task_id: str, reason: str) -> Optional[Dict]:
        """Escalate a task"""
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TaskDB).where(TaskDB.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                return None
            
            task.status = "escalated"
            task.escalation_reason = reason
            task.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(task)
            
            # Send notification (simulated for MVP)
            await self.send_escalation_notification(
                {"intent": task.intent, "issue": task.issue},
                reason,
                task.customer_phone
            )
            
            return {
                "task_id": task.id,
                "status": task.status,
                "escalation_reason": task.escalation_reason
            }
    
    async def get_dashboard_stats(self, business_id: str) -> Dict:
        """Get dashboard statistics including medical stats"""
        from app.database import AppointmentDB, PatientDB
        
        async with AsyncSessionLocal() as session:
            # Total calls
            total_calls_result = await session.execute(
                select(func.count(CallLogDB.id)).where(CallLogDB.business_id == business_id)
            )
            total_calls = total_calls_result.scalar() or 0
            
            # Tasks created
            tasks_created_result = await session.execute(
                select(func.count(TaskDB.id)).where(TaskDB.business_id == business_id)
            )
            tasks_created = tasks_created_result.scalar() or 0
            
            # Escalations
            escalations_result = await session.execute(
                select(func.count(TaskDB.id)).where(
                    TaskDB.business_id == business_id,
                    TaskDB.status == "escalated"
                )
            )
            escalations = escalations_result.scalar() or 0
            
            # Failures
            failures_result = await session.execute(
                select(func.count(FailureLogDB.id)).where(FailureLogDB.business_id == business_id)
            )
            failures = failures_result.scalar() or 0
            
            # Medical Stats
            appointments_result = await session.execute(
                select(func.count(AppointmentDB.id)).where(AppointmentDB.business_id == business_id)
            )
            appointments_count = appointments_result.scalar() or 0
            
            patients_result = await session.execute(
                select(func.count(PatientDB.id)).where(PatientDB.business_id == business_id)
            )
            patients_count = patients_result.scalar() or 0
            
            # Success rate
            success_rate = (tasks_created / total_calls * 100) if total_calls > 0 else 0
            
            return {
                "total_calls": total_calls,
                "tasks_created": tasks_created,
                "escalations": escalations,
                "failures": failures,
                "appointments_count": appointments_count,
                "patients_count": patients_count,
                "success_rate": round(success_rate, 2)
            }
    
    async def log_failure(self, error_message: str, phone_number: Optional[str] = None):
        """Log a system failure"""
        
        async with AsyncSessionLocal() as session:
            failure = FailureLogDB(
                id=str(uuid.uuid4()),
                error_message=error_message,
                phone_number=phone_number,
                created_at=datetime.utcnow()
            )
            session.add(failure)
            await session.commit()
    
    async def get_failures(self, limit: int = 50) -> List[Dict]:
        """Get failure logs"""
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(FailureLogDB)
                .order_by(desc(FailureLogDB.created_at))
                .limit(limit)
            )
            failures = result.scalars().all()
            
            return [
                {
                    "id": f.id,
                    "error_message": f.error_message,
                    "phone_number": f.phone_number,
                    "created_at": f.created_at
                }
                for f in failures
            ]
    
    async def send_task_notification(self, task: Dict):
        """Send notification about new task using Twilio (SMS/WhatsApp)"""
        from app.services.twilio_service import TwilioService
        import os
        
        # Log to console
        print(f"📱 NOTIFICATION: New {task['urgency']} task created")
        print(f"   Intent: {task['intent']}")
        print(f"   Issue: {task['issue']}")
        print(f"   Customer: {task['customer_phone']}")
        
        # Send real notification via Twilio
        twilio = TwilioService()
        notification_phone = os.getenv("ESCALATION_PHONE", "")
        notification_whatsapp = os.getenv("ESCALATION_WHATSAPP", "")
        
        # Try WhatsApp first, fall back to SMS
        if notification_whatsapp:
            await twilio.send_task_notification(task, notification_whatsapp, channel="whatsapp")
        elif notification_phone:
            await twilio.send_task_notification(task, notification_phone, channel="sms")
    
    async def send_escalation_notification(
        self,
        intent_result: Dict,
        reason: str,
        phone_number: str
    ):
        """Send escalation notification using Twilio (SMS/WhatsApp)"""
        from app.services.twilio_service import TwilioService
        import os
        
        # Log to console
        print(f"🚨 ESCALATION ALERT")
        print(f"   Reason: {reason}")
        print(f"   Customer: {phone_number}")
        print(f"   Details: {intent_result}")
        
        # Send real notification via Twilio
        twilio = TwilioService()
        notification_phone = os.getenv("ESCALATION_PHONE", "")
        notification_whatsapp = os.getenv("ESCALATION_WHATSAPP", "")
        
        task_data = {
            "intent": intent_result.get("intent", "Unknown"),
            "issue": intent_result.get("issue", "Unknown"),
            "customer_phone": phone_number,
            "confidence": intent_result.get("confidence", 0)
        }
        
        # Try WhatsApp first (preferred for escalations)
        if notification_whatsapp:
            await twilio.send_escalation_notification(
                task_data, reason, notification_whatsapp, channel="whatsapp"
            )
        elif notification_phone:
            await twilio.send_escalation_notification(
                task_data, reason, notification_phone, channel="sms"
            )
