from pathlib import Path
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    # Generate TTS audio
    response = client.audio.speech.create(
        model="tts-1",
        voice="shimmer",
        input="Testing OpenAI Text-to-Speech output!"
    )
    speech_file_path = Path("test_speech.mp3")
    response.stream_to_file(speech_file_path)
    print("TTS successful, saved as 'test_speech.mp3'")

    # Playback the audio
    audio = AudioSegment.from_file(speech_file_path)
    play(audio)
    print("Playback successful.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists("test_speech.mp3"):
        os.remove("test_speech.mp3")
        print("Temporary file 'test_speech.mp3' removed.")
