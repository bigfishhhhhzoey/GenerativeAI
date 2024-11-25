import time
import re
import os
import ssl
from datetime import datetime
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition as sr
from gtts import gTTS
import click
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

from openai import OpenAI
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@click.command()
@click.option("--energy", default=300, help="Energy level for the mic to detect", type=int)
@click.option("--pause", default=0.8, help="Pause time before entry ends", type=float)
@click.option("--dynamic_energy", default=False, is_flag=True, help="Flag to enable dynamic energy")
@click.option("--wake_word", default="hey computer", help="Wake word to listen for", type=str)
@click.option("--verbose", default=False, is_flag=True, help="Whether to print verbose output")
def main(energy=300, pause=0.8, dynamic_energy=False, wake_word="hey computer", verbose=False):
    r = sr.Recognizer()
    r.energy_threshold = energy
    r.pause_threshold = pause
    r.dynamic_energy_threshold = dynamic_energy

    with sr.Microphone(sample_rate=16000) as source:
        print("Listening...")
        conversation_active = False  # Track if the bot is in conversation mode

        while True:
            try:
                if verbose:
                    print(f"[{datetime.now()}] Waiting for input...")

                # Listen for audio
                audio = r.listen(source, phrase_time_limit=10)
                if verbose:
                    print(f"[{datetime.now()}] Captured audio.")

                # Transcribe audio
                transcription = transcribe_audio(audio, verbose)
                if not transcription:
                    continue

                # Check for stop word
                if "stop" in transcription.lower():
                    if verbose:
                        print(f"[{datetime.now()}] Stop word detected. Ending conversation.")
                    conversation_active = False
                    continue

                # Handle wake word or active conversation
                if conversation_active or transcription.lower().startswith(wake_word.lower()):
                    if not conversation_active:
                        transcription = transcription[len(wake_word):].strip()
                        conversation_active = True
                        if verbose:
                            print(f"[{datetime.now()}] Wake word detected. Starting conversation mode.")

                    if verbose:
                        print(f"[{datetime.now()}] User input: '{transcription}'")

                    # Get response from OpenAI API
                    response = get_response(transcription, verbose)
                    if verbose:
                        print(f"[{datetime.now()}] Bot response: '{response}'")

                    # Speak the response
                    speak_response(response, verbose)

                else:
                    if verbose:
                        print(f"[{datetime.now()}] Ignoring input (not in conversation mode).")

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                if verbose:
                    print(f"[{datetime.now()}] ERROR: {e}")


def transcribe_audio(audio, verbose):
    """Transcribe audio using OpenAI Whisper."""
    temp_audio_path = "temp_audio.wav"
    with open(temp_audio_path, "wb") as temp_audio_file:
        temp_audio_file.write(audio.get_wav_data())

    try:
        with open(temp_audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcription.text.strip()
    except Exception as e:
        if verbose:
            print(f"[{datetime.now()}] ERROR in transcription: {e}")
        return None
    finally:
        os.remove(temp_audio_path)


def get_response(user_input, verbose):
    """Get a response from OpenAI."""
    system_message = "You are a helpful assistant."
    user_message = f"Q: {user_input}?\nA:"
    messages = [{'role': 'system', 'content': system_message}, {'role': 'user', 'content': user_message}]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        if verbose:
            print(f"[{datetime.now()}] ERROR in OpenAI response: {e}")
        return "I'm sorry, I couldn't generate a response."


def speak_response(response, verbose):
    """Convert text to speech and play it."""
    try:
        mp3_obj = gTTS(text=response, lang="en", slow=False)
        mp3_obj.save("reply.mp3")
        if verbose:
            print(f"[{datetime.now()}] Audio file 'reply.mp3' generated successfully.")

        reply_audio = AudioSegment.from_mp3("reply.mp3")
        play(reply_audio)  # Blocking playback
        if verbose:
            print(f"[{datetime.now()}] Playback completed.")

    except Exception as e:
        if verbose:
            print(f"[{datetime.now()}] ERROR in TTS or playback: {e}")
    finally:
        if os.path.exists("reply.mp3"):
            os.remove("reply.mp3")


if __name__ == "__main__":
    main()
