from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ....core.exceptions import ResourceInitializationError

class BaseRecognizer(ABC):
    """Base class for speech recognizers."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize recognizer.
        
        Raises:
            ResourceInitializationError: If initialization fails
        """
        raise NotImplementedError
        
    @abstractmethod
    async def start_recognition(self) -> None:
        """Start recognition session."""
        raise NotImplementedError
        
    @abstractmethod
    async def stop_recognition(self) -> None:
        """Stop recognition session."""
        raise NotImplementedError
        
    @abstractmethod
    async def process_audio(self, audio_data: bytes) -> Optional[str]:
        """Process audio data.
        
        Args:
            audio_data: Raw audio bytes to process
            
        Returns:
            Optional[str]: Recognized text if any
        """
        raise NotImplementedError
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        raise NotImplementedError