"""Local text-to-speech implementation."""
import pyttsx3
import io
import wave
from typing import Optional
from .base import BaseSynthesizer
from ....core.exceptions import ResourceInitializationError

class LocalTTSEngine(BaseSynthesizer):
    """Local text-to-speech engine using pyttsx3."""
    
    def __init__(self):
        """Initialize TTS engine."""
        self._engine = None
        
    async def initialize(self) -> None:
        """Initialize the TTS engine."""
        try:
            self._engine = pyttsx3.init()
        except Exception as e:
            raise ResourceInitializationError(f"Failed to initialize TTS engine: {str(e)}")
            
    async def synthesize(self, text: str) -> bytes:
        """Synthesize speech from text."""
        if not self._engine:
            raise ResourceInitializationError("TTS engine not initialized")
            
        try:
            # Convert text to speech and get raw audio
            self._engine.save_to_file(text, 'temp.wav')
            self._engine.runAndWait()
            
            # Read the wav file and return bytes
            with wave.open('temp.wav', 'rb') as wav_file:
                return wav_file.readframes(wav_file.getnframes())
                
        except Exception as e:
            raise ResourceInitializationError(f"Failed to synthesize speech: {str(e)}")
            
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._engine:
            self._engine.stop()
