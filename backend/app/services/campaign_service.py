import uuid
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import WhatsAppCampaignDB, CampaignRecipientDB, PatientDB
from .twilio_service import TwilioService
from ..utils.safe_print import safe_print as print

class CampaignService:
    """Handles WhatsApp marketing/notification campaigns"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.twilio = TwilioService()
        
    async def create_campaign(
        self, 
        business_id: str, 
        name: str, 
        message_template: str, 
        recipient_phones: List[str]
    ) -> WhatsAppCampaignDB:
        """Create a new campaign and its recipients"""
        
        # Resolve 'all_patients' keyword
        if "all_patients" in recipient_phones:
            result = await self.db.execute(
                select(PatientDB.phone).where(PatientDB.business_id == business_id)
            )
            patients_phones = [row[0] for row in result.all()]
            # Remove the keyword and add the actual phones
            recipient_phones = [p for p in recipient_phones if p != "all_patients"]
            recipient_phones.extend(patients_phones)
            
        # Remove duplicates and empty strings
        recipient_phones = list(set([p.strip() for p in recipient_phones if p.strip()]))
        
        campaign = WhatsAppCampaignDB(
            id=str(uuid.uuid4()),
            business_id=business_id,
            name=name,
            message_template=message_template,
            status="pending",
            total_recipients=len(recipient_phones),
            success_count=0,
            failure_count=0
        )
        
        self.db.add(campaign)
        
        # Add individual recipients
        for phone in recipient_phones:
            recipient = CampaignRecipientDB(
                id=str(uuid.uuid4()),
                campaign_id=campaign.id,
                phone_number=phone,
                status="pending"
            )
            self.db.add(recipient)
            
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def run_campaign(self, campaign_id: str):
        """Execute the campaign by sending WhatsApp messages in background"""
        result = await self.db.execute(
            select(WhatsAppCampaignDB).where(WhatsAppCampaignDB.id == campaign_id)
        )
        campaign = result.scalars().first()
        if not campaign or campaign.status in ["sending", "completed"]:
            return
            
        campaign.status = "sending"
        await self.db.commit()
        
        # Get pending recipients
        result = await self.db.execute(
            select(CampaignRecipientDB).where(
                and_(
                    CampaignRecipientDB.campaign_id == campaign_id,
                    CampaignRecipientDB.status == "pending"
                )
            )
        )
        recipients = result.scalars().all()
        
        for recipient in recipients:
            try:
                # Add a small delay for rate limiting if needed, but Twilio handles most
                sid = await self.twilio.send_whatsapp_notification(
                    to_phone=recipient.phone_number,
                    message=campaign.message_template
                )
                
                if sid:
                    recipient.status = "sent"
                    recipient.message_sid = sid
                    campaign.success_count += 1
                else:
                    # In simulation mode, sid might be None but we can treat as success if no exception
                    if not self.twilio.client:
                        recipient.status = "sent"
                        recipient.message_sid = "simulated_whatsapp_sid"
                        campaign.success_count += 1
                    else:
                        recipient.status = "failed"
                        recipient.error_message = "Twilio failed to return SID"
                        campaign.failure_count += 1
                    
            except Exception as e:
                recipient.status = "failed"
                recipient.error_message = str(e)
                campaign.failure_count += 1
                
            recipient.sent_at = datetime.utcnow()
            await self.db.commit()
            
        campaign.status = "completed"
        campaign.sent_at = datetime.utcnow()
        await self.db.commit()

    async def get_campaigns(self, business_id: str) -> List[WhatsAppCampaignDB]:
        """List all campaigns for a business"""
        result = await self.db.execute(
            select(WhatsAppCampaignDB)
            .where(WhatsAppCampaignDB.business_id == business_id)
            .order_by(WhatsAppCampaignDB.created_at.desc())
        )
        return result.scalars().all()

    async def get_campaign_details(self, campaign_id: str) -> Optional[Dict]:
        """Get details and recipient status for a campaign"""
        result = await self.db.execute(
            select(WhatsAppCampaignDB).where(WhatsAppCampaignDB.id == campaign_id)
        )
        campaign = result.scalars().first()
        if not campaign:
            return None
            
        result = await self.db.execute(
            select(CampaignRecipientDB).where(CampaignRecipientDB.campaign_id == campaign_id)
        )
        recipients = result.scalars().all()
        
        return {
            "campaign": campaign,
            "recipients": recipients
        }
