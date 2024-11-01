"""Edge computing processor."""
import logging
from typing import Optional
from datetime import datetime
from ..speech.recognition.base import BaseRecognizer
from ..speech.synthesis.base import BaseSynthesizer
from ..speech.wake_word.base import BaseWakeWordDetector
from ...core.exceptions import ProcessorError
from ...models.intent import Intent, IntentType, IntentResult, IntentFeedback
from .cache.memory_cache import MemoryCache
from ...utils.main import parse_location
from ...models.intent import IntentSlot

class EdgeProcessor:
    """Edge computing processor for offline capabilities."""
    
    def __init__(self, 
                 cache: MemoryCache,
                 recognizer: Optional[BaseRecognizer] = None,
                 synthesizer: Optional[BaseSynthesizer] = None,
                 wake_word_detector: Optional[BaseWakeWordDetector] = None):
        """Initialize edge processor."""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._cache = cache
        self._recognizer = recognizer
        self._synthesizer = synthesizer
        self._wake_word_detector = wake_word_detector
        self._online_available = True
        
    async def process_offline(self, text: str) -> IntentResult:
        """Process text in offline mode."""
        try:
            # Check cache first
            cached = await self._cache.get(text)
            if cached:
                self._logger.info(f"Using cached result for: {text}")
                return self._format_cached_result(cached)
                
            # Process using offline components
            intent = Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                raw_text=text,
                slots={}
            )
            
            # Extract location
            location = parse_location(text)
            if location:
                intent.slots['location'] = IntentSlot('location', location, 1.0)
                
            # Basic offline intent determination
            if any(word in text.lower() for word in ['weather', 'temperature', 'forecast']):
                intent.type = IntentType.WEATHER
                intent.confidence = 0.6  # Lower confidence for offline
                
            elif any(word in text.lower() for word in ['calendar', 'schedule', 'meeting']):
                intent.type = IntentType.CALENDAR
                intent.confidence = 0.6
                
            # Create result with slots
            result = IntentResult(
                success=True,
                feedback=IntentFeedback(
                    text="I understand you, but I'm in offline mode.",
                    speech="I'm currently offline."
                ),
                data={
                    'intent': {
                        'type': intent.type.value,
                        'confidence': intent.confidence,
                        'text': text
                    },
                    'timestamp': datetime.now().isoformat(),
                    'offline': True
                },
                type=intent.type,
                slots=intent.slots  # Pass slots to result
            )
            
            # Cache result
            await self._cache.set(text, result)
            return result
            
        except Exception as e:
            self._logger.error(f"Failed to process offline: {e}")
            return IntentResult(
                success=False,
                feedback=IntentFeedback(
                    text=f"Error processing request: {str(e)}",
                    speech="Sorry, I encountered an error."
                ),
                error=str(e),
                type=IntentType.UNKNOWN,
                slots={}
            )
            
    def _format_cached_result(self, cached: dict) -> IntentResult:
        """Format cached result into IntentResult."""
        return IntentResult(
            success=cached.get('success', False),
            feedback=IntentFeedback(
                text=cached.get('feedback', {}).get('text', 'Cached response'),
                speech=cached.get('feedback', {}).get('speech', 'Cached response')
            ),
            data=cached.get('data'),
            error=cached.get('error'),
            type=IntentType(cached.get('data', {}).get('intent', {}).get('type', 'unknown'))
        )
            
    @property
    def online_available(self) -> bool:
        """Check if online processing is available."""
        return self._online_available
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._recognizer:
            await self._recognizer.cleanup()
        if self._synthesizer:
            await self._synthesizer.cleanup()
        if self._wake_word_detector:
            await self._wake_word_detector.cleanup()
