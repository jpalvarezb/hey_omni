import logging
import re
import dateparser
from typing import Optional, Dict, Any, Tuple
from .engine import Intent, IntentSlot, IntentEngine

class LocalSTI:
    """Local speech-to-intent processing."""
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._engine = IntentEngine()
        self._context = None
        
    async def initialize(self) -> None:
        """Initialize STI processing."""
        await self._engine.initialize()
        
    async def process_speech(self, text: str) -> Intent:
        """Process speech into intent with context."""
        # First get basic intent
        intent = await self._engine.detect_intent(text)
        
        # If we have context, boost confidence for matching intents
        if self._context and self._context == intent.type:
            intent.confidence *= 1.2  # Boost confidence by 20%
            
        # Now enrich the intent with slots based on type
        if intent.type != "unknown":
            intent.slots.update(await self._extract_slots(text, intent.type))
            
        return intent
        
    def set_context(self, context: str) -> None:
        """Set current context for better recognition."""
        self._context = context
        self._logger.debug(f"Context set to: {context}")
        
    async def _extract_slots(self, text: str, intent_type: str) -> Dict[str, IntentSlot]:
        """Extract slots based on intent type."""
        slots = {}
        
        if intent_type == "weather":
            slots.update(await self._extract_weather_slots(text))
        elif intent_type == "calendar":
            slots.update(await self._extract_calendar_slots(text))
        elif intent_type == "timer":
            slots.update(await self._extract_timer_slots(text))
            
        return slots
        
    async def _extract_weather_slots(self, text: str) -> Dict[str, IntentSlot]:
        """Extract weather-specific slots."""
        slots = {}
        
        # Location
        location_match = re.search(r"(?:in|at|for)\s+([\w\s]+?)(?=\s+(?:today|tomorrow|tonight|$)|\s*$)", text)
        if location_match:
            slots["location"] = IntentSlot("location", location_match.group(1), 0.8)
            
        # Time
        time_match = re.search(r"(?:for\s+|at\s+)?(today|tomorrow|tonight|\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)", text)
        if time_match:
            slots["time"] = IntentSlot("time", time_match.group(1), 0.8)
            
        return slots
        
    async def _extract_calendar_slots(self, text: str) -> Dict[str, IntentSlot]:
        """Extract calendar-specific slots."""
        slots = {}
        
        # Action
        action_match = re.search(r"(add|create|delete|remove|update|edit|modify|change)", text)
        if action_match:
            slots["action"] = IntentSlot("action", action_match.group(1), 0.8)
            
        # Time
        time_match = re.search(r"(today|tomorrow|next week|\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)", text)
        if time_match:
            slots["time"] = IntentSlot("time", time_match.group(1), 0.8)
            
        return slots
        
    async def _extract_timer_slots(self, text: str) -> Dict[str, IntentSlot]:
        """Extract timer-specific slots."""
        slots = {}
        
        # Duration
        duration_match = re.search(r"(\d+)\s*(minute|hour|second)s?", text)
        if duration_match:
            slots["duration"] = IntentSlot("duration", 
                                         f"{duration_match.group(1)} {duration_match.group(2)}", 
                                         0.8)
            
        return slots
