from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime

class IntentType(Enum):
    """Types of intents."""
    WEATHER = "weather"
    CALENDAR = "calendar"
    TIMER = "timer"
    DEVICE = "device"
    UNKNOWN = "unknown"

@dataclass
class Location:
    """Location information for intents."""
    city: str
    state: Optional[str] = None
    country: Optional[str] = None
    confidence: float = 1.0

    def __post_init__(self):
        """Post initialization processing."""
        self.city = self.city.strip().title()
        if self.state:
            self.state = self.state.strip().upper()
        if self.country:
            self.country = self.country.strip().title()

    def __str__(self) -> str:
        """Return string representation."""
        if self.state:
            return f"{self.city}, {self.state}"
        elif self.country:
            return f"{self.city}, {self.country}"
        return self.city

    def __eq__(self, other: object) -> bool:
        """Compare locations."""
        if isinstance(other, str):
            return str(self) == other
        if isinstance(other, Location):
            return (self.city == other.city and 
                   self.state == other.state and 
                   self.country == other.country)
        return False

@dataclass
class IntentSlot:
    """Slot in an intent."""
    name: str
    value: Any
    confidence: float = 1.0

@dataclass
class IntentFeedback:
    """Feedback for intent processing."""
    text: str
    speech: Optional[str] = None
    display: Optional[Dict[str, Any]] = None

@dataclass
class Intent:
    """Intent representation."""
    type: IntentType
    confidence: float
    raw_text: str = ""
    slots: Dict[str, IntentSlot] = field(default_factory=dict)
    sub_intents: List['Intent'] = field(default_factory=list)

    def __post_init__(self):
        """Post initialization validation."""
        if not isinstance(self.slots, dict):
            self.slots = {}

@dataclass
class IntentResult:
    """Result of intent processing."""
    success: bool
    feedback: IntentFeedback
    type: IntentType = IntentType.UNKNOWN
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    needs_followup: bool = False
    followup_type: Optional[str] = None
    followup_options: Optional[List[str]] = None
    slots: Dict[str, IntentSlot] = field(default_factory=dict)

    def __post_init__(self):
        """Post initialization validation."""
        if not isinstance(self.slots, dict):
            self.slots = {}

    @classmethod
    def from_intent(cls, intent: Intent, **kwargs) -> 'IntentResult':
        """Create result from intent."""
        return cls(
            success=True,
            feedback=IntentFeedback(text=""),
            type=intent.type,
            slots=intent.slots.copy(),
            **kwargs
        )
