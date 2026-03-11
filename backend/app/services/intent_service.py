"""
Intent Service - Extracts intent and entities from voice transcriptions
Uses Groq API for ultra-fast inference with Llama 3 models
"""
import os
import json
from typing import Dict, Optional
from groq import AsyncGroq
from ..utils.safe_print import safe_print as print


class IntentService:
    """Service for extracting intent and entities from transcriptions"""
    
    def __init__(self):
        """Initialize the service with Groq client"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("WARNING: GROQ_API_KEY not set. Please add it to backend/.env")
            print("Get your free key at: https://console.groq.com/keys")
        self.client = AsyncGroq(api_key=api_key) if api_key else None
    
    SUPPORTED_INTENTS = [
        "Prescription Renewal",
        "Symptom Triage",
        "Test Results Inquiry",
        "Nurse Callback",
        "Booking Appointment",
        "General Inquiry",
        "Other"
    ]
    
    async def extract_intent(self, transcript: str) -> Dict:
        """
        Extract intent and entities from transcript using Groq (Llama 3)
        
        Returns:
            {
                "intent": str,
                "issue": str,
                "urgency": str (low/medium/high/critical),
                "location": str (optional),
                "preferred_time": str (optional),
                "confidence": float (0-1)
            }
        """
        
        # Check if client is initialized
        if not self.client:
            return {
                "intent": "Other",
                "issue": "API key not configured",
                "urgency": "medium",
                "location": None,
                "preferred_time": None,
                "confidence": 0.0
            }
        
        system_prompt = f"""You are an AI assistant for a medical clinic intake system.
Your job is to analyze patient voice transcripts and extract structured information.

Note: The transcript may include speaker labels like "SPEAKER_00" and "SPEAKER_01" if it is a phone call.

SUPPORTED MEDICAL CATEGORIES:
{', '.join(self.SUPPORTED_INTENTS)}

Extract the following:
1. Intent: Which medical workflow category does this relate to?
2. Issue: What is the specific problem, symptom, or request?
3. Urgency: How urgent is this? (low, medium, high, critical)
4. Location: Where is the patient located or which clinic branch? (extract if mentioned)
5. Preferred Time: When do they want an appointment or callback? (extract if mentioned)
6. Confidence: How confident are you in this extraction? (0.0 to 1.0)

URGENCY GUIDELINES:
- Critical: Emergency symptoms (chest pain, severe bleeding), call 911 immediately
- High: Severe discomfort or urgent medication refill needed today
- Medium: Moderate symptoms, needs attention within 1-2 days
- Low: Routine request, general inquiry, flexible appointment

Return ONLY a valid JSON object with these exact keys:
{{"intent", "issue", "urgency", "location", "preferred_time", "confidence"}}

If any field is not mentioned, use null for optional fields."""

        user_prompt = f"Customer transcript: {transcript}"
        
        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Ultra-fast Groq model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Low temperature for consistent extraction
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate and normalize
            if result["intent"] not in self.SUPPORTED_INTENTS:
                result["intent"] = "Other"
                result["confidence"] = max(0.0, result.get("confidence", 0.5) - 0.2)
            
            # Ensure confidence is in valid range
            result["confidence"] = max(0.0, min(1.0, result.get("confidence", 0.5)))
            
            # Normalize urgency
            if result.get("urgency", "").lower() not in ["low", "medium", "high", "critical"]:
                result["urgency"] = "medium"
            else:
                result["urgency"] = result["urgency"].lower()
            
            return result
            
        except Exception as e:
            # Fallback: return low-confidence result
            print(f"Intent extraction failed: {e}")
            return {
                "intent": "Other",
                "issue": transcript[:100],  # First 100 chars
                "urgency": "medium",
                "location": None,
                "preferred_time": None,
                "confidence": 0.3  # Low confidence triggers escalation
            }
    
    async def should_escalate(self, intent_result: Dict) -> tuple[bool, str]:
        """
        Determine if this should be escalated based on confidence and context
        
        Returns (should_escalate, reason)
        """
        confidence = intent_result.get("confidence", 0.0)
        threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
        
        if confidence < threshold:
            return True, f"Low confidence score: {confidence:.2f}"
        
        # Check for unclear intents
        if intent_result.get("intent") == "Other":
            return True, "Unable to categorize service type"
        
        # Check for missing critical info
        if not intent_result.get("issue") or len(intent_result.get("issue", "")) < 5:
            return True, "Insufficient problem description"
        
        return False, ""
