"""
Gemini Speech-to-Text Service
==============================
Uses Google Gemini's multimodal audio understanding capability
to transcribe audio chunks. Buffers raw audio from Twilio,
wraps it in a WAV container, and sends to Gemini for transcription.

Note: No pydub dependency; uses Python's built-in wave/struct/audioop
for minimal audio format handling.
"""

import os
import io
import struct
import wave
from typing import Callable, Optional
from google import genai
from google.genai import types
from ..utils.safe_print import safe_print as print

# Mu-law decoding table (ITU-T G.711)
_MULAW_DECODE_TABLE = [
    -32124, -31100, -30076, -29052, -28028, -27004, -25980, -24956,
    -23932, -22908, -21884, -20860, -19836, -18812, -17788, -16764,
    -15996, -15484, -14972, -14460, -13948, -13436, -12924, -12412,
    -11900, -11388, -10876, -10364,  -9852,  -9340,  -8828,  -8316,
     -7932,  -7676,  -7420,  -7164,  -6908,  -6652,  -6396,  -6140,
     -5884,  -5628,  -5372,  -5116,  -4860,  -4604,  -4348,  -4092,
     -3900,  -3772,  -3644,  -3516,  -3388,  -3260,  -3132,  -3004,
     -2876,  -2748,  -2620,  -2492,  -2364,  -2236,  -2108,  -1980,
     -1884,  -1820,  -1756,  -1692,  -1628,  -1564,  -1500,  -1436,
     -1372,  -1308,  -1244,  -1180,  -1116,  -1052,   -988,   -924,
      -876,   -844,   -812,   -780,   -748,   -716,   -684,   -652,
      -620,   -588,   -556,   -524,   -492,   -460,   -428,   -396,
      -372,   -356,   -340,   -324,   -308,   -292,   -276,   -260,
      -244,   -228,   -212,   -196,   -180,   -164,   -148,   -132,
      -120,   -112,   -104,    -96,    -88,    -80,    -72,    -64,
       -56,    -48,    -40,    -32,    -24,    -16,     -8,      0,
     32124,  31100,  30076,  29052,  28028,  27004,  25980,  24956,
     23932,  22908,  21884,  20860,  19836,  18812,  17788,  16764,
     15996,  15484,  14972,  14460,  13948,  13436,  12924,  12412,
     11900,  11388,  10876,  10364,   9852,   9340,   8828,   8316,
      7932,   7676,   7420,   7164,   6908,   6652,   6396,   6140,
      5884,   5628,   5372,   5116,   4860,   4604,   4348,   4092,
      3900,   3772,   3644,   3516,   3388,   3260,   3132,   3004,
      2876,   2748,   2620,   2492,   2364,   2236,   2108,   1980,
      1884,   1820,   1756,   1692,   1628,   1564,   1500,   1436,
      1372,   1308,   1244,   1180,   1116,   1052,    988,    924,
       876,    844,    812,    780,    748,    716,    684,    652,
       620,    588,    556,    524,    492,    460,    428,    396,
       372,    356,    340,    324,    308,    292,    276,    260,
       244,    228,    212,    196,    180,    164,    148,    132,
       120,    112,    104,     96,     88,     80,     72,     64,
        56,     48,     40,     32,     24,     16,      8,      0,
]


def _mulaw_to_pcm16(mulaw_bytes: bytes) -> bytes:
    """Convert mu-law encoded audio bytes to 16-bit PCM."""
    pcm_samples = []
    for byte in mulaw_bytes:
        pcm_samples.append(_MULAW_DECODE_TABLE[byte])
    return struct.pack(f"<{len(pcm_samples)}h", *pcm_samples)


def _make_wav(pcm_data: bytes, sample_rate: int = 8000, channels: int = 1, sample_width: int = 2) -> bytes:
    """Wrap raw PCM data in a WAV container."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


class GeminiSTTConnection:
    """STT using Gemini multimodal audio understanding."""

    def __init__(self, gemini_client: genai.Client, on_transcript):
        self.client = gemini_client
        self.on_transcript = on_transcript
        self.audio_buffer = io.BytesIO()
        self.is_active = True
        self.detected_language = "en-IN"
        self._transcribing = False
        self._is_mulaw = True  # Default: expect mu-law from Twilio

    async def send(self, audio_chunk: bytes):
        """Buffer raw mu-law audio for processing"""
        if not self.is_active:
            return
        self._is_mulaw = True
        self.audio_buffer.write(audio_chunk)

    async def send_pcm(self, pcm_chunk: bytes):
        """Buffer raw PCM audio for processing"""
        if not self.is_active:
            return
        self._is_mulaw = False
        self.audio_buffer.write(pcm_chunk)

    async def transcribe_now(self):
        """Transcribe buffered audio using Gemini"""
        if self.audio_buffer.getbuffer().nbytes < 4000:
            return
        if self._transcribing:
            return
        self._transcribing = True

        try:
            raw_audio = self.audio_buffer.getvalue()
            self.audio_buffer = io.BytesIO()

            if self._is_mulaw:
                # Convert mu-law 8kHz -> PCM 16-bit -> WAV
                pcm_data = _mulaw_to_pcm16(raw_audio)
                wav_bytes = _make_wav(pcm_data, sample_rate=8000)
            else:
                # Already PCM 16kHz 16-bit mono, just wrap in WAV
                wav_bytes = _make_wav(raw_audio, sample_rate=16000)

            # Send to Gemini for transcription
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "Transcribe this audio exactly as spoken. Return ONLY the transcript text, nothing else. If no speech is detected, return an empty string.",
                    types.Part.from_bytes(
                        data=wav_bytes,
                        mime_type="audio/wav",
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                ),
            )

            transcript = response.text.strip() if response.text else ""
            if transcript:
                self.on_transcript(transcript, True)

        except Exception as e:
            print(f"❌ Gemini STT Error: {e}")
        finally:
            self._transcribing = False

    async def finish(self):
        self.is_active = False


class STTService:
    """Unified STT service using Gemini"""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_client = None

        if self.gemini_key:
            self.gemini_client = genai.Client(api_key=self.gemini_key)
            print("✅ Gemini STT Service Ready")
        else:
            print("⚠️ GEMINI_API_KEY not set. STT will not work.")

    async def start_session(self, on_transcript):
        """Initialize an STT session"""
        if self.gemini_client:
            return GeminiSTTConnection(self.gemini_client, on_transcript)
        return None
