import asyncio
import os
from dotenv import load_dotenv
from sarvamai import AsyncSarvamAI

load_dotenv()

async def inspect_ws():
    key = os.getenv("SARVAM_API_KEY")
    client = AsyncSarvamAI(api_subscription_key=key)
    
    try:
        async with client.speech_to_text_streaming.connect(
            model="saaras:v3",
            language_code="en-IN"
        ) as ws:
            print("Client type:", type(ws))
            print("Methods:", [m for m in dir(ws) if not m.startswith("_")])
                
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(inspect_ws())
