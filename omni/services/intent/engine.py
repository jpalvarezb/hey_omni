import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class IntentSlot:
    """Represents a slot in an intent."""
    name: str
    value: Any
    confidence: float

@dataclass
class Intent:
    """Represents a processed intent."""
    type: str
    confidence: float
    slots: Dict[str, IntentSlot]
    raw_text: str

class IntentEngine:
    """Core engine for basic intent detection."""
    
    # Basic intent patterns
    INTENT_TYPES = {
        "weather": ["weather", "temperature", "forecast"],
        "calendar": ["calendar", "schedule", "event", "meeting"],
        "timer": ["timer", "remind", "alarm"],
        "device": ["device", "turn", "switch"]
    }
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the intent engine."""
        try:
            self._initialized = True
            self._logger.info("Intent engine initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize intent engine: {e}")
            raise
            
    async def detect_intent(self, text: str) -> Intent:
        """Detect basic intent from text."""
        if not self._initialized:
            await self.initialize()
            
        try:
            text = text.lower().strip()
            best_match = None
            best_confidence = 0.0
            
            # Basic intent matching
            for intent_type, keywords in self.INTENT_TYPES.items():
                matches = [word for word in keywords if word in text]
                if matches:
                    confidence = len(matches) / len(keywords)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = intent_type
                        
            if best_match:
                return Intent(
                    type=best_match,
                    confidence=best_confidence,
                    slots={},  # Let handlers fill slots
                    raw_text=text
                )
                
            return Intent(
                type="unknown",
                confidence=0.0,
                slots={},
                raw_text=text
            )
            
        except Exception as e:
            self._logger.error(f"Error detecting intent: {e}")
            return Intent(
                type="error",
                confidence=0.0,
                slots={"error": IntentSlot("error", str(e), 1.0)},
                raw_text=text
            )
            
    async def cleanup(self) -> None:
        """Cleanup engine resources."""
        self._initialized = False
        self._logger.info("Intent engine cleaned up")
