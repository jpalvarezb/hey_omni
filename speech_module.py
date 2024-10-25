import pyttsx3
import vosk
import json
import numpy as np
import pyaudio
import pvporcupine  # For wake word detection

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Function to convert text to speech
def speak_text(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error in speak_text: {e}")

# Function to recognize speech using Vosk
def recognize_speech():
    stream = None
    try:
        model_path = "./vosk-model-small-en-us-0.15"
        model = vosk.Model(model_path)

        recognizer = pyaudio.PyAudio()
        stream = recognizer.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
        stream.start_stream()

        rec = vosk.KaldiRecognizer(model, 16000)

        print("Listening for your speech...")  # Notify the user the program is waiting
        detected_text = ""

        while True:
            data = stream.read(4096, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                detected_text = result.get("text", "").strip()
                if detected_text:  # Ensure it's not blank
                    print(f"You said: {detected_text}")
                    break  # Exit the loop when valid speech is detected

            partial_result = rec.PartialResult()  # Handle partial results separately
            partial_result_data = json.loads(partial_result)
            if partial_result_data.get("partial"):
                print(f"Partial result: {partial_result_data['partial']}")

    except Exception as e:
        print(f"Error in recognize_speech: {e}")

    finally:
        # Ensure that the stream is properly closed
        if stream is not None:
            stream.stop_stream()
            stream.close()
        recognizer.terminate()

    if detected_text:
        return detected_text
    else:
        print("I didn't understand that, trying again...")
        speak_text("I didn't understand that, please repeat.")
        return ""

# Function to initialize Porcupine for wake word detection
def initialize_porcupine():
    try:
        access_key = "UCQk8w5THzU7yu7Y96/HeJO1sXwcrLB0afg6O/onLeMXZSXEfWmZzQ=="  # Your access key
        porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=['./Hey-Omni_en_mac_v3_0_0/Hey-Omni_en_mac_v3_0_0.ppn']  # Replace with the correct path
        )
        return porcupine
    except Exception as e:
        print(f"Error in initialize_porcupine: {e}")
        return None

# Function to listen for the wake word using Porcupine
def listen_for_wakeword(porcupine):
    stream = None
    try:
        recognizer = pyaudio.PyAudio()
        # Initialize PyAudio
        stream = recognizer.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=porcupine.frame_length)
        stream.start_stream()

        while True:
            # Read from the audio stream
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = np.frombuffer(pcm, dtype=np.int16)

            # Check if the wake word is detected
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("Wake word detected!")
                return True

    except KeyboardInterrupt:
        print("Stopped by user")

    except Exception as e:
        print(f"Error in listen_for_wakeword: {e}")
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
        print("Cleaning up resources...")
        porcupine.delete()
        print("Resources cleaned up.")

# Function to start the speech interaction, waiting for wake word and processing speech commands
def start_speech_interaction(porcupine):
    print("Listening for wake word...")
    if listen_for_wakeword(porcupine):
        print("Wake word detected!")
        return True
    return False