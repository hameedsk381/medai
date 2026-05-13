import asyncio
import json
import os
import base64
import io
import uuid
from datetime import datetime
from typing import Optional
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from .stt_service import STTService
from .tts_service import TTSService
from .agent_service import AgentService
from .tool_executor import ToolExecutor
from .knowledge_service import KnowledgeService
from .conversation_state import ConversationState
from ..database import AsyncSessionLocal
from ..utils.safe_print import safe_print as print

class WebVoicePipeline:
    """Orchestrates the STT (Gemini) -> Agent -> TTS loop for a web-based voice interaction"""
    
    def __init__(self, websocket: any, business_id: str = "demo-clinic-1"):
        self.websocket = websocket
        self.business_id = business_id
        self.stt = STTService()
        self.tts = TTSService()
        self.agent = AgentService()
        self.knowledge = KnowledgeService()
        self.state = ConversationState()
        
        # Audio state
        self.is_speaking = False
        self.session_id = str(uuid.uuid4())
        
        # Conversation state
        self.history = []
        self.clinic_context = ""
        self.utterance_transcript = ""
        self.is_final = False
        
        # Interruption handling
        self.tts_task = None
        self.is_agent_speaking = False
        self.active_tts_tasks = 0
        
        # Silence Detection for Web (Gemini STT)
        self.silence_timer = None
        self.dg_connection = None
        
        self.detected_language = "en-IN"

    async def start(self):
        """Start the web voice pipeline with Gemini STT"""
        # Start Gemini STT session for the web client
        self.dg_connection = await self.stt.start_session(
            on_transcript=self.on_transcript
        )
        
        # Initialize session state (Phase 4)
        await self.state.create_session(self.session_id, self.business_id, "Web User")
        
        # Fetch initial clinic context (Phase 3)
        self.clinic_context = await self.knowledge.get_clinic_context(self.business_id)
        
        print(f"🌐 Web Pipeline (Gemini STT) started (Session: {self.session_id})")
        
        # Immediate greeting
        await self.handle_agent_turn("Hello! I'm MedVoice AI, the receptionist for MedClinic. How can I assist you today?")

    async def process_audio_chunk(self, audio_data: bytes):
        """Process raw PCM audio chunks from the frontend"""
        if self.dg_connection:
            # Web sends raw 16kHz PCM (defined in VoiceInterface.tsx)
            await self.dg_connection.send_pcm(audio_data)
            
            # Reset silence timer — transcribe after 1.5s of silence
            if self.silence_timer:
                self.silence_timer.cancel()
            self.silence_timer = asyncio.create_task(self.wait_for_silence())

    async def wait_for_silence(self, timeout=1.5):
        """Wait for silence before triggering Gemini transcription"""
        await asyncio.sleep(timeout)
        if self.dg_connection and hasattr(self.dg_connection, 'transcribe_now'):
            await self.dg_connection.transcribe_now()

    async def process_transcript_input(self, text: str, is_final: bool):
        """[Deprecated] Transcripts now come from self.on_transcript via Gemini STT"""
        pass

    def on_transcript(self, transcript: str, is_final: bool):
        """STT callback when Gemini transcribes speech from the web audio stream"""
        if not transcript.strip():
            return

        print(f"🎙️ [Web-Gemini] User: {transcript} [{'FINAL' if is_final else 'LIVE'}]")
        self.utterance_transcript = transcript
        
        # Inform UI about live transcript
        asyncio.create_task(self.send_to_web({
            "event": "transcript", 
            "text": transcript, 
            "role": "user",
            "is_final": is_final
        }))

        # Interruption handling
        if self.is_agent_speaking and len(transcript.split()) > 1:
            print("🚀 Interruption detected! Stopping AI speech.")
            self.stop_agent_speech()
        
        if is_final:
            asyncio.create_task(self.handle_agent_turn(transcript))

    def stop_agent_speech(self):
        """Stop current AI speech tasks and clear web audio queue"""
        if self.tts_task:
            self.tts_task.cancel()
            self.tts_task = None
        self.is_agent_speaking = False
        self.active_tts_tasks = 0
        
        # Send clear to web UI
        asyncio.create_task(self.send_to_web({"event": "clear"}))

    async def handle_agent_turn(self, user_text: str):
        """Unified turn handler for web pipeline"""
        self.history = await self.state.get_history(self.session_id)
        
        if user_text.strip():
            self.history.append({"role": "user", "content": user_text})
            await self.state.add_turn(self.session_id, "user", user_text)
            
            # Sync user transcript to UI
            await self.send_to_web({"event": "transcript", "text": user_text, "role": "user", "is_final": True})
        
        # Stream response
        full_response = ""
        current_sentence = ""
        
        print("⚡ [Web] Streaming response via Gemini...")
        self.is_agent_speaking = True
        
        try:
            async for chunk_text in self.agent.process_turn_stream(
                user_text, 
                self.history, 
                clinic_context=self.clinic_context
            ):
                full_response += chunk_text
                current_sentence += chunk_text
                
                if any(p in chunk_text for p in [".", "!", "?", ":", "\n"]):
                    sentence_to_tts = current_sentence.strip()
                    if len(sentence_to_tts) > 2:
                        # Start TTS task for this sentence
                        asyncio.create_task(self.stream_response_to_user(sentence_to_tts))
                        # Update UI with partial assistant transcript
                        await self.send_to_web({"event": "transcript", "text": full_response, "role": "assistant"})
                        current_sentence = ""

            if current_sentence.strip():
                asyncio.create_task(self.stream_response_to_user(current_sentence.strip()))
                await self.send_to_web({"event": "transcript", "text": full_response, "role": "assistant"})

            # Persist assistant turn
            await self.state.add_turn(self.session_id, "assistant", full_response)
            
        except Exception as e:
            print(f"❌ Web Pipeline Error: {e}")
        finally:
            # We don't drop is_agent_speaking here immediately, 
            # it will be cleared by the last stream_response_to_user task.
            pass

    async def stream_response_to_user(self, text: str):
        """Generate and stream audio chunks to the frontend"""
        self.active_tts_tasks += 1
        self.is_agent_speaking = True
        try:
            async for audio_chunk in self.tts.generate_speech_stream(text, language=self.detected_language):
                payload = base64.b64encode(audio_chunk).decode('utf-8')
                await self.send_to_web({
                    "event": "audio",
                    "payload": payload
                })
        except Exception as e:
            print(f"⚠️ TTS Stream error: {e}")
        finally:
            self.active_tts_tasks -= 1
            if self.active_tts_tasks <= 0:
                self.is_agent_speaking = False
                self.active_tts_tasks = 0

    async def send_to_web(self, message: dict):
        """Safe WebSocket send helper"""
        try:
            if self.websocket.client_state == WebSocketState.CONNECTED:
                await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            if self.websocket.client_state == WebSocketState.CONNECTED:
                print(f"❌ Error sending to web: {e}")

    async def stop(self):
        """Cleanup session and resources"""
        if self.tts_task:
            self.tts_task.cancel()
        if self.silence_timer:
            self.silence_timer.cancel()
        if self.dg_connection:
            await self.dg_connection.finish()
        print("🛑 Web Pipeline stopped")
