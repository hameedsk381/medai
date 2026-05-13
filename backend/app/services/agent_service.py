import os
import json
import re
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from ..models import ServiceIntent
from ..utils.safe_print import safe_print as print

class AgentService:
    """Conversational AI brain for MedVoice AI — powered by Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("WARNING: GEMINI_API_KEY not set. Agent will not work.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            print("✅ Agent service (Gemini) initialized")
            
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

    def _get_tool_declarations(self) -> list:
        """Get Gemini-format function declarations for all available tools"""
        return [
            {
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
            },
            {
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
            },
            {
                "name": "get_clinic_info",
                "description": "Get general clinic information, FAQs, hours, and policies",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The specific topic to lookup"}
                    },
                    "required": ["query"]
                }
            },
            {
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
        ]

    def _convert_history_to_gemini(self, history: List[Dict[str, str]]) -> List[types.Content]:
        """Convert OpenAI-style message history to Gemini Contents format"""
        contents = []
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Gemini uses "user" and "model" roles (not "assistant")
            # "tool" messages are handled separately
            if role == "assistant":
                role = "model"
            elif role == "tool":
                # Tool results are sent as user-role function responses
                # Skip for now or wrap them appropriately
                role = "user"
            elif role == "system":
                # System messages are handled via system_instruction config
                continue
            
            if content:
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part(text=content)]
                ))
        return contents

    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[list] = None
    ) -> Any:
        """Call Gemini with tool definitions"""
        if not self.client:
            return None
        
        try:
            # Separate system message from history
            system_instruction = None
            chat_messages = []
            for msg in messages:
                if msg.get("role") == "system":
                    system_instruction = msg.get("content", "")
                else:
                    chat_messages.append(msg)
            
            contents = self._convert_history_to_gemini(chat_messages)
            
            # Build config
            config_kwargs = {
                "temperature": 0.1,
                "max_output_tokens": 512,
            }
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction
            if tools:
                config_kwargs["tools"] = [types.Tool(function_declarations=tools)]
            
            config = types.GenerateContentConfig(**config_kwargs)
            
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=config,
            )
            return response
        except Exception as e:
            print(f"❌ Gemini LLM Error: {e}")
            return None

    async def chat_completion_stream(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[list] = None
    ) -> Any:
        """Call Gemini with streaming enabled"""
        if not self.client:
            return
        
        try:
            system_instruction = None
            chat_messages = []
            for msg in messages:
                if msg.get("role") == "system":
                    system_instruction = msg.get("content", "")
                else:
                    chat_messages.append(msg)
            
            contents = self._convert_history_to_gemini(chat_messages)
            
            config_kwargs = {
                "temperature": 0.1,
                "max_output_tokens": 512,
            }
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction
            if tools:
                config_kwargs["tools"] = [types.Tool(function_declarations=tools)]
            
            config = types.GenerateContentConfig(**config_kwargs)
            
            async for chunk in await self.client.aio.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=contents,
                config=config,
            ):
                yield chunk
        except Exception as e:
            print(f"❌ Gemini LLM Stream Error: {e}")

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
        
        # Get tool declarations
        tool_declarations = self._get_tool_declarations()
        
        response = await self.chat_completion(messages, tools=tool_declarations)
        
        if not response:
            return {
                "role": "assistant",
                "content": "I apologize, I'm having trouble processing right now. Could you please repeat that?",
                "tool_calls": None
            }
        
        # Parse Gemini response
        candidate = response.candidates[0]
        text_content = ""
        tool_calls = []
        
        for part in candidate.content.parts:
            if part.text:
                text_content += part.text
            if part.function_call:
                # Convert Gemini function_call to a format compatible with ToolExecutor
                tool_calls.append(part.function_call)
        
        return {
            "role": "assistant",
            "content": self.format_for_voice(text_content) if text_content else None,
            "tool_calls": tool_calls if tool_calls else None
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
            
        try:
            full_content = ""
            async for chunk in self.chat_completion_stream(messages):
                # Gemini streaming chunks have candidates[0].content.parts
                if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                    for part in chunk.candidates[0].content.parts:
                        if part.text:
                            content = part.text
                            full_content += content
                            yield content
        except Exception as e:
            print(f"❌ Stream process error: {e}")
