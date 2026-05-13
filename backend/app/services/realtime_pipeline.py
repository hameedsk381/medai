import asyncio
import json
import os
import base64
import io
import uuid
import struct
import wave
from datetime import datetime
from typing import Callable, Optional
from .stt_service import STTService
from .tts_service import TTSService
from .agent_service import AgentService
from .tool_executor import ToolExecutor
from .knowledge_service import KnowledgeService
from .conversation_state import ConversationState
from ..database import AsyncSessionLocal
from ..utils.safe_print import safe_print as print

class RealtimeVoicePipeline:
    """Orchestrates the STT -> Agent -> TTS loop for a single call"""
    
    def __init__(self, websocket: any, business_id: str = "demo-clinic-1"):
        """
        Initialize the pipeline for a single WebSocket session (Twilio Media Stream)
        
        Args:
            websocket: Twilio Media Stream WebSocket connection
            business_id: The tenant ID for this clinic
        """
        self.websocket = websocket
        self.business_id = business_id
        self.stt = STTService()
        self.tts = TTSService()
        self.agent = AgentService()
        self.knowledge = KnowledgeService()
        self.state = ConversationState()
        
        # Audio state
        self.is_speaking = False
        self.last_audio_timestamp = 0
        self.stream_sid = None
        self.call_sid = None
        self.caller_phone = None
        
        # Audio silence detection
        self.silence_timer = None
        self.last_audio_recv_time = 0
        
        # Conversation state
        self.history = []
        self.clinic_context = ""
        self.utterance_transcript = ""
        self.is_final = False
        
        # Interruption handling
        self.tts_task = None
        self.is_agent_speaking = False
        
        # Outbound flow
        self.is_outbound = False
        
        # Language tracking
        self.detected_language = "en-IN"

    @staticmethod
    def get_tool_call_name(tool_call: any) -> str:
        """Normalize tool-call access across Gemini, OpenAI/Groq SDK objects and dict payloads."""
        # Gemini format: function_call has .name directly
        if hasattr(tool_call, "name") and tool_call.name:
            return str(tool_call.name)
        # OpenAI/Groq format: tool_call.function.name
        function = getattr(tool_call, "function", None)
        if function and getattr(function, "name", None):
            return str(function.name)
        if isinstance(tool_call, dict):
            return str(tool_call.get("name", tool_call.get("function", {}).get("name", "unknown_tool")))
        return "unknown_tool"

    async def start(self):
        """Start the realtime audio pipeline"""
        # Start STT session
        self.dg_connection = await self.stt.start_session(
            on_transcript=self.on_transcript
        )
        
        # Fetch initial clinic context
        self.clinic_context = await self.knowledge.get_clinic_context(self.business_id)
        
        print(f"✅ Pipeline started for WebSocket session (Context: {len(self.clinic_context)} chars)")
        
        # If outbound, greet immediately after a short stabilization delay
        if self.is_outbound:
            await asyncio.sleep(1.5)
            await self.handle_agent_turn(
                "Hello, I am calling from Aura Medical. I see you had an inquiry regarding our services.",
                persist_user_turn=False
            )

    async def process_audio_chunk(self, chunk_payload: str):
        """
        Process a binary audio chunk from Twilio (mu-law 8kHz)
        
        Args:
            chunk_payload: Base64-encoded mu-law audio chunk
        """
        audio_payload = base64.b64decode(chunk_payload)
        
        # Send raw mu-law to STT buffer
        if self.dg_connection:
            await self.dg_connection.send(audio_payload)
            
            # Reset silence timer — transcribe after 1.5s of silence
            if hasattr(self.dg_connection, 'transcribe_now'):
                if self.silence_timer:
                    self.silence_timer.cancel()
                self.silence_timer = asyncio.create_task(self.wait_for_silence())

    async def wait_for_silence(self, timeout=1.5):
        """Wait for silence before triggering transcription"""
        await asyncio.sleep(timeout)
        if self.dg_connection and hasattr(self.dg_connection, 'transcribe_now'):
            await self.dg_connection.transcribe_now()

    def on_transcript(self, transcript: str, is_final: bool):
        """STT callback when speech is transcribed"""
        if not transcript.strip():
            return

        print(f"🎙️ Patient: {transcript} [{'FINAL' if is_final else 'LIVE'}]")
        self.utterance_transcript = transcript
        self.is_final = is_final
        
        # INTERRUPTION HANDLING
        if self.is_agent_speaking and len(transcript.split()) > 1:
            print("🚀 Interruption detected! Stopping AI speech.")
            self.stop_agent_speech()
        
        if is_final:
            asyncio.create_task(self.handle_agent_turn(transcript))

    def stop_agent_speech(self):
        """Stop current TTS playback and clear Twilio buffer"""
        if self.tts_task:
            self.tts_task.cancel()
            self.tts_task = None
        
        self.is_agent_speaking = False
        
        if self.stream_sid:
            asyncio.create_task(self.send_clear_to_twilio())

    async def send_clear_to_twilio(self):
        """Send a 'clear' message to Twilio to stop all buffered audio"""
        try:
            clear_message = {
                "event": "clear",
                "streamSid": self.stream_sid
            }
            await self.websocket.send_text(json.dumps(clear_message))
        except Exception as e:
            print(f"❌ Error clearing Twilio buffer: {e}")

    async def handle_agent_turn(self, user_text: str, persist_user_turn: bool = True):
        """Handle one turn of the conversation"""
        # 1. Add user message to history
        working_history = list(self.history)
        if user_text and user_text.strip() and persist_user_turn:
            working_history.append({"role": "user", "content": user_text})
            if self.call_sid:
                await self.state.add_turn(self.call_sid, "user", user_text)
        
        # 2. Get agent response
        agent_resp = await self.agent.process_turn(
            user_text, 
            self.history, 
            clinic_context=self.clinic_context
        )
        
        # 3. Check for tool calls
        if agent_resp.get("tool_calls"):
            async with AsyncSessionLocal() as db:
                executor = ToolExecutor(db, self.business_id, caller_phone=self.caller_phone or "Unknown")
                
                for tool_call in agent_resp["tool_calls"]:
                    tool_result = await executor.execute(tool_call)
                    tool_name = self.get_tool_call_name(tool_call)
                    assistant_tool_turn = f"Tool Call: {tool_name}"
                    
                    working_history.append({"role": "assistant", "content": assistant_tool_turn})
                    working_history.append({"role": "tool", "content": tool_result["output"]})

                    if self.call_sid:
                        await self.state.add_turn(self.call_sid, "assistant", assistant_tool_turn)
                        await self.state.add_turn(self.call_sid, "tool", tool_result["output"])
                
                # Update history for final response
                self.history = working_history
                agent_resp = await self.agent.process_turn(
                    "", 
                    self.history, 
                    clinic_context=self.clinic_context
                )
        else:
            self.history = working_history

        # 4. Handle final text response
        response_text = agent_resp.get("content")
        if not response_text:
            response_text = "I've processed your request. Is there anything else?"

        print(f"🤖 Bot: {response_text}")
        
        # 5. Persistent State Update
        if self.call_sid:
            await self.state.add_turn(self.call_sid, "assistant", response_text)
        
        # 6. Update detected language from STT
        if self.dg_connection and hasattr(self.dg_connection, 'detected_language'):
            lang = str(self.dg_connection.detected_language)
            if lang:
                self.detected_language = lang
        
        # 7. Synthesize speech to patient (TTS)
        self.tts_task = asyncio.create_task(self.stream_response_to_patient(response_text))
        
        # 8. Audit logging
        await self.log_interaction("VOICE_TURN", {"user": user_text, "bot": response_text})

    async def stream_response_to_patient(self, text: str):
        """Stream TTS chunks to patient until complete or interrupted"""
        self.is_agent_speaking = True
        try:
            async for audio_chunk in self.tts.generate_speech_stream(text, language=self.detected_language):
                await self.send_audio_to_twilio(audio_chunk)
        finally:
            self.is_agent_speaking = False
            self.tts_task = None

    async def log_interaction(self, action: str, details: dict):
        """HIPAA compliant audit logging"""
        from ..database import AuditLogDB
        try:
            async with AsyncSessionLocal() as db:
                log = AuditLogDB(
                    id=str(uuid.uuid4()),
                    business_id=self.business_id,
                    action=action,
                    details=json.dumps(details),
                    created_at=datetime.utcnow()
                )
                db.add(log)
                await db.commit()
        except Exception as e:
            print(f"❌ Audit Log Error: {e}")

    async def trigger_transfer(self, reason: str):
        """Escalate call to a human receptionist"""
        print(f"📞 ESCALATING: {reason}")
        await self.log_interaction("HUMAN_TRANSFER", {"reason": reason})
        await self.handle_agent_turn("I am connecting you with a human representative now. Please hold.")

    @staticmethod
    def _pcm16_to_mulaw(pcm_data: bytes) -> bytes:
        """Convert 16-bit PCM samples to mu-law encoding (ITU-T G.711)."""
        MULAW_MAX = 0x1FFF
        MULAW_BIAS = 33
        result = bytearray()
        for i in range(0, len(pcm_data), 2):
            if i + 1 >= len(pcm_data):
                break
            sample = struct.unpack_from('<h', pcm_data, i)[0]
            sign = 0x80 if sample >= 0 else 0
            if sample < 0:
                sample = -sample
            sample = min(sample, MULAW_MAX)
            sample += MULAW_BIAS
            exponent = 7
            for exp_val in [0x4000, 0x2000, 0x1000, 0x0800, 0x0400, 0x0200, 0x0100]:
                if sample >= exp_val:
                    break
                exponent -= 1
            mantissa = (sample >> (exponent + 3)) & 0x0F
            mulaw_byte = ~(sign | (exponent << 4) | mantissa) & 0xFF
            result.append(mulaw_byte)
        return bytes(result)

    async def send_audio_to_twilio(self, wav_data: bytes):
        """
        Convert WAV audio to raw mu-law 8kHz and send to Twilio in chunks.
        Pure Python implementation (no pydub/audioop needed).
        """
        if not self.stream_sid or len(wav_data) < 100:
            return

        try:
            # Parse WAV to get raw PCM
            with wave.open(io.BytesIO(wav_data), 'rb') as wf:
                src_rate = wf.getframerate()
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                pcm_data = wf.readframes(wf.getnframes())
            
            # Downsample if needed (e.g., 24kHz -> 8kHz = keep every 3rd sample)
            if src_rate != 8000 and src_rate > 0:
                ratio = src_rate // 8000
                if ratio > 1:
                    step = sample_width * n_channels * ratio
                    frame_size = sample_width * n_channels
                    downsampled = bytearray()
                    for i in range(0, len(pcm_data), step):
                        downsampled.extend(pcm_data[i:i + frame_size])
                    pcm_data = bytes(downsampled)
            
            # If stereo, take only left channel
            if n_channels == 2:
                mono = bytearray()
                for i in range(0, len(pcm_data), sample_width * 2):
                    mono.extend(pcm_data[i:i + sample_width])
                pcm_data = bytes(mono)

            # Convert PCM to mu-law
            raw_mulaw = self._pcm16_to_mulaw(pcm_data)
            
            # Send in 160-byte chunks (20ms at 8kHz mu-law)
            chunk_size = 160
            for i in range(0, len(raw_mulaw), chunk_size):
                chunk = raw_mulaw[i:i + chunk_size]
                if not chunk:
                    break
                    
                payload = base64.b64encode(chunk).decode('utf-8')
                media_message = {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {"payload": payload}
                }
                
                await self.websocket.send_text(json.dumps(media_message))
                
                if i % 1600 == 0:
                    print(f"📤 Sent {i//160} chunks to Twilio...")
                
                # Jitter Buffer Strategy
                if i < 2400:
                    await asyncio.sleep(0.001)  # Quick burst
                else:
                    await asyncio.sleep(0.015)  # Stay ahead
                
        except Exception as e:
            print(f"❌ Error transcoding audio for Twilio: {e}")

    async def stop(self):
        """Stop all services and cleanup"""
        if self.dg_connection:
            await self.dg_connection.finish()
        if self.tts:
            await self.tts.close()
        if self.state:
            await self.state.close()
        print("🛑 Pipeline stopped")
