import pyttsx3
import vosk
import json
import wave
import pyaudio
import pvporcupine
import struct

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Function to convert text to speech
def speak_text(text):
    engine.say(text)
    engine.runAndWait()

import pvporcupine

def initialize_porcupine():
    access_key = "UCQk8w5THzU7yu7Y96/HeJO1sXwcrLB0afg6O/onLeMXZSXEfWmZzQ=="  # Replace with your actual Picovoice access key
    porcupine = pvporcupine.create(
        access_key=access_key,
        keyword_paths=['./Hey-Omni_en_mac_v3_0_0/Hey-Omni_en_mac_v3_0_0.ppn']  # Adjust path to the trained custom wake word model
    )
    return porcupine

# Function to listen for wake word using Porcupine
def listen_for_wakeword(porcupine):
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print("Listening for wake word...")
    
    while True:
        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print("Wake word detected!")
            speak_text("Yes, how can I help?")
            return True  # Trigger voice command recognition after wake word

# Function to recognize speech using Vosk
def recognize_speech():
    model_path = "./vosk-model-small-en-us-0.15"  # Adjust if needed
    model = vosk.Model(model_path)
    
    # Initialize microphone recording
    recognizer = pyaudio.PyAudio()
    stream = recognizer.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
    stream.start_stream()
    
    print("Listening...")

    # Capture audio and process with Vosk
    rec = vosk.KaldiRecognizer(model, 16000)

    while True:
        data = stream.read(4096)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if "text" in result:
                print(f"You said: {result['text']}")
                return result['text']

    # Handle cases where speech wasn't recognized
    print("Sorry, I did not understand that.")
    speak_text("Sorry, I did not understand that. Please repeat.")
    return ""

# Optional retry mechanism if speech isn't recognized the first time
def recognize_speech_with_retry(attempts=3):
    for _ in range(attempts):
        result = recognize_speech()
        if result:  # If a valid result is returned, exit the loop
            return result
        speak_text("Let me try that again.")
    speak_text("Sorry, I couldn't understand you after several attempts.")
    return None  # Return None after exceeding the retry attempts

# Main function to combine wake word detection and speech recognition
def start_speech_interaction():
    porcupine = initialize_porcupine()  # Initialize Porcupine
    while True:
        if listen_for_wakeword(porcupine):  # Listen for wake word first
            command = recognize_speech_with_retry()  # Recognize speech after wake word is detected
            if command:
                print(f"Command: {command}")
                # Process the command here