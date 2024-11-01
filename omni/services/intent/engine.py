import logging
from typing import Optional, Dict, Any, List, Tuple, Set
from dataclasses import dataclass
from omni.core.config import RECOGNITION_CONTEXTS, Config
from omni.utils.main import parse_location, Location, parse_time
from omni.utils.logging import get_logger
from omni.models.intent import Intent, IntentType, IntentSlot, Location
from omni.core.exceptions import IntentError
from datetime import datetime, timedelta

# Get logger at module level
logger = get_logger(__name__)

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

class IntentBuilder:
    """Builder for creating intents."""
    
    def __init__(self, intent_name: str):
        """Initialize intent builder."""
        self.intent_name = intent_name
        self.required = []
        self.optional = []
        
    def require(self, entity_type: str) -> 'IntentBuilder':
        """Add required entity."""
        self.required.append(entity_type)
        return self
        
    def optionally(self, entity_type: str) -> 'IntentBuilder':
        """Add optional entity."""
        self.optional.append(entity_type)
        return self
        
    def build(self) -> Dict[str, Any]:
        """Build intent configuration."""
        return {
            'name': self.intent_name,
            'required': self.required,
            'optional': self.optional
        }

class IntentEngine:
    """Intent processing engine."""
    
    # Confidence thresholds
    BASE_CONFIDENCE = 0.8
    HIGH_CONFIDENCE = 0.9
    CONTEXT_CONFIDENCE = 0.6
    BOOST_CONFIDENCE = 0.2
    
    # Required slots per intent type
    REQUIRED_SLOTS = {
        IntentType.WEATHER: {'location'},
        IntentType.CALENDAR: {'time'},
        IntentType.TIMER: {'time'},
    }
    
    # Location aliases for common abbreviations
    LOCATION_ALIASES = {
        'LA': 'Los Angeles',
        'NYC': 'New York City',
        'SF': 'San Francisco',
        'DC': 'Washington DC'
    }
    
    def __init__(self):
        """Initialize engine."""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._context: Optional[Intent] = None
        self._context_timestamp: Optional[datetime] = None
        
    def _check_required_slots(self, intent_type: IntentType, slots: Dict[str, IntentSlot]) -> Tuple[bool, Set[str]]:
        """Check if all required slots are present.
        
        Args:
            intent_type: Type of intent to check
            slots: Available slots
            
        Returns:
            Tuple of (has_all_required, missing_slots)
        """
        if intent_type not in self.REQUIRED_SLOTS:
            return True, set()
            
        required = self.REQUIRED_SLOTS[intent_type]
        available = set(slots.keys())
        missing = required - available
        return len(missing) == 0, missing
        
    def _normalize_location(self, location: str) -> str:
        """Normalize location name using aliases."""
        return self.LOCATION_ALIASES.get(location.upper(), location)
        
    def _detect_intent_type(self, text: str, slots: Dict[str, IntentSlot]) -> Tuple[IntentType, float]:
        """Detect intent type and confidence."""
        text = text.lower()
        max_confidence = 0.0
        detected_type = IntentType.UNKNOWN
        
        # Check each intent type's patterns
        for intent_name, patterns in RECOGNITION_CONTEXTS.items():
            matches = sum(1 for pattern in patterns if pattern in text)
            if matches > 0:
                # Base confidence from matches
                confidence = self.BASE_CONFIDENCE + (matches / len(patterns)) * 0.2
                
                try:
                    intent_type = IntentType(intent_name)
                    # Check required slots
                    has_required, missing = self._check_required_slots(intent_type, slots)
                    
                    # Adjust confidence based on slots
                    if has_required:
                        confidence += self.BOOST_CONFIDENCE
                    else:
                        confidence *= 0.8  # Reduce confidence if missing required slots
                        
                    if confidence > max_confidence:
                        max_confidence = min(confidence, 1.0)
                        detected_type = intent_type
                        
                except ValueError:
                    self._logger.warning(f"Unknown intent type: {intent_name}")
                    continue
                    
        return detected_type, max_confidence
        
    def _apply_context(self, intent: Intent) -> None:
        """Apply context to refine intent."""
        if not self._context or not self._context_timestamp:
            return
            
        # Check context expiry (5 minutes)
        if datetime.now() - self._context_timestamp > timedelta(minutes=5):
            self._logger.debug("Context expired")
            self._context = None
            self._context_timestamp = None
            return
            
        # If intent type is unknown, inherit from context
        if intent.type == IntentType.UNKNOWN:
            intent.type = self._context.type
            intent.confidence = self.CONTEXT_CONFIDENCE
            self._logger.debug(f"Inherited type from context: {intent.type}")
            
        # If intent type matches context, boost confidence
        elif intent.type == self._context.type:
            old_confidence = intent.confidence
            intent.confidence = min(1.0, intent.confidence + self.BOOST_CONFIDENCE)
            self._logger.debug(
                f"Boosted confidence from {old_confidence} to {intent.confidence}"
            )
            
        # Inherit missing slots from context
        for slot_name, slot in self._context.slots.items():
            if slot_name not in intent.slots:
                intent.slots[slot_name] = slot
                self._logger.debug(f"Inherited slot from context: {slot_name}")
                
    async def process(self, text: str, context: Optional[Intent] = None) -> Intent:
        """Process text into intent."""
        try:
            # Update context
            if context:
                self._context = context
                self._context_timestamp = datetime.now()
                
            # Initialize base intent
            intent = Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                raw_text=text,
                slots={}
            )
            
            # Extract slots
            try:
                time_info = parse_time(text)
                if time_info:
                    intent.slots['time'] = IntentSlot('time', time_info['datetime'], 1.0)
                    self._logger.debug(f"Extracted time slot: {time_info['datetime']}")
            except Exception as e:
                self._logger.warning(f"Time parsing error: {e}")
                
            try:
                location = parse_location(text)
                if location:
                    # Normalize location name
                    location.city = self._normalize_location(location.city)
                    intent.slots['location'] = IntentSlot('location', location, 1.0)
                    self._logger.debug(f"Extracted location slot: {location}")
            except Exception as e:
                self._logger.warning(f"Location parsing error: {e}")
                
            # Determine intent type and confidence
            intent.type, intent.confidence = self._detect_intent_type(text, intent.slots)
            
            # Apply context if available
            self._apply_context(intent)
            
            self._logger.debug(
                f"Processed intent: type={intent.type}, "
                f"confidence={intent.confidence}, slots={intent.slots}"
            )
            
            return intent
            
        except Exception as e:
            self._logger.error(f"Error processing intent: {e}")
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                raw_text=text,
                slots={}
            )
            
    def add_recognition_pattern(self, intent_type: str, pattern: str) -> None:
        """Add new recognition pattern for intent type.
        
        Args:
            intent_type: Type of intent to add pattern for
            pattern: Pattern to add
            
        Raises:
            IntentError: If pattern is invalid
        """
        if not pattern or not isinstance(pattern, str):
            raise IntentError("Invalid pattern")
            
        if not pattern.strip():
            raise IntentError("Empty pattern")
            
        if intent_type not in RECOGNITION_CONTEXTS:
            RECOGNITION_CONTEXTS[intent_type] = []
            
        if pattern not in RECOGNITION_CONTEXTS[intent_type]:
            RECOGNITION_CONTEXTS[intent_type].append(pattern.lower())
            
    def remove_recognition_pattern(self, intent_type: str, pattern: str) -> None:
        """Remove recognition pattern for intent type."""
        if intent_type in RECOGNITION_CONTEXTS:
            try:
                RECOGNITION_CONTEXTS[intent_type].remove(pattern.lower())
            except ValueError:
                pass
                
    def reset_context(self) -> None:
        """Reset context and timestamp."""
        self._context = None
        self._context_timestamp = None
