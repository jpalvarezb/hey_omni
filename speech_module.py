import os
import pyttsx3
import vosk
import time
import json
import numpy as np
import pyaudio
import pvporcupine 
from helpers import log_info, log_error 

# Define recognition contexts and their patterns
RECOGNITION_CONTEXTS = {
    'weather': {
        'patterns': [
            ('our lee', 'hourly'),
            ('our leave', 'hourly'),
            ('early', 'hourly'),
            ('hour lee', 'hourly'),
            ('whether', 'weather'),
            ('four cast', 'forecast'),
            ('ford cast', 'forecast'),
            ('next to', 'next two'),
            ('tree', 'three'),
            ('for days', 'four days'),
            ('temper sure', 'temperature'),
            ('temper chair', 'temperature'),
            ('degree', 'degrees'),
            ('celsius', 'celsius'),
            ('sunny', 'sunny'),
            ('rain', 'rain'),
            ('raining', 'raining'),
            ('cloudy', 'cloudy'),
            ('precipitation', 'precipitation'),
            ('humidity', 'humidity'),
            ('weekly', 'weekly'),
            ('daily', 'daily'),
            ('tonight', 'tonight'),
            ('this evening', 'this evening'),
            ('this morning', 'this morning'),
            ('this afternoon', 'this afternoon')
        ],
        'keywords': [
            'weather', 'forecast', 'temperature', 'climate', 'hourly', 'daily',
            'sunny', 'rain', 'cloudy', 'precipitation', 'humidity',
            'degrees', 'celsius', 'weekly', 'tonight', 'morning', 'afternoon',
            'evening', 'conditions', 'high', 'low'
        ]
    },
    'timer': {
        'patterns': [
            ('set timer', 'set timer'),
            ('four', 'four'),
            ('mini its', 'minutes'),
            ('minute', 'minutes')
        ],
        'keywords': ['timer', 'minute', 'minutes', 'hour', 'hours', 'second', 'seconds']
    },
    'event': {
        'patterns': [
            ('a band', 'event'),
            ('every', 'event'),
            ('a vent', 'event'),
            ('of and', 'event'),
            ('oh but the bait', 'update'),
            ('the elite', 'delete'),
            ('the lead', 'delete'),
            ('named', 'named'),
            ('from', 'from'),
            ('to', 'to'),
            ('make it', 'make it'),
            ('change', 'change'),
            ('rename', 'rename'),
            ('reschedule', 'reschedule'),
            ('move', 'move'),
            ('start', 'start'),
            ('end', 'end'),
            ('duration', 'duration'),
            ('description', 'description'),
            ('summary', 'summary'),
            ('verify', 'verify'),
            ('confirm', 'confirm')
        ],
        'keywords': [
            'event', 'update', 'delete',
            'named', 'from', 'to', 'change', 'rename',
            'reschedule', 'move', 'start', 'end',
            'duration', 'description', 'summary',
            'verify', 'confirm', 'cancel'
        ]
    }
}

class ContextualRecognizer:
    def __init__(self):
        self.current_context = None
        self.model = None
        self.recognizer = None
        
    def set_context(self, context):
        """Set the current recognition context"""
        self.current_context = context
        log_info(f"Recognition context set to: {context}")
        
    def validate_and_correct(self, text):
        """Validate and correct text based on current context"""
        if not text or not self.current_context:
            return text
            
        context_data = RECOGNITION_CONTEXTS.get(self.current_context)
        if not context_data:
            return text
            
        # Check if text contains any context keywords
        text_lower = text.lower()
        has_context = any(keyword in text_lower for keyword in context_data['keywords'])
        
        if has_context:
            # Apply context-specific corrections
            for wrong, correct in context_data['patterns']:
                if wrong in text_lower:
                    log_info(f"Correcting '{wrong}' to '{correct}' based on {self.current_context} context")
                    text = text_lower.replace(wrong, correct)
                    
        return text

# Initialize the contextual recognizer
contextual_recognizer = ContextualRecognizer()

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

def recognize_speech(context=None):
    """
    Recognize speech with context awareness
    Args:
        context (str): Optional context for recognition (e.g., 'weather', 'timer')
    """
    if context:
        contextual_recognizer.set_context(context)
    
    stream = None
    start_time = time.time()
    timeout_duration = 10
    detected_text = ""

    try:
        model_path = "./vosk-model-small-en-us-0.15"
        model = vosk.Model(model_path)
        recognizer = pyaudio.PyAudio()
        stream = recognizer.open(format=pyaudio.paInt16, channels=1, rate=16000, 
                               input=True, frames_per_buffer=8192)
        stream.start_stream()

        rec = vosk.KaldiRecognizer(model, 16000)
        log_info("Listening for your speech...")

        while True:
            data = stream.read(4096, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                detected_text = result.get("text", "").strip()
                if detected_text:
                    # Apply context-based validation and correction
                    detected_text = contextual_recognizer.validate_and_correct(detected_text)
                    log_info(f"You said: {detected_text}")
                    break
            
            if time.time() - start_time > timeout_duration:
                log_info("Speech recognition timed out. Asking user to retry.")
                break

            partial_result = rec.PartialResult()
            partial_result_data = json.loads(partial_result)
            if partial_result_data.get("partial"):
                partial_text = partial_result_data['partial']
                # Apply context validation to partial results too
                partial_text = contextual_recognizer.validate_and_correct(partial_text)
                log_info(f"Partial result: {partial_text}")

    except Exception as e:
        log_error(f"Error in recognize_speech: {e}")

    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        recognizer.terminate()

    return detected_text if detected_text else ""

def recognize_speech_with_cancel_retry(attempts=3, context=None):
    """Listens for speech input with context awareness"""
    for attempt in range(attempts):
        log_info(f"Starting attempt {attempt + 1}/{attempts}")
        speech = recognize_speech(context=context).lower()

        if "cancel" in speech or "stop" in speech:
            log_info("User issued a cancel command.")
            return "cancel"

        if speech:
            log_info(f"Valid input received: {speech}")
            return speech

        log_info(f"Attempt {attempt + 1}/{attempts} failed. Retrying...")
        # Only speak the retry message if we're not on the last attempt
        if attempt < attempts - 1:
            speak_text("I didn't get that. Please repeat.")

    log_info("All attempts failed. No valid input received.")
    speak_text("I'm sorry, I couldn't understand you. Let's try something else.")
    return None

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
