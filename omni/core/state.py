"""Application state management."""
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class AppState:
    """Application state."""
    online: bool = True
    debug: bool = False
    current_intent: Optional[str] = None
    context: Dict[str, Any] = None
