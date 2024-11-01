"""Tests for local STI."""
import pytest
from datetime import datetime
import logging
from omni.models.intent import Intent, IntentType, IntentSlot, Location
from omni.services.intent.local_sti import LocalSTI
from omni.services.intent.engine import IntentEngine

@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for tests."""
    logging.basicConfig(level=logging.DEBUG)

@pytest.mark.asyncio
class TestLocalSTI:
    """Test local STI functionality."""
    
    @pytest.fixture
    async def sti(self):
        """Create STI instance."""
        engine = IntentEngine()
        return LocalSTI(engine)
        
    async def test_complex_time_expressions(self, sti):
        """Test handling complex time expressions."""
        text = "what's the weather tomorrow at 3pm"
        result = await sti.process(text)
        
        assert result.type == IntentType.WEATHER
        assert 'time' in result.slots
        time_slot = result.slots['time']
        assert time_slot.value.hour == 15
        
    async def test_complex_location_handling(self, sti):
        """Test handling complex locations."""
        text = "what's the weather in São Paulo"
        result = await sti.process(text)
        
        assert result.type == IntentType.WEATHER
        assert 'location' in result.slots
        location = result.slots['location'].value
        assert location.city == "São Paulo"