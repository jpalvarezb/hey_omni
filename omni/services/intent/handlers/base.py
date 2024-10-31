from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..engine import Intent

class BaseIntentHandler(ABC):
    """Base class for all intent handlers."""
    
    @abstractmethod
    async def can_handle(self, intent: Intent) -> bool:
        """Check if this handler can process the intent."""
        pass
        
    @abstractmethod
    async def handle(self, intent: Intent) -> Dict[str, Any]:
        """Handle the intent and return result."""
        pass
        
    @abstractmethod
    async def get_help(self) -> str:
        """Get help text for this handler."""
        pass 