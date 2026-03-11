from pydub import AudioSegment
import io
import base64

def test_conversion():
    # Create 1s of 440Hz sine wave
    from pydub.generators import Sine
    audio = Sine(440).to_audio_segment(duration=1000).set_frame_rate(8000).set_channels(1)
    
    # Method 1: wav with -acodec pcm_mulaw
    with io.BytesIO() as out:
        audio.export(out, format="wav", parameters=["-acodec", "pcm_mulaw"])
        wav_bytes = out.getvalue()
        print(f"WAV with mu-law size: {len(wav_bytes)}")
        print(f"Header: {wav_bytes[:10]}")
        # Twilio payload would be wav_bytes[44:]
        
    # Method 2: raw mulaw
    with io.BytesIO() as out:
        audio.export(out, format="mulaw")
        raw_bytes = out.getvalue()
        print(f"Raw mu-law size: {len(raw_bytes)}")
        # 1s at 8kHz should be exactly 8000 bytes
        
if __name__ == "__main__":
    test_conversion()
