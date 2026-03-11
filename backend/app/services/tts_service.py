"""
Sarvam AI Text-to-Speech Service (Bulbul v3)
============================================
Primary TTS engine with native Indian language support.
Falls back to Groq Orpheus if SARVAM_API_KEY is not configured.

Bulbul v3 Features:
- 30+ natural Indian voices
- 11 languages (10 Indian + English)
- Native 8kHz output (Twilio-compatible, no ffmpeg needed!)
- Adjustable speed (0.5x-2.0x)
"""

import asyncio
import base64
import os
import re
from typing import AsyncGenerator, List, Optional

import httpx
from ..utils.safe_print import safe_print as print


class TTSService:
    """Text-to-speech service with low-latency chunked synthesis."""

    def __init__(self):
        self.sarvam_key = os.getenv("SARVAM_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")

        self.sarvam_url = "https://api.sarvam.ai/text-to-speech"
        self.groq_url = "https://api.groq.com/openai/v1/audio/speech"

        self.sarvam_model = "bulbul:v3"
        self.sarvam_speaker = "priya"
        self.sarvam_language = "en-IN"
        self.max_chunk_chars = int(os.getenv("TTS_MAX_CHARS", "220"))

        self.client = httpx.AsyncClient(timeout=30.0)

        if self.sarvam_key:
            print("Sarvam TTS (Bulbul v3) initialized")
        elif self.groq_key:
            print("Sarvam TTS not configured, using Groq Orpheus fallback")
        else:
            print("No TTS API key configured!")

    async def generate_speech_stream(self, text: str, language: str = "en-IN") -> AsyncGenerator[bytes, None]:
        """
        Generate speech audio from text.

        The provider returns full clips, so we reduce first-audio latency by
        splitting long responses into smaller chunks and prefetching the next
        clip while the current one is playing.
        """
        if not text or not text.strip():
            return

        text_chunks = self.split_text_for_streaming(
            text,
            self.get_chunk_size_for_text(text)
        )
        if not text_chunks:
            return

        if self.sarvam_key:
            async def synthesize(chunk_text: str) -> Optional[bytes]:
                return await self._synthesize_sarvam(chunk_text, language)
        elif self.groq_key:
            synthesize = self._synthesize_groq_fallback
        else:
            return

        pending_audio = asyncio.create_task(synthesize(text_chunks[0]))

        for next_chunk in text_chunks[1:]:
            audio_bytes = await pending_audio
            pending_audio = asyncio.create_task(synthesize(next_chunk))

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

    async def _synthesize_sarvam(self, text: str, language: str = "en-IN") -> Optional[bytes]:
        """Synthesize one chunk with Sarvam."""
        headers = {
            "api-subscription-key": self.sarvam_key,
            "Content-Type": "application/json"
        }

        data = {
            "inputs": [text],
            "target_language_code": language,
            "model": self.sarvam_model,
            "speaker": self.sarvam_speaker,
            "sample_rate": 8000,
            "enable_preprocessing": True,
            "speech_speed": 1.0
        }

        try:
            response = await self.client.post(self.sarvam_url, json=data, headers=headers)

            if response.status_code != 200:
                print(f"Sarvam TTS error {response.status_code}: {response.text[:300]}")
                return None

            result = response.json()
            audios = result.get("audios", [])
            if audios:
                return base64.b64decode(audios[0])

        except httpx.ReadTimeout:
            print("Sarvam TTS timeout")
        except Exception as error:
            print(f"Sarvam TTS error: {error}")

        return None

    async def _synthesize_groq_fallback(self, text: str) -> Optional[bytes]:
        """Synthesize one chunk with Groq fallback."""
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "canopylabs/orpheus-v1-english",
            "input": text,
            "voice": "daniel",
            "response_format": "wav"
        }

        try:
            response = await self.client.post(self.groq_url, json=data, headers=headers)

            if response.status_code != 200:
                print(f"Groq TTS error {response.status_code}: {response.text[:300]}")
                return None

            return response.content

        except httpx.ReadTimeout:
            print("Groq TTS timeout")
        except Exception as error:
            print(f"Groq TTS error: {error}")

        return None

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None
