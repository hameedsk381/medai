import asyncio
import os
import base64
from dotenv import load_dotenv
from sarvamai import AsyncSarvamAI

load_dotenv()

async def test_transcribe():
    key = os.getenv("SARVAM_API_KEY")
    client = AsyncSarvamAI(api_subscription_key=key)
    
    async with client.speech_to_text_streaming.connect(
        model="saaras:v3",
        language_code="en-IN"
    ) as ws:
        print("Connected")
        # Send 100ms of audio (800 bytes at 8k mu-law? No, PCM 16k)
        # PCM 16k 16-bit = 16000 samples/sec * 2 bytes = 32000 bytes/sec
        # 100ms = 3200 bytes
        audio_bytes = b'\x00' * 3200
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        try:
            await ws.transcribe(audio=audio_b64)
            print("Sent base64")
        except Exception as e:
            print("Base64 error:", e)
            
        try:
            # Try sending raw bytes just in case the type hint is loose
            await ws.transcribe(audio=audio_bytes)
            print("Sent bytes")
        except Exception as e:
            print("Bytes error:", e)

if __name__ == "__main__":
    asyncio.run(test_transcribe())
