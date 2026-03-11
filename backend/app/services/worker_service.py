"""
Worker Service - Manages workers/service providers
Handles worker CRUD, assignment, and availability tracking
"""
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import select, func, desc, or_
from app.database import AsyncSessionLocal, WorkerDB, TaskDB
from ..utils.safe_print import safe_print as print


class WorkerService:
    """Service for managing workers and task assignments"""
    
    async def create_worker(
        self,
        name: str,
        phone: str,
        skills: List[str],
        business_id: str,
        max_tasks: int = 5
    ) -> Dict:
        """Create a new worker"""
        
        async with AsyncSessionLocal() as session:
            # Check if phone already exists for this business
            result = await session.execute(
                select(WorkerDB).where(
                    WorkerDB.phone == phone,
                    WorkerDB.business_id == business_id
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                raise ValueError(f"Worker with phone {phone} already exists")
            
            worker = WorkerDB(
                id=str(uuid.uuid4()),
                business_id=business_id,
                name=name,
                phone=phone,
                skills=json.dumps(skills),
                status="available",
                current_tasks=0,
                max_tasks=max_tasks,
                rating=None,
                total_jobs=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(worker)
            await session.commit()
            await session.refresh(worker)
            
            return self._worker_to_dict(worker)
    
    async def get_workers(
        self,
        business_id: str,
        status: Optional[str] = None,
        skill: Optional[str] = None
    ) -> List[Dict]:
        """Get all workers with optional filters"""
        
        async with AsyncSessionLocal() as session:
            query = select(WorkerDB).where(WorkerDB.business_id == business_id).order_by(WorkerDB.name)
            
            if status:
                query = query.where(WorkerDB.status == status)
            
            result = await session.execute(query)
            workers = result.scalars().all()
            
            # Filter by skill if provided
            if skill:
                workers = [
                    w for w in workers
                    if skill in json.loads(w.skills)
                ]
            
            return [self._worker_to_dict(w) for w in workers]
    
    async def get_worker(self, worker_id: str) -> Optional[Dict]:
        """Get specific worker by ID"""
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WorkerDB).where(WorkerDB.id == worker_id)
            )
            worker = result.scalar_one_or_none()
            
            if not worker:
                return None
            
            return self._worker_to_dict(worker)
    
    async def update_worker(
        self,
        worker_id: str,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        skills: Optional[List[str]] = None,
        status: Optional[str] = None,
        max_tasks: Optional[int] = None
    ) -> Optional[Dict]:
        """Update worker details"""
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WorkerDB).where(WorkerDB.id == worker_id)
            )
            worker = result.scalar_one_or_none()
            
            if not worker:
                return None
            
            if name:
                worker.name = name
            if phone:
                worker.phone = phone
            if skills:
                worker.skills = json.dumps(skills)
            if status:
                worker.status = status
            if max_tasks is not None:
                worker.max_tasks = max_tasks
            
            worker.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(worker)
            
            return self._worker_to_dict(worker)
    
    async def delete_worker(self, worker_id: str) -> bool:
        """Delete a worker"""
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WorkerDB).where(WorkerDB.id == worker_id)
            )
            worker = result.scalar_one_or_none()
            
            if not worker:
                return False
            
            await session.delete(worker)
            await session.commit()
            
            return True
    
    async def assign_task_to_worker(
        self,
        task_id: str,
        worker_id: str
    ) -> Optional[Dict]:
        """Assign a task to a worker"""
        
        async with AsyncSessionLocal() as session:
            # Get worker
            worker_result = await session.execute(
                select(WorkerDB).where(WorkerDB.id == worker_id)
            )
            worker = worker_result.scalar_one_or_none()
            
            if not worker:
                raise ValueError("Worker not found")
            
            # Get task
            task_result = await session.execute(
                select(TaskDB).where(TaskDB.id == task_id)
            )
            task = task_result.scalar_one_or_none()
            
            if not task:
                raise ValueError("Task not found")
            
            # Check if worker has capacity
            if worker.current_tasks >= worker.max_tasks:
                raise ValueError(f"Worker {worker.name} is at maximum capacity")
            
            # Assign task
            task.assigned_to = worker_id
            task.assigned_worker_name = worker.name
            task.status = "in_progress"
            task.updated_at = datetime.utcnow()
            
            # Update worker
            worker.current_tasks += 1
            if worker.current_tasks >= worker.max_tasks:
                worker.status = "busy"
            worker.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(task)
            
            # Send notification to worker
            from app.services.twilio_service import TwilioService
            twilio = TwilioService()
            
            message = f"""🔔 NEW TASK ASSIGNED

Issue: {task.issue}
Location: {task.location or 'N/A'}
Urgency: {task.urgency.upper()}
Customer: {task.customer_phone}

Please confirm or call customer ASAP.

Task ID: {task.id[:8]}"""
            
            await twilio.send_sms_notification(worker.phone, message)
            
            print(f"✅ Task {task_id[:8]} assigned to {worker.name}")
            
            return {
                "task_id": task.id,
                "worker_id": worker.id,
                "worker_name": worker.name,
                "status": task.status
            }
    
    async def auto_assign_task(
        self,
        task_id: str
    ) -> Optional[Dict]:
        """Auto-assign task to best available worker"""
        
        async with AsyncSessionLocal() as session:
            # Get task
            task_result = await session.execute(
                select(TaskDB).where(TaskDB.id == task_id)
            )
            task = task_result.scalar_one_or_none()
            
            if not task:
                return None
            
            # Find available workers with matching skills
            workers_result = await session.execute(
                select(WorkerDB).where(
                    WorkerDB.status.in_(["available", "busy"])
                ).order_by(
                    WorkerDB.current_tasks,  # Prefer workers with fewer tasks
                    WorkerDB.rating.desc()    # Then by rating
                )
            )
            workers = workers_result.scalars().all()
            
            # Filter by skill match and capacity
            best_worker = None
            for worker in workers:
                skills = json.loads(worker.skills)
                if task.intent in skills and worker.current_tasks < worker.max_tasks:
                    best_worker = worker
                    break
            
            if not best_worker:
                print(f"⚠️ No available worker found for task {task_id[:8]}")
                return None
            
            # Assign to best worker
            return await self.assign_task_to_worker(task_id, best_worker.id)
    
    async def complete_task(
        self,
        task_id: str,
        rating: Optional[float] = None
    ):
        """Mark task as complete and update worker stats"""
        
        async with AsyncSessionLocal() as session:
            # Get task
            task_result = await session.execute(
                select(TaskDB).where(TaskDB.id == task_id)
            )
            task = task_result.scalar_one_or_none()
            
            if not task or not task.assigned_to:
                return
            
            # Get worker
            worker_result = await session.execute(
                select(WorkerDB).where(WorkerDB.id == task.assigned_to)
            )
            worker = worker_result.scalar_one_or_none()
            
            if not worker:
                return
            
            # Update worker stats
            worker.current_tasks = max(0, worker.current_tasks - 1)
            worker.total_jobs += 1
            
            if rating and worker.rating:
                # Update average rating
                worker.rating = (worker.rating * (worker.total_jobs - 1) + rating) / worker.total_jobs
            elif rating:
                worker.rating = rating
            
            if worker.current_tasks < worker.max_tasks:
                worker.status = "available"
            
            worker.updated_at = datetime.utcnow()
            
            await session.commit()
            
            print(f"✅ Task completed by {worker.name}, stats updated")
    
    async def get_worker_stats(self, business_id: str) -> Dict:
        """Get aggregated worker statistics for a specific business"""
        
        async with AsyncSessionLocal() as session:
            # Total workers
            total_result = await session.execute(
                select(func.count(WorkerDB.id)).where(WorkerDB.business_id == business_id)
            )
            total = total_result.scalar() or 0
            
            # Available workers
            available_result = await session.execute(
                select(func.count(WorkerDB.id)).where(
                    WorkerDB.business_id == business_id,
                    WorkerDB.status == "available"
                )
            )
            available = available_result.scalar() or 0
            
            # Busy workers
            busy_result = await session.execute(
                select(func.count(WorkerDB.id)).where(
                    WorkerDB.business_id == business_id,
                    WorkerDB.status == "busy"
                )
            )
            busy = busy_result.scalar() or 0
            
            # Total jobs done
            jobs_result = await session.execute(
                select(func.sum(WorkerDB.total_jobs)).where(WorkerDB.business_id == business_id)
            )
            total_jobs = jobs_result.scalar() or 0
            
            # Average rating
            rating_result = await session.execute(
                select(func.avg(WorkerDB.rating)).where(
                    WorkerDB.business_id == business_id,
                    WorkerDB.rating.isnot(None)
                )
            )
            avg_rating = rating_result.scalar() or 0
            
            return {
                "total_workers": total,
                "available": available,
                "busy": busy,
                "offline": total - available - busy,
                "total_jobsdone": total_jobs,
                "average_rating": round(avg_rating, 2) if avg_rating else None
            }
    
    def _worker_to_dict(self, worker: WorkerDB) -> Dict:
        """Convert worker DB model to dictionary"""
        return {
            "id": worker.id,
            "name": worker.name,
            "phone": worker.phone,
            "skills": json.loads(worker.skills),
            "status": worker.status,
            "current_tasks": worker.current_tasks,
            "max_tasks": worker.max_tasks,
            "rating": worker.rating,
            "total_jobs": worker.total_jobs,
            "created_at": worker.created_at,
            "updated_at": worker.updated_at
        }
