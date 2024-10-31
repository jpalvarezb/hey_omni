from abc import ABC, abstractmethod
from typing import Optional, Dict, Union
import asyncio
import logging
from ....core.exceptions import TTSError, ResourceInitializationError

class BaseSynthesizer(ABC):
    """Abstract base class for asynchronous speech synthesis."""
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Union[str, int, float]]] = None) -> None:
        """Initialize the synthesizer with optional configuration."""
        pass
        
    @abstractmethod
    async def speak(self, text: str, timeout: Optional[float] = None) -> None:
        """Synthesize and speak text with optional timeout."""
        pass
        
    @abstractmethod
    async def is_speaking(self) -> bool:
        """Check if the synthesizer is currently speaking."""
        pass
        
    @abstractmethod
    async def stop_speaking(self) -> None:
        """Stop current speech synthesis."""
        pass
        
    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if synthesizer is initialized and ready."""
        pass
        
    async def handle_error(self, error: Exception, logger: Optional[logging.Logger] = None) -> None:
        """Handle errors with default logging."""
        log = logger or self._logger
        log.error(f"Synthesis error: {str(error)}", exc_info=True)
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources used by the synthesizer."""
        pass
