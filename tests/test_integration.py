"""Integration tests."""
import pytest
from datetime import datetime
from omni.core.config import Config
from omni.models.intent import Intent, IntentType, IntentSlot, Location
from omni.services.intent.engine import IntentEngine
from omni.services.intent.local_sti import LocalSTI
from omni.services.cloud.api.weather_service import WeatherAPI
from omni.services.intent.handlers.weather_handler import WeatherHandler

@pytest.mark.integration
class TestWeatherIntegration:
    """Integration tests for weather processing."""
    
    @pytest.fixture
    async def setup_components(self):
        """Set up test components."""
        config = Config()
        await config.load()
        
        engine = IntentEngine()
        sti = LocalSTI(engine)
        weather_api = WeatherAPI(config)
        await weather_api.initialize()
        handler = WeatherHandler(weather_api)
        
        return engine, sti, handler
        
    async def test_missing_location_followup(self, setup_components):
        """Test handling missing location."""
        _, sti, handler = setup_components
        
        # Process intent without location
        intent = Intent(
            type=IntentType.WEATHER,
            confidence=0.9,
            slots={},
            raw_text="what's the weather"
        )
        
        result = await handler.handle(intent)
        assert not result.success
        assert result.needs_followup
        assert result.followup_type == "location"