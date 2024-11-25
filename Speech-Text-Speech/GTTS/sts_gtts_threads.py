import time
import queue
import threading
import re
import os
import ssl
from datetime import datetime
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition as sr
import torch
import numpy as np
from gtts import gTTS
import click
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

from openai import OpenAI
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def initialize_flags():
    global shutdown_event, pause_event
    shutdown_event = threading.Event()
    pause_event = threading.Event()


@click.command()
@click.option("--model", default="base", help="Model to use", type=click.Choice(["tiny", "base", "small", "medium", "large"]))
@click.option("--english", default=False, is_flag=True, help="Whether to use the English model")
@click.option("--energy", default=300, help="Energy level for the mic to detect", type=int)
@click.option("--pause", default=0.8, help="Pause time before entry ends", type=float)
@click.option("--dynamic_energy", default=False, is_flag=True, help="Flag to enable dynamic energy")
@click.option("--wake_word", default="hey computer", help="Wake word to listen for", type=str)
@click.option("--verbose", default=False, is_flag=True, help="Whether to print verbose output")
def main(model="base", english=False, energy=300, pause=0.8, dynamic_energy=False, wake_word="hey computer", verbose=False):
    initialize_flags()  # Reinitialize global flags

    audio_queue = queue.Queue()
    result_queue = queue.Queue()

    # Start threads
    record_thread = threading.Thread(target=record_audio, args=(audio_queue, energy, pause, dynamic_energy, verbose))
    transcribe_thread = threading.Thread(target=transcribe_forever, args=(audio_queue, result_queue, wake_word, verbose))
    reply_thread = threading.Thread(target=reply, args=(result_queue, verbose))

    record_thread.start()
    transcribe_thread.start()
    reply_thread.start()

    try:
        while True:
            time.sleep(0.1)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("\nShutting down...")
        shutdown_event.set()  # Signal all threads to stop
    finally:
        # Ensure threads are joined
        record_thread.join()
        transcribe_thread.join()
        reply_thread.join()
        print("All threads terminated. Goodbye!")


def record_audio(audio_queue, energy, pause, dynamic_energy, verbose):
    r = sr.Recognizer()
    r.energy_threshold = energy
    r.pause_threshold = pause
    r.dynamic_energy_threshold = dynamic_energy

    with sr.Microphone(sample_rate=16000) as source:
        print("Listening...")
        while not shutdown_event.is_set():
            try:
                audio = r.listen(source)
                audio_data = audio.get_wav_data()  # Get audio data in WAV format
                audio_queue.put_nowait(audio_data)
            except sr.WaitTimeoutError:
                if verbose:
                    print(f"[{datetime.now()}] Timeout: No speech detected.")
            except Exception as e:
                if shutdown_event.is_set():
                    break
                print(f"[{datetime.now()}] Error in record_audio: {e}")


def transcribe_forever(audio_queue, result_queue, wake_word, verbose):
    stop_word = "stop"  # Define the stop word
    conversation_active = False  # Reset conversation mode at the start
    while not shutdown_event.is_set():
        try:
            audio_data = audio_queue.get(timeout=1)  # Timeout prevents indefinite blocking
        except queue.Empty:
            continue  # Skip if queue is empty and re-check shutdown_event

        # Save the audio to a temporary file for transcription
        temp_audio_path = "temp_audio.wav"
        with open(temp_audio_path, "wb") as temp_audio_file:
            temp_audio_file.write(audio_data)

        try:
            with open(temp_audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            predicted_text = transcription.text
        except Exception as e:
            if verbose:
                print(f"[{datetime.now()}] ERROR in transcription: {e}")
            continue
        finally:
            os.remove(temp_audio_path)

        if verbose:
            print(f"[{datetime.now()}] Transcription result: '{predicted_text}'")

        # Check for stop word
        if stop_word in predicted_text.strip().lower():
            if verbose:
                print(f"[{datetime.now()}] Stop word detected. Ending conversation.")
            conversation_active = False  # Exit conversation mode
            continue

        # Handle wake word or active conversation
        if conversation_active or predicted_text.strip().lower().startswith(wake_word.strip().lower()):
            if not conversation_active:  # Transition to conversation mode
                pattern = re.compile(re.escape(wake_word), re.IGNORECASE)
                predicted_text = pattern.sub("", predicted_text).strip()
                conversation_active = True
                if verbose:
                    print(f"[{datetime.now()}] Wake word detected. Starting conversation mode.")

            predicted_text = re.sub(r"[^\w\s]", "", predicted_text)  # Clean up punctuation
            if verbose:
                print(f"[{datetime.now()}] Processing input: '{predicted_text}'")

            result_queue.put_nowait(predicted_text)
        else:
            if verbose:
                print(f"[{datetime.now()}] Ignoring input (not in conversation mode).")


def get_completion(messages, model="gpt-4o-mini", temperature=0.3, max_tokens=50):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()


def reply(result_queue, verbose):
    cache = {}  # Cache for storing previously generated responses
    while not shutdown_event.is_set():
        try:
            question = result_queue.get(timeout=1)  # Timeout prevents indefinite blocking
        except queue.Empty:
            continue  # Skip if queue is empty and re-check shutdown_event

        if question in cache:
            response = cache[question]
        else:
            system_message = f"""You're a helpful question-answering bot."""
            user_message = f"Q: {question}?\nA:"
            messages = [{'role': 'system', 'content': system_message}, {'role': 'user', 'content': user_message}]
            response = get_completion(messages)
            cache[question] = response

        # Print output based on verbosity
        if verbose:
            print(f"[{datetime.now()}] User question: '{question}'")
            print(f"[{datetime.now()}] Bot response: '{response}'")
        else:
            print(f"User question: '{question}'")
            print(f"Bot response: '{response}'\n")

        try:
            mp3_obj = gTTS(text=response, lang="en", slow=False)
            mp3_obj.save("reply.mp3")
            if verbose:
                print(f"[{datetime.now()}] Audio file 'reply.mp3' generated successfully.")
            reply_audio = AudioSegment.from_mp3("reply.mp3")
            if verbose:
                print(f"[{datetime.now()}] AudioSegment loaded successfully.")
            play(reply_audio)
            if verbose:
                print(f"[{datetime.now()}] Playback completed.")
            os.remove("reply.mp3")
            if verbose:
                print(f"[{datetime.now()}] Temporary audio file 'reply.mp3' removed.")
        except Exception as e:
            if verbose:
                print(f"[{datetime.now()}] ERROR in audio generation or playback: {e}")


if __name__ == "__main__":
    main()
