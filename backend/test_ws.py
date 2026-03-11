import asyncio
import os
import websockets

async def test_ws():
    uri = os.getenv("VOICE_WS_URL", "ws://localhost:8000/voice-stream")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            await websocket.send(
                '{"event":"start","start":{"streamSid":"test","callSid":"test","customParameters":{"business_id":"test","is_outbound":"true","caller":"+15551234567"}}}'
            )
            print("Message sent")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
