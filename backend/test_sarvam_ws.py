import asyncio
import os
from dotenv import load_dotenv
from sarvamai import AsyncSarvamAI

load_dotenv()

async def test_streaming_stt():
    key = os.getenv("SARVAM_API_KEY")
    client = AsyncSarvamAI(api_subscription_key=key)
    
    try:
        async with client.speech_to_text_streaming.connect(
            model="saaras:v3",
            language_code="en-IN",
            input_audio_codec="pcm_s16le",
            sample_rate=16000
        ) as ws:
            print("Connected to Sarvam STT WebSocket")
            # Send 1 second of silence (16000 samples * 2 bytes = 32000 bytes)
            silence = b'\x00' * 32000
            await ws.send(silence)
            print("Sent silence")
            
            # Send close
            await ws.close()
            print("Closed")
                
    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming_stt())
