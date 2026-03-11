from dotenv import load_dotenv
load_dotenv()
import httpx, os, base64, io
from pydub import AudioSegment

key = os.getenv("SARVAM_API_KEY")

r = httpx.post("https://api.sarvam.ai/text-to-speech", json={
    "inputs": ["Hi, how are you?"],
    "target_language_code": "en-IN",
    "model": "bulbul:v3",
    "speaker": "priya",
    "sample_rate": 8000
}, headers={"api-subscription-key": key}, timeout=15)

ab = base64.b64decode(r.json()["audios"][0])
print(f"Raw bytes: {len(ab)}, first 8 hex: {ab[:8].hex()}")

# Check if WAV
if ab[:4] == b'RIFF':
    print("Format: WAV")
    a = AudioSegment.from_wav(io.BytesIO(ab))
    print(f"WAV info: {a.frame_rate}Hz, {a.sample_width*8}-bit, {a.channels}ch, {len(a)}ms")
else:
    print(f"Format: NOT WAV, magic: {ab[:4]}")
