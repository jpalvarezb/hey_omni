import asyncio
import json
import vosk
import pyaudio
from typing import Optional, Dict, Union
from concurrent.futures import ThreadPoolExecutor
from ....core.exceptions import SpeechRecognitionError, ResourceInitializationError

class VoskRecognizer:
    """Speech recognition using Vosk."""
    
    def __init__(self, model_path: str = "./vosk-model-small-en-us-0.15"):
        self._model_path = model_path
        self._model = None
        self._recognizer = None
        self._audio = None
        self._stream = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._running = False
        
    async def initialize(self, config: Optional[Dict[str, Union[str, int, float]]] = None) -> None:
        """Initialize Vosk recognizer."""
        try:
            def _init():
                model = vosk.Model(self._model_path)
                audio = pyaudio.PyAudio()
                return model, audio
                
            self._model, self._audio = await asyncio.get_event_loop().run_in_executor(
                self._executor, _init
            )
            
            # Initialize recognizer with same settings as speech_module
            self._recognizer = vosk.KaldiRecognizer(self._model, 16000)
            
        except Exception as e:
            raise ResourceInitializationError(f"Failed to initialize Vosk: {str(e)}")
            
    async def start_recognition(self) -> None:
        """Start audio stream for recognition."""
        if not self._audio:
            raise ResourceInitializationError("Recognizer not initialized")
            
        try:
            def _start_stream():
                stream = self._audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=8192  # Same as speech_module
                )
                stream.start_stream()
                return stream
                
            self._stream = await asyncio.get_event_loop().run_in_executor(
                self._executor, _start_stream
            )
            self._running = True
            
        except Exception as e:
            raise SpeechRecognitionError(f"Failed to start recognition: {str(e)}")
            
    async def recognize(self) -> Optional[str]:
        """Perform speech recognition."""
        if not self._running:
            await self.start_recognition()
            
        try:
            def _recognize():
                data = self._stream.read(4096, exception_on_overflow=False)
                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    return result.get("text", "").strip()
                return None
                
            return await asyncio.get_event_loop().run_in_executor(
                self._executor, _recognize
            )
            
        except Exception as e:
            raise SpeechRecognitionError(f"Recognition failed: {str(e)}")
            
    async def stop_recognition(self) -> None:
        """Stop recognition."""
        if self._stream:
            def _stop_stream():
                self._stream.stop_stream()
                self._stream.close()
                
            await asyncio.get_event_loop().run_in_executor(
                self._executor, _stop_stream
            )
            self._stream = None
            self._running = False
            
    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.stop_recognition()
        if self._audio:
            self._audio.terminate()
        if self._executor:
            self._executor.shutdown(wait=True)
