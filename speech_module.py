import os
import pyttsx3
import vosk
import time
import json
import numpy as np
import pyaudio
import pvporcupine 
from helpers import log_info, log_error 

# Initialize text-to-speech engine
engine = pyttsx3.init()

#TTS
def speak_text(text):
    try:
        log_info(f"Speaking: {text}")
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        log_error(f"Error in speak_text: {e}")

def recognize_speech():
    stream = None
    start_time = time.time()
    timeout_duration = 10
    detected_text = ""

    try:
        model_path = "./vosk-model-small-en-us-0.15"
        model = vosk.Model(model_path)
        recognizer = pyaudio.PyAudio()
        stream = recognizer.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
        stream.start_stream()

        rec = vosk.KaldiRecognizer(model, 16000)
        log_info("Listening for your speech...")

        while True:
            data = stream.read(4096, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                detected_text = result.get("text", "").strip()
                if detected_text:
                    log_info(f"You said: {detected_text}")
                    break
            
            if time.time() - start_time > timeout_duration:
                log_info("Speech recognition timed out. Asking user to retry.")
                break

            partial_result = rec.PartialResult()
            partial_result_data = json.loads(partial_result)
            if partial_result_data.get("partial"):
                log_info(f"Partial result: {partial_result_data['partial']}")

    except Exception as e:
        log_error(f"Error in recognize_speech: {e}")

    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        recognizer.terminate()

    return detected_text if detected_text else ""

# Function to retry speech recognition and/or cancel command
def recognize_speech_with_cancel_retry(attempts=3):
    """Listens for speech input, retries on failure, and allows user to cancel."""
    for attempt in range(attempts):
        log_info(f"Starting attempt {attempt + 1}/{attempts}")
        speech = recognize_speech().lower()  # Capture the speech input

        if "cancel" in speech or "stop" in speech:
            log_info("User issued a cancel command.")
            return "cancel"  # Return "cancel" to indicate command termination

        if speech:  # If valid speech is recognized
            log_info(f"Valid input received: {speech}")
            return speech  # Return the recognized speech

        # Prompt the user to retry if speech was not recognized
        log_info(f"Attempt {attempt + 1}/{attempts} failed. Retrying...")
        speak_text("I didn't get that. Please repeat.")

    log_info("All attempts failed. No valid input received.")
    speak_text("I'm sorry, I couldn't understand you. Let's try something else.")
    return None  # Return None if all attempts fail without valid input

#Wake word
def initialize_porcupine():
    try:
        access_key = os.getenv("PORCUPINE_API_KEY")  # Fetching API key from environment variable
        if not access_key:
            raise ValueError("PORCUPINE_API_KEY is not set in environment variables.")
        
        porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=['./Hey-Omni_en_mac_v3_0_0/Hey-Omni_en_mac_v3_0_0.ppn']
        )
        
        log_info("Porcupine initialized successfully.")
        return porcupine
    except Exception as e:
        log_error(f"Error in initialize_porcupine: {e}")
        return None

def listen_for_wakeword(porcupine):
    stream = None
    try:
        recognizer = pyaudio.PyAudio()
        stream = recognizer.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=porcupine.frame_length)
        stream.start_stream()

        log_info("Listening for wake word...")
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = np.frombuffer(pcm, dtype=np.int16)
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                log_info("Wake word detected.")
                return True

    except KeyboardInterrupt:
        log_info("Wake word detection stopped by user.")

    except Exception as e:
        log_error(f"Error in listen_for_wakeword: {e}")
        return False

    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        recognizer.terminate()

    return False

def start_speech_interaction(porcupine):
    log_info("Waiting for wake word to start interaction...")
    if listen_for_wakeword(porcupine):
        log_info("Proceeding with speech interaction after wake word detected.")
        speak_text("Wake word detected!")
        return True
    return False