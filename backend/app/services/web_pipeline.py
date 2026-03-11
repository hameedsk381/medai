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
    """Orchestrates the STT -> Agent -> TTS loop for a web-based voice interaction"""
    
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
        
        self.detected_language = "en-IN"
        self.use_sarvam = bool(os.getenv("SARVAM_API_KEY"))

    async def start(self):
        """Start the web voice pipeline"""
        # We don't need backend STT for the web pipeline anymore
        # since the client uses native Web Speech API.
        self.dg_connection = None
        
        # Initialize session state
        await self.state.create_session(self.session_id, self.business_id, "Web User")
        
        # Fetch initial clinic context
        self.clinic_context = await self.knowledge.get_clinic_context(self.business_id)
        
        print(f"🌐 Web Pipeline started (Session: {self.session_id})")
        
        # Immediate greeting
        await self.handle_agent_turn("Hello! I'm MedVoice AI, the receptionist for MedClinic. How can I assist you today?")

    async def process_audio_chunk(self, audio_data: bytes):
        pass # Deprecated for Web Voice

    async def process_transcript_input(self, text: str, is_final: bool):
        """Handle raw text transcripts coming from the frontend Web Speech API."""
        self.on_transcript(text, is_final)

    def on_transcript(self, transcript: str, is_final: bool):
        if not transcript.strip():
            return

        print(f"🎙️ [Web] User: {transcript} [{'FINAL' if is_final else 'LIVE'}]")
        self.utterance_transcript = transcript
        
        # Inform UI about live transcript
        asyncio.create_task(self.send_to_web({
            "event": "transcript", 
            "text": transcript, 
            "role": "user",
            "is_final": is_final
        }))

        if self.is_agent_speaking and len(transcript.split()) > 1:
            print("🚀 Interruption detected! Stopping AI speech.")
            self.stop_agent_speech()
        
        if is_final:
            asyncio.create_task(self.handle_agent_turn(transcript))

    def stop_agent_speech(self):
        if self.tts_task:
            self.tts_task.cancel()
            self.tts_task = None
        self.is_agent_speaking = False
        
        # Send clear to web
        asyncio.create_task(self.send_to_web({"event": "clear"}))

    async def handle_agent_turn(self, user_text: str):
        self.history = await self.state.get_history(self.session_id)
        
        if user_text.strip():
            self.history.append({"role": "user", "content": user_text})
            await self.state.add_turn(self.session_id, "user", user_text)
            
            # Inform UI about the transcript
            await self.send_to_web({"event": "transcript", "text": user_text, "role": "user"})
        
        # Start streaming LLM response
        full_response = ""
        current_sentence = ""
        
        print("⚡ [Web] Starting Ultra-Low Latency streaming...")
        self.active_tts_tasks += 1
        self.is_agent_speaking = True
        
        try:
            async for chunk_text in self.agent.process_turn_stream(
                user_text, 
                self.history, 
                clinic_context=self.clinic_context
            ):
                full_response += chunk_text
                current_sentence += chunk_text
                
                # Check for sentence completion (., !, ?)
                # If we have a sentence-ending punctuation followed by space or just after a few words
                if any(p in chunk_text for p in [".", "!", "?", ":", "\n"]):
                    # Send this sentence to TTS immediately
                    sentence_to_tts = current_sentence.strip()
                    if len(sentence_to_tts) > 2: # Ignore tiny fragments
                        print(f"🔊 [Web] Streaming Sentence to TTS: {sentence_to_tts}")
                        # We don't await the full TTS here, we start it as a task to keep LLM streaming
                        asyncio.create_task(self.stream_response_to_user(sentence_to_tts))
                        # Update UI with assistant transcript so far
                        await self.send_to_web({"event": "transcript", "text": full_response, "role": "assistant"})
                        current_sentence = ""

            # Handle any remaining text at the end
            if current_sentence.strip():
                asyncio.create_task(self.stream_response_to_user(current_sentence.strip()))
                await self.send_to_web({"event": "transcript", "text": full_response, "role": "assistant"})

            # Sync with database at the end
            await self.state.add_turn(self.session_id, "assistant", full_response)
            
        except Exception as e:
            print(f"❌ Web Streaming Error: {e}")
        finally:
            self.active_tts_tasks -= 1
            if self.active_tts_tasks <= 0:
                self.is_agent_speaking = False
                self.active_tts_tasks = 0

    async def stream_response_to_user(self, text: str):
        self.active_tts_tasks += 1
        self.is_agent_speaking = True
        try:
            async for audio_chunk in self.tts.generate_speech_stream(text, language=self.detected_language):
                # Send raw audio as base64 to web
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
        try:
            if self.websocket.client_state == WebSocketState.CONNECTED:
                await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            # Only print if it's not a normal disconnect
            if self.websocket.client_state == WebSocketState.CONNECTED:
                print(f"❌ Error sending to web: {e}")

    async def stop(self):
        """Stop all services and cleanup"""
        if self.tts_task:
            self.tts_task.cancel()
            self.tts_task = None
            
        if hasattr(self, 'dg_connection') and self.dg_connection:
            await self.dg_connection.finish()
            self.dg_connection = None
            
        print("🛑 Web Pipeline stopped")
