import unittest

from app.services.agent_service import AgentService
from app.services.realtime_pipeline import RealtimeVoicePipeline
from app.services.twilio_service import TwilioService


class FunctionCall:
    def __init__(self, name: str):
        self.name = name


class ToolCallObject:
    def __init__(self, name: str):
        self.function = FunctionCall(name)


class VoicePipelineSmokeTests(unittest.TestCase):
    def test_stream_twiml_includes_caller_parameter(self):
        twiml = TwilioService().generate_stream_twiml(
            host="example.com",
            business_id="clinic-1",
            is_outbound=True,
            caller_phone="+15551234567"
        )

        self.assertIn('url="wss://example.com/voice-stream"', twiml)
        self.assertIn('name="business_id" value="clinic-1"', twiml)
        self.assertIn('name="is_outbound" value="true"', twiml)
        self.assertIn('name="caller" value="+15551234567"', twiml)

    def test_tool_call_name_handles_sdk_object(self):
        tool_call = ToolCallObject("book_appointment")
        self.assertEqual(
            RealtimeVoicePipeline.get_tool_call_name(tool_call),
            "book_appointment"
        )

    def test_tool_call_name_handles_dict(self):
        tool_call = {"function": {"name": "get_clinic_info"}}
        self.assertEqual(
            RealtimeVoicePipeline.get_tool_call_name(tool_call),
            "get_clinic_info"
        )

    def test_agent_formats_voice_output(self):
        formatted = AgentService.format_for_voice("Sure\n- We are open 9 to 5; call us back if needed")
        self.assertEqual(formatted, "Sure We are open 9 to 5. Call us back if needed.")


if __name__ == "__main__":
    unittest.main()
