"""
Voice Service - Handles post-call transcription and analytics
Migrated to Sarvam AI Batch API (Speech-to-Text-Translate) with Diarization
and Call Analytics processing as per the official Sarvam cookbook.
"""
import os
import json
import httpx
import tempfile
import asyncio
import textwrap
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from sarvamai import SarvamAI
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
    """Service for voice transcription and call analytics processing"""
    
    def __init__(self):
        """Initialize the service with Sarvam AI client"""
        self.api_key = os.getenv("SARVAM_API_KEY")
        if not self.api_key:
            print("WARNING: SARVAM_API_KEY not set. Post-call analytics will fail.")
            self.client = None
        else:
            self.client = SarvamAI(api_subscription_key=self.api_key)
            self.output_dir = Path("outputs")
            self.output_dir.mkdir(exist_ok=True)
            print("✅ Sarvam Call Analytics initialized for post-call processing")
    
    async def transcribe_audio(self, audio_url: str, language: str = "en") -> str:
        """
        Transcribe audio from URL using Sarvam Batch API and generate analytics
        """
        if not self.client:
            raise Exception("Sarvam API key not configured. Please add SARVAM_API_KEY to backend/.env")
        
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
            
            print(f"📥 Downloaded recording from Twilio, kicking off Sarvam Analytics...")
            
            # Execute the heavy batch process in a separate thread so we don't block FastAPI
            transcript, analysis = await asyncio.to_thread(self._process_call_recording, temp_file)
            
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
            
    def _process_call_recording(self, file_path: str) -> Tuple[str, str]:
        """Synchronous process: Uploads to Batch API, waits, diarizes and analyzes."""
        # 1. Create Batch Job with Diarization
        job = self.client.speech_to_text_translate_job.create_job(
            model="saaras:v3",
            mode="translate",
            with_diarization=True,
        )
        
        job.upload_files(file_paths=[file_path], timeout=300)
        job.start()
        
        print(f"⏳ Waiting for Sarvam Batch Job {job.job_id} to complete...")
        job.wait_until_complete()
        
        if job.is_failed():
            raise Exception("Transcription job failed at Sarvam API.")
            
        # 2. Download and Parse JSON Output
        job_dir = self.output_dir / f"transcriptions_{job.job_id}"
        job_dir.mkdir(parents=True, exist_ok=True)
        job.download_outputs(output_dir=str(job_dir))
        
        json_files = list(job_dir.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(f"No .json transcription files found in {job_dir}.")
            
        json_file = json_files[0]
        file_name = json_file.stem
        
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        diarized = data.get("diarized_transcript", {}).get("entries")
        lines = []
        speaker_times = {}
        
        if diarized:
            for entry in diarized:
                speaker = entry["speaker_id"]
                text = entry["transcript"]
                lines.append(f"{speaker}: {text}")
                
                # Time tracking
                start = entry.get("start_time_seconds")
                end = entry.get("end_time_seconds")
                if start is not None and end is not None:
                    duration = end - start
                    speaker_times[speaker] = speaker_times.get(speaker, 0.0) + duration
        else:
            lines = [f"UNKNOWN: {data.get('transcript', '')}"]
            
        conversation_text = "\n".join(lines)
        
        # 3. Save Parsed Files (Transcript + Timing)
        txt_path = job_dir / f"{file_name}_conversation.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(conversation_text)
            
        if speaker_times:
            timing_path = job_dir / f"{file_name}_timing.json"
            with open(timing_path, "w", encoding="utf-8") as f:
                json.dump(speaker_times, f, indent=2)
                
        # 4. Generate LLM Analytics
        analysis = self._analyze_transcription(conversation_text, job_dir, file_name)
        
        return conversation_text, analysis
        
    def _analyze_transcription(self, transcription: str, output_dir: Path, file_name: str) -> str:
        """Call Sarvam Chat API to generate post-call analytics report"""
        analysis_prompt = textwrap.dedent(ANALYSIS_PROMPT_TEMPLATE.format(transcription=transcription))
        messages = [
            {
                "role": "system", 
                "content": "You are a call analytics expert working for a healthcare clinic's support operations team. Your job is to understand patient calls end-to-end and provide structured insights."
            },
            {
                "role": "user", 
                "content": analysis_prompt
            },
        ]
        
        try:
            response = self.client.chat.completions(messages=messages)
            analysis = response.choices[0].message.content
            
            analysis_path = output_dir / f"{file_name}_analysis.txt"
            with open(analysis_path, "w", encoding="utf-8") as f:
                f.write(analysis.strip())
            print(f"📊 Analytics saved to {analysis_path}")
            return analysis
        except Exception as e:
            print(f"Error generating call analytics: {e}")
            return ""
            
    async def transcribe_file(self, file_path: str) -> str:
        """Transcribe local audio file via Batch API"""
        if not self.client:
            raise Exception("Sarvam API key not configured.")
        
        try:
            transcript, _ = await asyncio.to_thread(self._process_call_recording, file_path)
            return transcript
        except Exception as e:
            print(f"Transcription failed: {e}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def validate_audio_format(self, filename: str) -> bool:
        """Validate audio file format"""
        valid_extensions = [".mp3", ".wav", ".m4a", ".ogg", ".webm", ".amr"]
        return any(filename.lower().endswith(ext) for ext in valid_extensions)
