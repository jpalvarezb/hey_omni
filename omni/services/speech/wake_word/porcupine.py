import os
import asyncio
import numpy as np
import pyaudio
import pvporcupine
from typing import Optional, Dict, Union
from concurrent.futures import ThreadPoolExecutor
from ....core.exceptions import ResourceInitializationError, WakeWordError
from .base import BaseWakeWordDetector

class PorcupineWakeWord(BaseWakeWordDetector):
    """Wake word detection using Picovoice's Porcupine."""
    
    def __init__(self):
        self._porcupine = None
        self._audio = None
        self._stream = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._running = False
        
    async def initialize(self, config: Optional[Dict[str, Union[str, int, float]]] = None) -> None:
        """Initialize Porcupine detector."""
        try:
            access_key = os.getenv("PORCUPINE_API_KEY")
            if not access_key:
                raise ResourceInitializationError("PORCUPINE_API_KEY is not set")
                
            def _init():
                porcupine = pvporcupine.create(
                    access_key=access_key,
                    keyword_paths=['./Hey-Omni_en_mac_v3_0_0/Hey-Omni_en_mac_v3_0_0.ppn']
                )
                return porcupine
                
            self._porcupine = await asyncio.get_event_loop().run_in_executor(
                self._executor, _init
            )
            self._running = True
            
        except Exception as e:
            raise ResourceInitializationError(f"Failed to initialize Porcupine: {str(e)}")
            
    async def start_detection(self) -> None:
        """Start wake word detection."""
        if not self._running:
            await self.initialize()
            
        try:
            # Initialize audio interface
            self._audio = pyaudio.PyAudio()
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=self._porcupine.frame_length
            )
            self._stream.start_stream()
            
        except Exception as e:
            raise WakeWordError(f"Failed to start audio stream: {str(e)}")
            
    async def detect(self) -> bool:
        """Check for wake word detection."""
        if not self._running or not self._stream:
            return False
            
        try:
            pcm = self._stream.read(self._porcupine.frame_length, exception_on_overflow=False)
            pcm = np.frombuffer(pcm, dtype=np.int16)
            return self._porcupine.process(pcm) >= 0
            
        except Exception as e:
            if self._running:
                print(f"Detection error: {e}")
            return False
            
    async def stop_detection(self) -> None:
        """Stop wake word detection."""
        self._running = False
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
        if self._audio:
            try:
                self._audio.terminate()
            except:
                pass
        self._stream = None
        self._audio = None
        
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self._running = False
        await self.stop_detection()
        if self._porcupine:
            self._porcupine.delete()
        if self._executor:
            self._executor.shutdown(wait=True)
            
    async def is_ready(self) -> bool:
        """Check if detector is initialized and ready."""
        return self._porcupine is not None and self._running
