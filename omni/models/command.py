"""Command data models."""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class CommandType(Enum):
    """Types of commands."""
    SYSTEM = "system"
    USER = "user"
    DEVICE = "device"
    UNKNOWN = "unknown"

@dataclass
class Command:
    """Command representation."""
    type: CommandType
    action: str
    timestamp: datetime = field(default_factory=datetime.now)
    params: Optional[Dict[str, Any]] = None
    source: str = "user"
    target: str = "system"
    priority: int = 0
    
    def __post_init__(self):
        """Post initialization processing."""
        if not isinstance(self.type, CommandType):
            raise ValueError(f"Invalid command type: {self.type}")
        if not self.action:
            raise ValueError("Command action cannot be empty")
        if self.params is None:
            self.params = {}
