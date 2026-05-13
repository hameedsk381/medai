import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .appointment_service import AppointmentService
from .task_service import TaskService
from .knowledge_service import KnowledgeService
from ..utils.safe_print import safe_print as print

class ToolExecutor:
    """Executes structured tool calls from the AgentService during voice interaction"""
    
    def __init__(self, db_session: AsyncSession, business_id: str, caller_phone: str = "Unknown"):
        self.db = db_session
        self.business_id = business_id
        self.caller_phone = caller_phone
        self.appointment_service = AppointmentService(db_session)
        self.knowledge_service = KnowledgeService(db_session)
        self.task_service = TaskService()
        
    async def execute(self, tool_call: Any) -> Dict[str, Any]:
        """Route tool calls for execution. Supports both Gemini and OpenAI/Groq formats."""
        # Gemini format: function_call with .name and .args (dict)
        if hasattr(tool_call, "name") and hasattr(tool_call, "args"):
            name = tool_call.name
            args = dict(tool_call.args) if tool_call.args else {}
            tool_call_id = getattr(tool_call, "id", "")
        # OpenAI/Groq format: tool_call with .function.name and .function.arguments (JSON string)
        elif hasattr(tool_call, "function") and getattr(tool_call, "function", None) is not None:
            function = tool_call.function
            name = function.name
            args = json.loads(function.arguments)
            tool_call_id = getattr(tool_call, "id", "")
        # Dict format fallback
        elif isinstance(tool_call, dict):
            name = tool_call.get("function", {}).get("name", tool_call.get("name", "unknown"))
            raw_args = tool_call.get("function", {}).get("arguments", tool_call.get("args", "{}"))
            args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
            tool_call_id = tool_call.get("id", "")
        else:
            return {"tool_call_id": "", "output": json.dumps({"status": "error", "message": "Unrecognized tool_call format"})}
        
        print(f"🛠️ Executing tool: {name} (Args: {args})")
        
        if name == "check_doctor_availability":
            result = await self.appointment_service.check_availability(
                doctor_name=args.get("doctor_name", ""),
                preferred_date=args.get("preferred_date", ""),
                business_id=self.business_id
            )
            return {"tool_call_id": tool_call_id, "output": json.dumps(result)}
            
        elif name == "book_appointment":
            result = await self.appointment_service.book_appointment(
                patient_name=args.get("patient_name", ""),
                patient_phone=args.get("patient_phone", self.caller_phone),
                doctor_name=args.get("doctor_name", ""),
                date=args.get("date", ""),
                time=args.get("time", ""),
                business_id=self.business_id
            )
            return {"tool_call_id": tool_call_id, "output": json.dumps(result)}
            
        elif name == "create_triage_task":
            result = await self.task_service.create_task(
                intent=args.get("intent", "General Inquiry"),
                issue=args.get("issue", "Patient request from voice call"),
                urgency=args.get("urgency", "low"),
                customer_phone=self.caller_phone,
                transcript="Created via MedVoice AI Realtime Pipeline",
                confidence=1.0,
                business_id=self.business_id
            )
            return {"tool_call_id": tool_call_id, "output": json.dumps(result)}
            
        elif name == "get_clinic_info":
            result = await self.knowledge_service.search_faqs(
                query=args.get("query", ""),
                business_id=self.business_id
            )
            return {"tool_call_id": tool_call_id, "output": json.dumps({"info": result})}
            
        return {"tool_call_id": tool_call_id, "output": json.dumps({"status": "error", "message": "Unknown tool"})}
