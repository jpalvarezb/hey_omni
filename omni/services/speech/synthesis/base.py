from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ....core.exceptions import ResourceInitializationError

class BaseSynthesizer(ABC):
    """Base class for speech synthesizers."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize synthesizer.
        
        Raises:
            ResourceInitializationError: If initialization fails
        """
        raise NotImplementedError
        
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            
        Returns:
            bytes: Audio data
        """
        raise NotImplementedError
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        raise NotImplementedError
