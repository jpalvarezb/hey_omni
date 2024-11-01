"""Tests for intent engine."""
import pytest
from datetime import datetime, timedelta
import logging
from omni.models.intent import Intent, IntentType, IntentSlot, Location
from omni.services.intent.engine import IntentEngine
from omni.core.exceptions import IntentError

@pytest.mark.asyncio
class TestIntentEngine:
    """Test intent engine functionality."""
    
    @pytest.fixture
    async def engine(self):
        """Create intent engine."""
        return IntentEngine()
        
    async def test_multi_intent_ambiguity(self, engine):
        """Test handling ambiguous intents."""
        # Test weather intent with high confidence
        text = "what's the weather in London"
        intent = await engine.process(text)
        
        assert intent.type == IntentType.WEATHER
        assert intent.confidence >= engine.BASE_CONFIDENCE
        assert 'location' in intent.slots
        assert intent.slots['location'].value.city == "London"
        
    async def test_dynamic_confidence_thresholds(self, engine):
        """Test confidence threshold adjustments."""
        # Test with required slots
        text = "what's the weather in London"
        intent = await engine.process(text)
        base_confidence = intent.confidence
        
        # Test without required slots
        text = "what's the weather"
        intent = await engine.process(text)
        assert intent.confidence < base_confidence
        
    async def test_contextual_intent_resolution(self, engine):
        """Test context-based intent resolution."""
        # Set weather context
        context = Intent(
            type=IntentType.WEATHER,
            confidence=0.9,
            slots={'location': IntentSlot('location', Location(city='London'), 1.0)},
            raw_text="what's the weather in London"
        )
        
        # Test follow-up query
        result = await engine.process("and tomorrow", context)
        assert result.type == IntentType.WEATHER
        assert 'location' in result.slots
        assert result.slots['location'].value.city == "London"
        assert result.confidence >= engine.CONTEXT_CONFIDENCE
        
    async def test_slot_inheritance(self, engine):
        """Test slot inheritance from context."""
        # Set context with location
        context = Intent(
            type=IntentType.WEATHER,
            confidence=0.9,
            slots={'location': IntentSlot('location', Location(city='London'), 1.0)},
            raw_text="what's the weather in London"
        )
        
        # Test inheriting location
        result = await engine.process("how about tomorrow", context)
        assert 'location' in result.slots
        assert result.slots['location'].value.city == "London"
        
    async def test_confidence_boost_with_slots(self, engine):
        """Test confidence boosting with slots."""
        # Test without location
        text = "what's the weather"
        result = await engine.process(text)
        base_confidence = result.confidence
        
        # Test with location
        text = "what's the weather in London"
        result = await engine.process(text)
        assert result.confidence > base_confidence
        
    async def test_location_aliases(self, engine):
        """Test location alias handling."""
        text = "what's the weather in LA"
        result = await engine.process(text)
        assert result.slots['location'].value.city == "Los Angeles"
        
        text = "what's the weather in NYC"
        result = await engine.process(text)
        assert result.slots['location'].value.city == "New York City"
        
    async def test_required_slots(self, engine):
        """Test required slots checking."""
        # Weather intent requires location
        text = "what's the weather"
        result = await engine.process(text)
        assert result.confidence < engine.BASE_CONFIDENCE
        
        # Calendar intent requires time
        text = "schedule a meeting"
        result = await engine.process(text)
        assert result.confidence < engine.BASE_CONFIDENCE
        
    async def test_context_expiry(self, engine):
        """Test context expiration."""
        # Set old context
        context = Intent(
            type=IntentType.WEATHER,
            confidence=0.9,
            slots={'location': IntentSlot('location', Location(city='London'), 1.0)},
            raw_text="what's the weather in London"
        )
        engine._context = context
        engine._context_timestamp = datetime.now() - timedelta(minutes=6)  # Expired
        
        # Test that expired context isn't used
        result = await engine.process("how about now")
        assert 'location' not in result.slots
        
    async def test_unknown_intent_handling(self, engine):
        """Test handling unknown intents."""
        text = "play some music"  # Not a recognized intent
        result = await engine.process(text)
        
        assert result.type == IntentType.UNKNOWN
        assert result.confidence < engine.BASE_CONFIDENCE
        
    async def test_error_handling(self, engine):
        """Test error handling."""
        # Test with None input
        result = await engine.process(None)  # type: ignore
        assert result.type == IntentType.UNKNOWN
        assert result.confidence == 0.0
        
        # Test with empty string
        result = await engine.process("")
        assert result.type == IntentType.UNKNOWN
        assert result.confidence == 0.0
        