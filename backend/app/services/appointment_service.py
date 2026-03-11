import os
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import PatientDB, DoctorDB, AppointmentDB
from ..utils.safe_print import safe_print as print

class AppointmentService:
    """Handles appointment-related database operations for MedVoice AI"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        
    async def get_patient_by_phone(self, phone: str, business_id: str) -> Optional[PatientDB]:
        """Find a patient by their phone number within a business tenant"""
        result = await self.db.execute(
            select(PatientDB).where(
                and_(PatientDB.phone == phone, PatientDB.business_id == business_id)
            )
        )
        return result.scalars().first()

    async def create_patient(self, name: str, phone: str, business_id: str) -> PatientDB:
        """Create a new patient record"""
        new_patient = PatientDB(
            id=str(uuid.uuid4()),
            business_id=business_id,
            name=name,
            phone=phone
        )
        self.db.add(new_patient)
        await self.db.commit()
        await self.db.refresh(new_patient)
        return new_patient

    async def get_doctor_by_name(self, name: str, business_id: str) -> Optional[DoctorDB]:
        """Find a doctor by name within a business tenant"""
        # Exact name match initially, can be fuzzy later
        result = await self.db.execute(
            select(DoctorDB).where(
                and_(DoctorDB.name.ilike(f"%{name}%"), DoctorDB.business_id == business_id)
            )
        )
        return result.scalars().first()

    async def check_availability(self, doctor_name: str, preferred_date: str, business_id: str) -> Dict[str, Any]:
        """
        Check for available time slots for a doctor on a specific date.
        Currently uses a mock list of slots for Phase 2.
        """
        doctor = await self.get_doctor_by_name(doctor_name, business_id)
        if not doctor:
            return {"status": "error", "message": f"Doctor {doctor_name} not found."}
            
        # Simplified simulation of slots: 10:00 AM, 11:30 AM, 2:00 PM, 4:30 PM
        # In a real system, you'd check AppointmentDB for existing bookings.
        
        # Check for existing appointments to find taken slots
        available_slots = ["10:00 AM", "11:30 AM", "02:00 PM", "04:30 PM"]
        
        # In production this would query DB:
        # result = await self.db.execute(select(AppointmentDB).where(and_(...)))
        
        return {
            "status": "success",
            "doctor_id": doctor.id,
            "doctor_name": doctor.name,
            "date": preferred_date,
            "available_slots": available_slots
        }

    async def book_appointment(
        self, 
        patient_name: str, 
        patient_phone: str, 
        doctor_name: str, 
        date: str, 
        time: str, 
        business_id: str
    ) -> Dict[str, Any]:
        """Book a new appointment slot for a patient"""
        # 1. Get or create patient
        patient = await self.get_patient_by_phone(patient_phone, business_id)
        if not patient:
            patient = await self.create_patient(patient_name, patient_phone, business_id)
            
        # 2. Find doctor
        doctor = await self.get_doctor_by_name(doctor_name, business_id)
        if not doctor:
            # Fallback - If no doctor selected by AI, just pick one for the demo
            result = await self.db.execute(select(DoctorDB).where(DoctorDB.business_id == business_id))
            doctor = result.scalars().first()
            
        if not doctor:
            return {"status": "error", "message": f"Doctor {doctor_name} not found."}
            
        # 3. Create appointment
        try:
            appointment = AppointmentDB(
                id=str(uuid.uuid4()),
                business_id=business_id,
                patient_id=patient.id,
                doctor_id=doctor.id,
                date=datetime.now(), # In production, use parsed date
                time_slot=time,
                status="scheduled",
                created_via="ai_call"
            )
            
            self.db.add(appointment)
            await self.db.commit()
            await self.db.refresh(appointment)
            
            # TRIGGER SMS CONFIRMATION (Phase 3 QoL)
            try:
                from .twilio_service import TwilioService
                twilio = TwilioService()
                sms_message = f"Confirmed! Your appointment with {doctor.name} is scheduled for {date} at {time}. See you at MedClinic!"
                # Use background task in production, direct for this demo refinement
                await twilio.send_sms(patient_phone, sms_message)
                print(f"📲 Appointment SMS sent to {patient_phone}")
            except Exception as sms_err:
                print(f"⚠️ Failed to send appointment SMS: {sms_err}")

            return {
                "status": "success",
                "appointment_id": appointment.id,
                "patient_name": patient.name,
                "doctor_name": doctor.name,
                "date": date,
                "time": time
            }
        except Exception as e:
            await self.db.rollback()
            return {"status": "error", "message": str(e)}

    async def get_all_doctors(self, business_id: str) -> List[DoctorDB]:
        """Get all doctors for a business"""
        result = await self.db.execute(
            select(DoctorDB).where(DoctorDB.business_id == business_id)
        )
        return result.scalars().all()

    async def get_all_appointments(self, business_id: str) -> List[AppointmentDB]:
        """Get all appointments for a business"""
        result = await self.db.execute(
            select(AppointmentDB).where(AppointmentDB.business_id == business_id).order_by(AppointmentDB.date.desc())
        )
        return result.scalars().all()

    async def get_all_patients(self, business_id: str) -> List[PatientDB]:
        """Get all patients for a business"""
        result = await self.db.execute(
            select(PatientDB).where(PatientDB.business_id == business_id).order_by(PatientDB.name)
        )
        return result.scalars().all()

    async def create_doctor(self, name: str, specialization: str, phone: str, business_id: str) -> DoctorDB:
        """Add a new doctor record"""
        new_doctor = DoctorDB(
            id=str(uuid.uuid4()),
            business_id=business_id,
            name=name,
            specialization=specialization,
            phone=phone,
            status="active"
        )
        self.db.add(new_doctor)
        await self.db.commit()
        await self.db.refresh(new_doctor)
        return new_doctor
