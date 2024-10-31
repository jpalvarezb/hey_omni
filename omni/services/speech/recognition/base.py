from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
import asyncio
import logging
from ....core.exceptions import SpeechRecognitionError, ResourceInitializationError

class BaseRecognizer(ABC):
    """Abstract base class for asynchronous speech recognition."""
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Union[str, int, float]]] = None) -> None:
        """Initialize the recognizer with optional configuration."""
        pass
        
    @abstractmethod
    async def start_recognition(self, timeout: Optional[float] = None) -> None:
        """Start the recognition process, with an optional timeout."""
        pass
        
    @abstractmethod
    async def stop_recognition(self, timeout: Optional[float] = None) -> None:
        """Stop the recognition process, with an optional timeout."""
        pass
        
    @abstractmethod
    async def recognize(self, 
                       context: Optional[Dict[str, Any]] = None,
                       timeout: Optional[float] = None) -> Optional[str]:
        """Perform speech recognition with optional context and timeout."""
        pass
        
    @abstractmethod
    async def reset(self) -> None:
        """Reset the recognizer to its initial state without full cleanup."""
        pass
        
    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if the recognizer is initialized and ready for recognition."""
        pass
        
    async def handle_error(self, error: Exception, logger: Optional[logging.Logger] = None) -> None:
        """Handle errors with default logging and optional reset."""
        log = logger or self._logger
        log.error(f"Recognition error: {str(error)}", exc_info=True)
        try:
            await self.reset()
        except Exception as e:
            log.error(f"Error during reset after error: {str(e)}", exc_info=True)
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources used by the recognizer."""
        pass