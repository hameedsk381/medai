"""
Sarvam AI Speech-to-Text Service (Saaras v3)
=============================================
High-performance Streaming STT using Sarvam WebSocket.
Falls back to REST STT or Groq if WebSocket fails.
"""

import os
import io
import asyncio
import base64
import httpx
from typing import Callable, Optional
from sarvamai import AsyncSarvamAI
from pydub import AudioSegment
from ..utils.safe_print import safe_print as print


class SarvamStreamingSTTConnection:
    """Real-time STT using Sarvam Saaras v3 WebSocket."""

    def __init__(self, sarvam_client: AsyncSarvamAI, on_transcript: Callable, mode: str = "translate"):
        self.client = sarvam_client
        self.on_transcript = on_transcript
        self.mode = mode
        self.ws = None
        self.is_active = True
        self.detected_language = "en-IN"
        self._audio_queue = asyncio.Queue()
        self._process_task = None

    async def connect(self):
        """Establish the WebSocket connection"""
        try:
            # Connect to Sarvam STT WebSocket
            # Note: connect() returns an async context manager
            self.ws_ctx = self.client.speech_to_text_streaming.connect(
                model="saaras:v3",
                language_code="unknown",
                mode=self.mode,
                input_audio_codec="pcm_s16le",
                sample_rate=16000
            )
            self.ws = await self.ws_ctx.__aenter__()

            # Start background tasks
            self._listen_task = asyncio.create_task(self.ws.start_listening())
            self._process_task = asyncio.create_task(self._process_audio_stream())
            
            # Set up message handler via SDK callbacks
            self.ws.on("message", self._on_sarvam_message)
            self.ws.on("error", lambda e: print(f"❌ Sarvam STT WS Error: {e}"))
            
            print("🔌 Sarvam STT WebSocket connected and listening in background")
            
        except Exception as e:
            print(f"❌ Failed to connect to Sarvam STT WebSocket: {e}")
            import traceback
            traceback.print_exc()
            self.is_active = False

    def _on_sarvam_message(self, msg):
        """Callback for Sarvam WebSocket messages"""
        try:
            transcript = ""
            is_final = False
            
            if hasattr(msg, 'transcript'):
                transcript = msg.transcript
                # SDK might provide is_final
                is_final = getattr(msg, 'is_final', True) 
                if hasattr(msg, 'language_code') and msg.language_code:
                    self.detected_language = msg.language_code
            elif isinstance(msg, dict):
                transcript = msg.get("transcript", "")
                is_final = msg.get("is_final", True)
                lang = msg.get("language_code")
                if lang: self.detected_language = lang
            
            if transcript and transcript.strip():
                print(f"📡 Sarvam WS Transcript: {transcript} [{'FINAL' if is_final else 'PARTIAL'}]")
                self.on_transcript(str(transcript), is_final)
        except Exception as e:
            print(f"⚠️ Error parsing Sarvam WS message: {e}")

    async def _recv_loop(self):
        """No longer used, replaced by start_listening task + callbacks"""
        pass

    async def send(self, audio_chunk: bytes):
        """Queue raw mu-law audio for processing"""
        if not self.is_active:
            return
        await self._audio_queue.put(audio_chunk)

    async def _process_audio_stream(self):
        """Background task to convert and stream audio to Sarvam"""
        try:
            while self.is_active:
                chunk = await self._audio_queue.get()
                if chunk is None: break
                
                try:
                    mulaw_io = io.BytesIO(chunk)
                    # Convert mu-law -> PCM 16-bit 16kHz
                    audio = AudioSegment.from_file(mulaw_io, format="mulaw", frame_rate=8000, channels=1, sample_width=1)
                    audio = audio.set_frame_rate(16000).set_sample_width(2)
                    pcm_bytes = audio.raw_data
                    
                    b64_audio = base64.b64encode(pcm_bytes).decode('utf-8')
                    # Use provided socket client handle
                    if self.ws:
                        await self.ws.transcribe(audio=str(b64_audio))
                except Exception as e:
                    print(f"⚠️ Sarvam STT mu-law transceive error: {e}")
        except Exception as e:
            print(f"❌ Sarvam STT WS process loop error: {e}")

    async def send_pcm(self, pcm_chunk: bytes):
        """Send raw PCM 16kHz audio directly to Sarvam"""
        if not self.is_active or not self.ws:
            return
        
        try:
            # OPTIONAL DEBUG: print(f"🎧 Sending PCM chunk to Sarvam: {len(pcm_chunk)} bytes")
            b64_audio = base64.b64encode(pcm_chunk).decode('utf-8')
            await self.ws.transcribe(audio=b64_audio)
        except Exception as e:
            print(f"⚠️ Sarvam WS send_pcm error: {e}")



    async def transcribe_now(self):
        pass # WebSocket is continuous

    async def finish(self):
        self.is_active = False
        await self._audio_queue.put(None)
        if self._process_task:
            self._process_task.cancel()
        if hasattr(self, '_listen_task') and self._listen_task:
            self._listen_task.cancel()
        
        if hasattr(self, 'ws_ctx') and self.ws_ctx:
            try:
                await self.ws_ctx.__aexit__(None, None, None)
            except:
                pass
        print("🛑 Sarvam STT WebSocket finished")


class SarvamRESTSTTConnection:
    """Fallback REST STT using Sarvam Saaras v3."""

    def __init__(self, api_key: str, on_transcript: Callable, mode: str = "translate"):
        self.api_key = api_key
        self.on_transcript = on_transcript
        self.mode = mode
        self.audio_buffer = io.BytesIO()
        self.is_active = True
        self.detected_language = "en-IN"
        self.client = httpx.AsyncClient(timeout=15.0)
        self.stt_url = "https://api.sarvam.ai/speech-to-text"
        self._transcribing = False

    async def send(self, audio_chunk: bytes):
        if not self.is_active: return
        self.audio_buffer.write(audio_chunk)

    async def send_pcm(self, pcm_chunk: bytes):
        if not self.is_active: return
        self.audio_buffer.write(pcm_chunk)

    async def transcribe_now(self):
        if self.audio_buffer.getbuffer().nbytes < 4000: return
        if self._transcribing: return
        self._transcribing = True

        try:
            raw_audio = self.audio_buffer.getvalue()
            self.audio_buffer = io.BytesIO()
            audio_io = io.BytesIO(raw_audio)
            
            # Identify format (simplified: try mu-law first as default for this pipeline)
            try:
                audio = AudioSegment.from_file(audio_io, format="mulaw", frame_rate=8000, channels=1, sample_width=1)
            except:
                # Fallback to PCM if mu-law fails (very basic check)
                audio_io.seek(0)
                audio = AudioSegment.from_file(audio_io, format="raw", frame_rate=16000, channels=1, sample_width=2)
                
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format="wav")
            response = await self.client.post(
                self.stt_url,
                files={"file": ("speech.wav", wav_buffer.getvalue(), "audio/wav")},
                data={"model": "saaras:v3", "language_code": "unknown", "mode": self.mode},
                headers={"api-subscription-key": self.api_key}
            )
            if response.status_code == 200:
                result = response.json()
                transcript = result.get("transcript", "").strip()
                if result.get("language_code"): self.detected_language = result["language_code"]
                if transcript: self.on_transcript(transcript, True)
        except Exception as e:
            print(f"❌ Sarvam REST STT Error: {e}")
        finally:
            self._transcribing = False

    async def finish(self):
        self.is_active = False
        await self.client.aclose()


class GroqSTTConnection:
    """Fallback STT using Groq Whisper"""

    def __init__(self, groq_client, on_transcript: Callable):
        self.client = groq_client
        self.on_transcript = on_transcript
        self.audio_buffer = io.BytesIO()
        self.is_active = True
        self.detected_language = "en-IN"
        self._transcribing = False

    async def send(self, audio_chunk: bytes):
        if not self.is_active: return
        self.audio_buffer.write(audio_chunk)

    async def send_pcm(self, pcm_chunk: bytes):
        if not self.is_active: return
        self.audio_buffer.write(pcm_chunk)

    async def transcribe_now(self):
        if self.audio_buffer.getbuffer().nbytes < 4000: return
        if self._transcribing: return
        self._transcribing = True

        try:
            raw_audio = self.audio_buffer.getvalue()
            self.audio_buffer = io.BytesIO()
            audio_io = io.BytesIO(raw_audio)
            
            try:
                audio = AudioSegment.from_file(audio_io, format="mulaw", frame_rate=8000, channels=1, sample_width=1)
            except:
                audio_io.seek(0)
                audio = AudioSegment.from_file(audio_io, format="raw", frame_rate=16000, channels=1, sample_width=2)
                
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format="wav")
            
            audio_file = ("speech.wav", wav_buffer.getvalue())
            response = await self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                response_format="json",
                language="en"
            )
            transcript = response.text
            if transcript.strip(): self.on_transcript(transcript, True)
        except Exception as e:
            print(f"❌ Groq STT Error: {e}")
        finally:
            self._transcribing = False

    async def finish(self):
        self.is_active = False


class STTService:
    """Unified STT service: Sarvam (WebSocket -> REST) -> Groq"""

    def __init__(self):
        self.sarvam_key = os.getenv("SARVAM_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.sarvam_client = None
        self.groq_client = None

        if self.sarvam_key:
            self.sarvam_client = AsyncSarvamAI(api_subscription_key=self.sarvam_key)
            print("✅ Sarvam STT Service Ready")
        
        if self.groq_key:
            from groq import AsyncGroq
            self.groq_client = AsyncGroq(api_key=self.groq_key)

    async def start_session(self, on_transcript: Callable[[str, bool], None]):
        """Initialize an STT session"""
        if self.sarvam_key and self.sarvam_client:
            conn = SarvamStreamingSTTConnection(self.sarvam_client, on_transcript)
            await conn.connect()
            if conn.is_active:
                return conn
            return SarvamRESTSTTConnection(self.sarvam_key, on_transcript)
        elif self.groq_client:
            return GroqSTTConnection(self.groq_client, on_transcript)
        return None
