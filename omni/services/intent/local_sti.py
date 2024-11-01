from typing import Optional, Dict, Any
import logging
from ...models.intent import Intent, IntentType, IntentSlot, Location
from ...core.config import RECOGNITION_CONTEXTS
from ...utils.main import parse_location, parse_time
from .engine import IntentEngine

class LocalSTI:
    """Local speech-to-intent processor."""
    
    def __init__(self, engine: Optional[IntentEngine] = None):
        """Initialize STI processor."""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._engine = engine or IntentEngine()
        self._context: Optional[Intent] = None
        
    async def process(self, text: str, context: Optional[Intent] = None) -> Intent:
        """Process text into intent."""
        try:
            # Update context
            if context:
                self._context = context
                
            # Extract slots first
            slots = {}
            
            # Try to extract location
            location = parse_location(text)
            if location:
                slots['location'] = IntentSlot('location', location, 1.0)
                
            # Try to extract time
            time_info = parse_time(text)
            if time_info:
                slots['time'] = IntentSlot('time', time_info['datetime'], 1.0)
                
            # Process with engine
            intent = await self._engine.process(text, self._context)
            
            # Add extracted slots
            intent.slots.update(slots)
            
            return intent
            
        except Exception as e:
            self._logger.error(f"Error processing intent: {e}")
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                raw_text=text,
                slots={}
            )
            
    def _refine_intent(self, intent: Intent) -> None:
        """Apply additional refinements to intent."""
        # Adjust confidence based on slot presence
        if intent.type == IntentType.WEATHER and 'location' not in intent.slots:
            intent.confidence *= 0.8
            
        if intent.type == IntentType.CALENDAR and 'time' not in intent.slots:
            intent.confidence *= 0.8
