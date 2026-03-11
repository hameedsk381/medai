import os
import asyncio
from app.services.tts_service import TTSService
from dotenv import load_dotenv

load_dotenv()

async def test_tts():
    tts = TTSService()
    text = "Hello, this is a test of the medical receptionist system. How can I help you?"
    print(f"Synthesizing: {text}")
    
    chunks = []
    async for chunk in tts.generate_speech_stream(text):
        chunks.append(chunk)
        print(f"Got chunk: {len(chunk)} bytes")
        
    if chunks:
        full_audio = b"".join(chunks)
        with open("test_tts_out.wav", "wb") as f:
            f.write(full_audio)
        print(f"Saved to test_tts_out.wav ({len(full_audio)} bytes)")
        
        # Try to parse with pydub
        from pydub import AudioSegment
        import io
        try:
            audio = AudioSegment.from_file(io.BytesIO(full_audio))
            print(f"Pydub parsed: {len(audio)}ms, {audio.frame_rate}Hz, channels={audio.channels}")
        except Exception as e:
            print(f"Pydub failed to parse: {e}")

if __name__ == "__main__":
    asyncio.run(test_tts())
