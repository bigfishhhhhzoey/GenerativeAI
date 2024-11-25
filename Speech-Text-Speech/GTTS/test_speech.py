from gtts import gTTS

try:
    tts = gTTS("Testing text-to-speech output", lang="en", slow=False)
    tts.save("test.mp3")
    print("TTS successful, saved as 'test.mp3'")
except Exception as e:
    print(f"TTS error: {e}")

from pydub import AudioSegment
from pydub.playback import play

try:
    audio = AudioSegment.from_mp3("test.mp3")
    play(audio)
    print("Playback successful.")
except Exception as e:
    print(f"Playback error: {e}")
