"""
Gemini Text-to-Speech Service
===============================
Uses Gemini 2.5 Flash Preview TTS for natural speech synthesis.
Supports chunked streaming for low-latency voice responses.

Features:
- 30 prebuilt voices
- Natural, expressive speech
- Multi-language support
- 24kHz PCM output (converted to WAV for pipeline compatibility)
"""

import asyncio
import io
import os
import re
import wave
from typing import AsyncGenerator, List, Optional

from google import genai
from google.genai import types
from ..utils.safe_print import safe_print as print


class TTSService:
    """Text-to-speech service using Gemini TTS."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        self.voice_name = os.getenv("GEMINI_TTS_VOICE", "Kore")
        self.max_chunk_chars = int(os.getenv("TTS_MAX_CHARS", "220"))

        if self.gemini_key:
            self.client = genai.Client(api_key=self.gemini_key)
            print(f"✅ Gemini TTS initialized (voice: {self.voice_name})")
        else:
            print("⚠️ GEMINI_API_KEY not set. TTS will not work.")

    async def generate_speech_stream(self, text: str, language: str = "en-IN") -> AsyncGenerator[bytes, None]:
        """
        Generate speech audio from text using Gemini TTS.

        Splits long text into sentence-sized chunks and prefetches
        the next clip while the current one plays for low latency.
        """
        if not text or not text.strip():
            return
        if not self.client:
            return

        text_chunks = self.split_text_for_streaming(
            text,
            self.get_chunk_size_for_text(text)
        )
        if not text_chunks:
            return

        # Prefetch pipeline for low latency
        pending_audio = asyncio.create_task(self._synthesize_gemini(text_chunks[0]))

        for next_chunk in text_chunks[1:]:
            audio_bytes = await pending_audio
            pending_audio = asyncio.create_task(self._synthesize_gemini(next_chunk))

            if audio_bytes and len(audio_bytes) > 100:
                yield audio_bytes

        final_audio = await pending_audio
        if final_audio and len(final_audio) > 100:
            yield final_audio

    def split_text_for_streaming(self, text: str, max_chars: Optional[int] = None) -> List[str]:
        """Split text into sentence-sized chunks for faster first playback."""
        max_chars = max_chars or self.max_chunk_chars
        normalized = " ".join(text.split())
        if not normalized:
            return []

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?;:])\s+", normalized)
            if sentence.strip()
        ]

        if not sentences:
            sentences = [normalized]

        chunks: List[str] = []
        current_chunk = ""

        for sentence in sentences:
            if len(sentence) > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                chunks.extend(self._split_long_sentence(sentence, max_chars))
                continue

            candidate = f"{current_chunk} {sentence}".strip()
            if current_chunk and len(candidate) > max_chars:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = candidate

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def get_chunk_size_for_text(self, text: str) -> int:
        """Tune chunk size to typical voice replies for better first-audio latency."""
        normalized = " ".join(text.split())
        text_length = len(normalized)

        if text_length <= 140:
            return max(text_length, 140)
        if text_length <= 320:
            return min(self.max_chunk_chars, 160)
        if text_length <= 520:
            return min(self.max_chunk_chars, 180)
        return self.max_chunk_chars

    def _split_long_sentence(self, sentence: str, max_chars: int) -> List[str]:
        """Split oversized sentences first on commas, then on words."""
        clauses = [part.strip() for part in re.split(r"(?<=,)\s+", sentence) if part.strip()]
        if len(clauses) <= 1:
            return self._split_on_words(sentence, max_chars)

        chunks: List[str] = []
        current_chunk = ""

        for clause in clauses:
            candidate = f"{current_chunk} {clause}".strip()
            if current_chunk and len(candidate) > max_chars:
                chunks.append(current_chunk.strip())
                current_chunk = clause
            else:
                current_chunk = candidate

        if current_chunk:
            if len(current_chunk) > max_chars:
                chunks.extend(self._split_on_words(current_chunk, max_chars))
            else:
                chunks.append(current_chunk.strip())

        return chunks

    def _split_on_words(self, text: str, max_chars: int) -> List[str]:
        """Last-resort splitter for long uninterrupted text."""
        words = text.split()
        if not words:
            return []

        chunks: List[str] = []
        current_chunk = ""

        for word in words:
            candidate = f"{current_chunk} {word}".strip()
            if current_chunk and len(candidate) > max_chars:
                chunks.append(current_chunk.strip())
                current_chunk = word
            else:
                current_chunk = candidate

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    async def _synthesize_gemini(self, text: str) -> Optional[bytes]:
        """Synthesize one chunk with Gemini TTS, returning WAV bytes."""
        if not self.client:
            return None

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=f"Say in a professional, warm tone: {text}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice_name,
                            )
                        )
                    ),
                ),
            )

            # Extract PCM audio data from response
            if (response.candidates and 
                response.candidates[0].content and 
                response.candidates[0].content.parts):
                
                pcm_data = response.candidates[0].content.parts[0].inline_data.data
                
                if pcm_data and len(pcm_data) > 100:
                    # Convert raw PCM to WAV (24kHz, 16-bit, mono)
                    wav_buffer = io.BytesIO()
                    with wave.open(wav_buffer, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)  # 16-bit
                        wf.setframerate(24000)
                        wf.writeframes(pcm_data)
                    
                    return wav_buffer.getvalue()

        except Exception as error:
            print(f"❌ Gemini TTS error: {error}")

        return None

    async def close(self):
        """Cleanup (no persistent connections with Gemini)"""
        self.client = None
