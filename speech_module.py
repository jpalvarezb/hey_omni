import pyttsx3
import vosk
import json
import numpy as np
import pyaudio
import time
import pvporcupine  # For wake word detection
import logging
from helpers import log_info  # Make sure helpers has log_info

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Set logging level for debugging (INFO level for general logging, DEBUG for detailed logs)
logging.basicConfig(level=logging.INFO)

# Function to convert text to speech
def speak_text(text):
    try:
        logging.info(f"Speaking: {text}")
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logging.error(f"Error in speak_text: {e}")

# Function to recognize speech using Vosk
def recognize_speech():
    stream = None
    start_time = time.time()
    timeout_duration = 10  # Set the timeout duration in seconds
    detected_text = ""

    try:
        model_path = "./vosk-model-small-en-us-0.15"
        model = vosk.Model(model_path)

        recognizer = pyaudio.PyAudio()
        stream = recognizer.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
        stream.start_stream()

        rec = vosk.KaldiRecognizer(model, 16000)

        logging.info("Listening for your speech...")  # Notify the user that the program is waiting

        while True:
            data = stream.read(4096, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                detected_text = result.get("text", "").strip()
                if detected_text:  # Ensure it's not blank
                    logging.info(f"You said: {detected_text}")
                    break  # Exit the loop when valid speech is detected
            
            # Add timeout logic
            if time.time() - start_time > timeout_duration:
                logging.warning("Speech recognition timed out. Asking user to retry.")
                speak_text("I didn't hear anything. Please try again.")
                break

            # Handle partial results separately for more immediate feedback
            partial_result = rec.PartialResult()
            partial_result_data = json.loads(partial_result)
            if partial_result_data.get("partial"):
                logging.debug(f"Partial result: {partial_result_data['partial']}")

    except Exception as e:
        logging.error(f"Error in recognize_speech: {e}")

    finally:
        # Ensure that the stream is properly closed
        if stream is not None:
            stream.stop_stream()
            stream.close()
        recognizer.terminate()

    return detected_text if detected_text else ""

# Function to retry speech recognition and/or cancel command
def recognize_speech_with_cancel_retry(attempts=3):
    """Listens for speech input, retries on failure, and allows user to cancel."""
    for attempt in range(attempts):
        speech = recognize_speech().lower()
        if "cancel" in speech or "stop" in speech:
            log_info("User issued a cancel command.")
            return "cancel"
        elif speech:  # If speech was recognized
            return speech
        else:
            log_info(f"Attempt {attempt + 1}/{attempts} failed. Retrying...")
            speak_text("I didn't understand that. Could you repeat?")
    return None  # Return None if all attempts fail

# Function to initialize Porcupine for wake word detection
def initialize_porcupine():
    try:
        access_key = "UCQk8w5THzU7yu7Y96/HeJO1sXwcrLB0afg6O/onLeMXZSXEfWmZzQ=="  # Your access key
        porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=['./Hey-Omni_en_mac_v3_0_0/Hey-Omni_en_mac_v3_0_0.ppn']  # Replace with the correct path
        )
        logging.info("Porcupine initialized successfully.")
        return porcupine
    except Exception as e:
        logging.error(f"Error in initialize_porcupine: {e}")
        return None

# Function to listen for the wake word using Porcupine
def listen_for_wakeword(porcupine):
    stream = None
    try:
        recognizer = pyaudio.PyAudio()
        # Initialize PyAudio
        stream = recognizer.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=porcupine.frame_length)
        stream.start_stream()

        logging.info("Listening for wake word...")
        while True:
            # Read from the audio stream
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = np.frombuffer(pcm, dtype=np.int16)

            # Check if the wake word is detected
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                logging.info("Wake word detected!")
                speak_text("Wake word detected!")
                return True

    except KeyboardInterrupt:
        logging.info("Wake word detection stopped by user.")

    except Exception as e:
        logging.error(f"Error in listen_for_wakeword: {e}")
        return False

    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        recognizer.terminate()

    return False

# Function to cleanup resources when exiting
def cleanup_resources(porcupine):
    if porcupine is not None:
        logging.info("Cleaning up resources...")
        porcupine.delete()
        logging.info("Resources cleaned up.")

# Function to start the speech interaction, waiting for wake word and processing speech commands
def start_speech_interaction(porcupine):
    logging.info("Waiting for wake word to start interaction...")
    if listen_for_wakeword(porcupine):
        logging.info("Proceeding with speech interaction after wake word detected.")
        return True
    return False