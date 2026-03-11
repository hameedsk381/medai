import asyncio
import os
import base64
from dotenv import load_dotenv
from sarvamai import AsyncSarvamAI

load_dotenv()

async def test_receive():
    key = os.getenv("SARVAM_API_KEY")
    client = AsyncSarvamAI(api_subscription_key=key)
    
    async with client.speech_to_text_streaming.connect(
        model="saaras:v3",
        language_code="en-IN"
    ) as ws:
        print("Connected")
        
        # Start a receiver task
        async def receiver():
            try:
                # Try async iterator pattern
                async for msg in ws:
                    print("Received (iterator):", msg)
            except Exception as e:
                print("Receiver error:", e)
        
        recv_task = asyncio.create_task(receiver())
        
        # Send some dummy audio
        audio_bytes = b'\x00' * 3200
        await ws.transcribe(audio=audio_bytes)
        
        await asyncio.sleep(1)
        await ws.close()
        await recv_task

if __name__ == "__main__":
    asyncio.run(test_receive())
