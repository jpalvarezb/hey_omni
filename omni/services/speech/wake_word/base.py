from abc import ABC, abstractmethod
from typing import Optional, Dict, Union

class BaseWakeWordDetector(ABC):
    """Abstract base class for wake word detection."""
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Union[str, int, float]]] = None) -> None:
        """Initialize the wake word detector."""
        pass
        
    @abstractmethod
    async def start_detection(self) -> None:
        """Start wake word detection."""
        pass
        
    @abstractmethod
    async def stop_detection(self) -> None:
        """Stop wake word detection."""
        pass
        
    @abstractmethod
    async def detect(self) -> bool:
        """Check for wake word detection."""
        pass
        
    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if detector is initialized and ready."""
        pass
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass
