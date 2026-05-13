"""
Voice Service - Handles post-call transcription and analytics
Uses Google Gemini for both audio transcription and call analytics.
"""
import os
import json
import httpx
import tempfile
import asyncio
import textwrap
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from google import genai
from google.genai import types
from ..utils.safe_print import safe_print as print

ANALYSIS_PROMPT_TEMPLATE = """
Analyze this call transcription thoroughly from start to finish.

TRANSCRIPTION:
{transcription}

Please answer the following:

1. Identify which speaker is the **patient/customer** and which one is the **medical agent**.
2. Determine if the patient is a **new/potential patient** or an **existing patient**.
3. What **problem, symptom, query, or request** did the patient raise at the beginning?
4. What **medical services/appointments** was the patient inquiring about?
5. How did the AI agent respond to and resolve the issue throughout the call?
6. Was the **patient satisfied** at the end of the call?
7. Did the patient express any **emotions or sentiments** (positive, negative, anxiety, or neutral)?
8. Were there any mentions of **urgency or emergency** symptoms?
9. Summarize the **resolution** and whether a booking/task was successfully created.

Provide your answer in a clear, structured format with section headings and bullet points.
"""

class VoiceService:
    """Service for voice transcription and call analytics processing using Gemini"""
    
    def __init__(self):
        """Initialize the service with Gemini client"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("WARNING: GEMINI_API_KEY not set. Post-call analytics will fail.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            self.output_dir = Path("outputs")
            self.output_dir.mkdir(exist_ok=True)
            print("✅ Gemini Call Analytics initialized for post-call processing")
    
    async def transcribe_audio(self, audio_url: str, language: str = "en") -> str:
        """
        Transcribe audio from URL using Gemini and generate analytics
        """
        if not self.client:
            raise Exception("GEMINI_API_KEY not configured. Please add it to .env")
        
        try:
            # Download audio file
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(audio_url, timeout=30.0)
                response.raise_for_status()
                audio_data = response.content
            
            # Save temporarily (Windows compatible path)
            temp_file = tempfile.mktemp(suffix=".mp3")
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            print(f"📥 Downloaded recording, starting Gemini transcription...")
            
            # Transcribe with Gemini
            transcript = await self._transcribe_with_gemini(audio_data, "audio/mpeg")
            
            # Generate analytics
            if transcript:
                analysis = await self._analyze_transcription(transcript)
                
                # Save outputs
                job_dir = self.output_dir / f"transcriptions_gemini"
                job_dir.mkdir(parents=True, exist_ok=True)
                
                import uuid
                file_id = str(uuid.uuid4())[:8]
                
                txt_path = job_dir / f"{file_id}_conversation.txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(transcript)
                
                if analysis:
                    analysis_path = job_dir / f"{file_id}_analysis.txt"
                    with open(analysis_path, "w", encoding="utf-8") as f:
                        f.write(analysis.strip())
                    print(f"📊 Analytics saved to {analysis_path}")
            
            # Clean up
            try:
                os.remove(temp_file)
            except:
                pass
            
            print(f"✅ Call Analytics completed successfully!")
            return transcript
            
        except Exception as e:
            print(f"Transcription failed: {e}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    async def _transcribe_with_gemini(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe audio using Gemini's multimodal audio understanding"""
        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    textwrap.dedent("""
                    Transcribe this audio recording precisely. 
                    If multiple speakers are detected, label them as SPEAKER_00, SPEAKER_01, etc.
                    Format: Each speaker turn on a new line as "SPEAKER_XX: <text>"
                    If only one speaker, just provide the transcript text.
                    Return ONLY the transcript, no commentary.
                    """).strip(),
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type=mime_type,
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                ),
            )
            
            return response.text.strip() if response.text else ""
            
        except Exception as e:
            print(f"❌ Gemini transcription error: {e}")
            return ""
    
    async def _analyze_transcription(self, transcription: str) -> str:
        """Generate post-call analytics using Gemini"""
        analysis_prompt = textwrap.dedent(ANALYSIS_PROMPT_TEMPLATE.format(transcription=transcription))
        
        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=analysis_prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are a call analytics expert working for a healthcare clinic's support operations team. Your job is to understand patient calls end-to-end and provide structured insights.",
                    temperature=0.3,
                ),
            )
            
            return response.text.strip() if response.text else ""
            
        except Exception as e:
            print(f"❌ Error generating call analytics: {e}")
            return ""
            
    async def transcribe_file(self, file_path: str) -> str:
        """Transcribe local audio file using Gemini"""
        if not self.client:
            raise Exception("GEMINI_API_KEY not configured.")
        
        try:
            with open(file_path, "rb") as f:
                audio_bytes = f.read()
            
            # Detect mime type from extension
            ext = os.path.splitext(file_path)[1].lower()
            mime_map = {
                ".mp3": "audio/mpeg",
                ".wav": "audio/wav",
                ".m4a": "audio/mp4",
                ".ogg": "audio/ogg",
                ".webm": "audio/webm",
                ".amr": "audio/amr",
                ".flac": "audio/flac",
            }
            mime_type = mime_map.get(ext, "audio/wav")
            
            transcript = await self._transcribe_with_gemini(audio_bytes, mime_type)
            return transcript
            
        except Exception as e:
            print(f"Transcription failed: {e}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def validate_audio_format(self, filename: str) -> bool:
        """Validate audio file format"""
        valid_extensions = [".mp3", ".wav", ".m4a", ".ogg", ".webm", ".amr", ".flac"]
        return any(filename.lower().endswith(ext) for ext in valid_extensions)
