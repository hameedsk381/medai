import os
import json
import re
from typing import List, Dict, Any, Optional
from groq import AsyncGroq
from ..models import ServiceIntent
from ..utils.safe_print import safe_print as print

class AgentService:
    """Conversational AI brain for MedVoice AI"""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("WARNING: GROQ_API_KEY not set. Agent will not work.")
            self.client = None
        else:
            self.client = AsyncGroq(api_key=self.api_key)
            print("✅ Agent service (Groq) initialized")
            
    def get_system_prompt(self, clinic_name: str = "Our Clinic", clinic_context: str = "") -> str:
        """Get the medical-specific system prompt with dynamic clinic context"""
        return f"""
        You are an expert AI medical receptionist for {clinic_name}. Your name is MedVoice AI.
        Your goal is to be professional, empathetic, and efficient.
        
        CLINIC CONTEXT:
        {clinic_context}
        
        YOUR CORE TASKS:
        1. Book appointments for patients.
        2. Check appointment status/details.
        3. Handle prescription renewal requests by creating a triage task.
        4. Answer clinic-related FAQs (hours, location, doctors).
        5. Create a triage task for any medical concerns that need nurse review.
        6. Escalate to a human for emergencies or complex medical questions.
        
        RULES:
        - Identify yourself as the MedVoice AI receptionist.
        - NEVER give medical advice. If asked, say: "I am an AI assistant and cannot provide medical advice. Please consult with our medical staff directly for health-related concerns."
        - ALWAYS collect: Patient Name, Preferred Doctor, and Preferred Date/Time for bookings.
        - For medical issues or refill requests, use `create_triage_task` to notify the medical staff.
        - If an emergency is detected (chest pain, severe bleeding, etc.), IMMEDIATELY say: "This sounds like an emergency. Please hang up and dial 911 or visit the nearest emergency room immediately, or stay on the line and I will transfer you to our triage team."
        - Keep responses concise for voice interaction.
        - Use short, natural sentences with clear punctuation.
        - Avoid bullet points, markdown, or long run-on answers.
        - Prefer 1 to 3 sentences unless you are confirming multiple details.
        - Be polite and reassuring.
        
        AVAILABLE TOOLS:
        - `check_doctor_availability(doctor_name, preferred_date)`
        - `book_appointment(patient_name, patient_phone, doctor_name, date, time)`
        - `create_triage_task(intent, issue, urgency)`: Use this for any non-appointment medical requests like refills, symptoms, or nurse callbacks.
        - `get_clinic_info(query)`: Use this to search for FAQs or clinic details if not in context.
        """

    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """Call the LLM with tool definitions"""
        if not self.client:
            return None
        
        try:
            return await self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.1, # Low temperature for medical consistency
                max_tokens=512   # Increased for better tool reasoning
            )
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            # Try fallback model
            try:
                return await self.client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.1,
                    max_tokens=512
                )
            except Exception as e2:
                print(f"❌ LLM Fallback Error: {e2}")
                return None

    async def chat_completion_stream(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """Call the LLM with streaming enabled"""
        if not self.client:
            return
        
        try:
            stream = await self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.1,
                max_tokens=512,
                stream=True
            )
            async for chunk in stream:
                yield chunk
        except Exception as e:
            print(f"❌ LLM Stream Error: {e}")

    @staticmethod
    def format_for_voice(content: Optional[str]) -> str:
        """Normalize model output into a TTS-friendly spoken reply."""
        if not content:
            return ""

        formatted = content.replace("\r", " ").replace("\n", " ")
        formatted = re.sub(r"\s*[•\-]\s*", " ", formatted)
        formatted = re.sub(r"\s*;\s*", ". ", formatted)
        formatted = re.sub(r"\s{2,}", " ", formatted).strip()
        formatted = re.sub(r"([.!?])\s+([a-z])", lambda match: f"{match.group(1)} {match.group(2).upper()}", formatted)

        if formatted and formatted[-1] not in ".!?":
            formatted += "."

        return formatted

    async def process_turn(
        self, 
        user_text: str, 
        history: List[Dict[str, str]], 
        clinic_name: str = "MedClinic",
        clinic_context: str = ""
    ) -> Dict[str, Any]:
        """
        Process a single turn of the conversation.
        """
        messages = [
            {"role": "system", "content": self.get_system_prompt(clinic_name, clinic_context)},
            *history
        ]

        if user_text and user_text.strip():
            messages.append({"role": "user", "content": user_text})
        
        # Define tools for the model
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "check_doctor_availability",
                    "description": "Check if a doctor is available on a specific date",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doctor_name": {"type": "string"},
                            "preferred_date": {"type": "string", "description": "e.g. 2024-03-25 or 'tomorrow'"}
                        },
                        "required": ["doctor_name", "preferred_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "book_appointment",
                    "description": "Book a new appointment slot for a patient",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "patient_name": {"type": "string"},
                            "doctor_name": {"type": "string"},
                            "date": {"type": "string"},
                            "time": {"type": "string"}
                        },
                        "required": ["patient_name", "doctor_name", "date", "time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_clinic_info",
                    "description": "Get general clinic information, FAQs, hours, and policies",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The specific topic to lookup"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_triage_task",
                    "description": "Create a medical triage task for nurse review (prescription refills, symptoms, follow-ups)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "intent": {
                                "type": "string", 
                                "enum": ["Prescription Renewal", "Symptom Triage", "Test Results Inquiry", "Nurse Callback", "General Inquiry"],
                                "description": "The category of the triage request"
                            },
                            "issue": {"type": "string", "description": "Specific details of the patient's concern or request"},
                            "urgency": {
                                "type": "string", 
                                "enum": ["low", "medium", "high", "critical"],
                                "description": "The estimated urgency of the request"
                            }
                        },
                        "required": ["intent", "issue", "urgency"]
                    }
                }
            }
        ]
        
        response = await self.chat_completion(messages, tools=tools)
        
        if not response:
            return {
                "role": "assistant",
                "content": "I apologize, I'm having trouble processing right now. Could you please repeat that?",
                "tool_calls": None
            }
        
        choice = response.choices[0].message
        
        return {
            "role": "assistant",
            "content": self.format_for_voice(choice.content),
            "tool_calls": choice.tool_calls
        }

    async def process_turn_stream(
        self, 
        user_text: str, 
        history: List[Dict[str, str]], 
        clinic_name: str = "MedClinic",
        clinic_context: str = ""
    ):
        """
        Process a single turn and yield text chunks as they arrive.
        """
        messages = [
            {"role": "system", "content": self.get_system_prompt(clinic_name, clinic_context)},
            *history
        ]
        if user_text and user_text.strip():
            messages.append({"role": "user", "content": user_text})
            
        # We'll skip tools for the streaming part for extreme speed, 
        # or handle them if detected. For now, focus on conversational speed.
        
        try:
            full_content = ""
            async for chunk in self.chat_completion_stream(messages):
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield content
        except Exception as e:
            print(f"❌ Stream process error: {e}")
