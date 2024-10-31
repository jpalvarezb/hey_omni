import asyncio
from typing import Optional, Dict, Union, Set
import pyttsx3
from concurrent.futures import ThreadPoolExecutor
from ....core.exceptions import TTSError, ResourceInitializationError
from .base import BaseSynthesizer

class LocalTTSEngine(BaseSynthesizer):
    """Local text-to-speech synthesis using pyttsx3."""
    
    ESSENTIAL_CONFIG_KEYS: Set[str] = {'rate', 'volume', 'voice'}
    
    def __init__(self):
        super().__init__()
        self._engine = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._lock = asyncio.Lock()
        self._initialized = False
        self._speaking = False
        self._config = {}
        self._available_voices = {}
        
    def _extract_config(self, config: Optional[Dict[str, Union[str, int, float]]] = None) -> Dict[str, Union[str, int, float]]:
        """Extract essential configuration parameters."""
        if not config:
            return {}
        return {k: config[k] for k in self.ESSENTIAL_CONFIG_KEYS if k in config}
        
    async def _init_with_retry(self, config: Optional[Dict[str, Union[str, int, float]]] = None) -> None:
        """Initialize TTS engine with retry mechanism."""
        retries = 3
        last_error = None
        
        for attempt in range(retries):
            try:
                def _init():
                    engine = pyttsx3.init()
                    self._available_voices = {voice.id: voice for voice in engine.getProperty('voices')}
                    self._logger.debug(f"Available voices: {list(self._available_voices.keys())}")
                    
                    if config:
                        if 'voice' in config:
                            if config['voice'] not in self._available_voices:
                                self._logger.warning(
                                    f"Requested voice '{config['voice']}' not available. Using default."
                                )
                            else:
                                engine.setProperty('voice', config['voice'])
                                self._logger.debug(f"Set voice to: {config['voice']}")
                                
                        if 'rate' in config:
                            engine.setProperty('rate', config['rate'])
                            self._logger.debug(f"Set rate to: {config['rate']}")
                            
                        if 'volume' in config:
                            engine.setProperty('volume', config['volume'])
                            self._logger.debug(f"Set volume to: {config['volume']}")
                            
                    return engine
                    
                self._engine = await asyncio.get_event_loop().run_in_executor(
                    self._executor, _init
                )
                self._config = self._extract_config(config)
                self._logger.debug("Engine initialization successful")
                return
                
            except Exception as e:
                last_error = e
                self._logger.warning(f"Initialization attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    
        raise ResourceInitializationError(f"Failed to initialize after {retries} attempts: {last_error}")
        
    async def _speak_with_timeout(self, text: str, timeout: Optional[float] = None) -> None:
        """Perform speech synthesis with timeout."""
        def _speak():
            self._engine.say(text)
            self._engine.runAndWait()
            
        if timeout:
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(self._executor, _speak),
                timeout=timeout
            )
        else:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, _speak
            )
            
    async def initialize(self, config: Optional[Dict[str, Union[str, int, float]]] = None) -> None:
        """Initialize the TTS engine with configuration."""
        if self._initialized:
            self._logger.debug("Engine already initialized")
            return
            
        try:
            await self._init_with_retry(config)
            self._initialized = True
            self._logger.info("Local TTS engine initialized successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to initialize TTS engine: {str(e)}")
            raise ResourceInitializationError(f"TTS initialization failed: {str(e)}")
            
    async def speak(self, text: str, timeout: Optional[float] = None) -> None:
        """Synthesize and speak text."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            try:
                self._speaking = True
                self._logger.debug(f"Starting speech synthesis")
                
                def _speak():
                    try:
                        self._engine.say(text)
                        self._engine.runAndWait()
                    finally:
                        self._speaking = False
                        
                # Run in executor and wait for completion
                await asyncio.get_event_loop().run_in_executor(
                    self._executor, _speak
                )
                self._logger.debug("Speech synthesis completed")
                
            except Exception as e:
                self._speaking = False
                self._logger.error(f"Speech synthesis failed: {e}")
                raise TTSError(f"Speech synthesis failed: {e}")
                
    async def is_speaking(self) -> bool:
        """Check if the synthesizer is currently speaking."""
        return self._speaking
        
    async def stop_speaking(self) -> None:
        """Stop current speech synthesis."""
        if self._speaking and self._engine:
            try:
                def _stop():
                    self._engine.stop()
                    self._speaking = False
                    
                await asyncio.get_event_loop().run_in_executor(
                    self._executor, _stop
                )
                self._logger.debug("Speech stopped")
            except Exception as e:
                self._logger.error(f"Failed to stop speech: {e}")
            finally:
                self._speaking = False
                
    async def is_ready(self) -> bool:
        """Check if synthesizer is initialized and ready."""
        return self._initialized and self._engine is not None
        
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._speaking:
            await self.stop_speaking()
            
        if self._executor:
            try:
                self._executor.shutdown(wait=True)
                self._logger.debug("TTS executor shutdown complete")
            except Exception as e:
                self._logger.error(f"Error shutting down TTS executor: {str(e)}")
                
        self._initialized = False
        self._engine = None
