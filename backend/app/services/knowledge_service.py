import json
from typing import Dict, List, Optional
from sqlalchemy import select
from ..database import AsyncSessionLocal, UserDB, DoctorDB

class KnowledgeService:
    """
    RAG-Lite Service for Clinic Knowledge.
    Handles storage and retrieval of clinic-specific FAQs, hours, and policies.
    """
    
    def __init__(self, db_session=None):
        self.db = db_session

    async def get_clinic_context(self, business_id: str) -> str:
        """
        Builds a text context of clinic-specific information for the LLM.
        """
        async with AsyncSessionLocal() as db:
            from ..database import ClinicKnowledgeDB
            # 1. Get basic business info
            result = await db.execute(select(UserDB).where(UserDB.id == business_id))
            business = result.scalars().first()
            
            if not business:
                return "Unknown Clinic"

            # 2. Get doctors list
            doc_result = await db.execute(select(DoctorDB).where(DoctorDB.business_id == business_id))
            doctors = doc_result.scalars().all()
            doc_list = ", ".join([f"{d.name} ({d.specialization})" for d in doctors])

            # 3. Get all knowledge items
            kn_result = await db.execute(
                select(ClinicKnowledgeDB).where(ClinicKnowledgeDB.business_id == business_id)
            )
            knowledge_items = kn_result.scalars().all()
            
            # Group by category
            hours = [f"{k.key}: {k.value}" for k in knowledge_items if k.category == 'hours']
            policies = [f"- {k.value}" for k in knowledge_items if k.category == 'policy']
            faqs = [f"Q: {k.key} A: {k.value}" for k in knowledge_items if k.category == 'faq']
            general = {k.key: k.value for k in knowledge_items if k.category == 'general'}

            # 4. Build context string
            context = f"""
            CLINIC NAME: {business.business_name}
            AVAILABLE DOCTORS: {doc_list}
            ADDRESS: {general.get('address', '123 Medical Dr, Clinical Heights')}
            CONTACT: {general.get('phone', business.twilio_phone or 'Not listed')}
            
            BUSINESS HOURS:
            {chr(10).join(hours) if hours else 'Mon-Fri 9:00 AM - 5:00 PM'}
            
            POLICIES: 
            {chr(10).join(policies) if policies else '- Appointments must be cancelled 24 hours in advance.'}
            
            FREQUENTLY ASKED QUESTIONS:
            {chr(10).join(faqs) if faqs else 'No specific FAQs listed.'}
            """
            
            return context.strip()

    async def search_faqs(self, query: str, business_id: str) -> str:
        """
        Retrieves relevant knowledge base items for a query.
        (Future: Use pgvector for semantic search)
        """
        async with AsyncSessionLocal() as db:
            from ..database import ClinicKnowledgeDB
            # Simple keyword match for now
            result = await db.execute(
                select(ClinicKnowledgeDB).where(
                    ClinicKnowledgeDB.business_id == business_id,
                    ClinicKnowledgeDB.category == 'faq',
                    (ClinicKnowledgeDB.key.ilike(f"%{query}%") | ClinicKnowledgeDB.value.ilike(f"%{query}%"))
                )
            )
            faqs = result.scalars().all()
            if not faqs:
                return "I'm sorry, I don't have specific information on that. Would you like to speak with a representative?"
            
            return "\n".join([f"Q: {f.key} A: {f.value}" for f in faqs])
