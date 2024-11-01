"""Tests for weather integration."""
import pytest
from datetime import datetime
import logging
from omni.models.intent import Intent, IntentType, IntentSlot, Location
from omni.services.intent.handlers.weather_handler import WeatherHandler
from omni.services.cloud.api.weather_service import WeatherAPI
from omni.core.exceptions import APIError

@pytest.mark.asyncio
class TestWeatherIntegration:
    """Test weather integration."""
    
    @pytest.fixture
    async def handler(self, test_config):
        """Create weather handler."""
        api = WeatherAPI(test_config)
        await api.initialize()
        handler = WeatherHandler(api)
        yield handler
        await api.cleanup()
        
    async def test_current_weather(self, handler):
        """Test getting current weather."""
        intent = Intent(
            type=IntentType.WEATHER,
            confidence=0.9,
            slots={'location': IntentSlot('location', Location(city='London'), 1.0)},
            raw_text="what's the weather in London"
        )
        
        result = await handler.handle(intent)
        assert result.success
        assert result.type == IntentType.WEATHER
        assert 'London' in result.feedback.text
        assert '72' in result.feedback.text
        
    async def test_forecast(self, handler):
        """Test getting forecast."""
        intent = Intent(
            type=IntentType.WEATHER,
            confidence=0.9,
            slots={'location': IntentSlot('location', Location(city='London'), 1.0)},
            raw_text="what's the forecast for London"
        )
        
        result = await handler.handle(intent)
        assert result.success
        assert result.type == IntentType.WEATHER
        assert 'London' in result.feedback.text
        assert 'Partly Cloudy' in result.feedback.text
        
    async def test_invalid_location(self, handler):
        """Test handling invalid location."""
        intent = Intent(
            type=IntentType.WEATHER,
            confidence=0.9,
            slots={'location': IntentSlot('location', Location(city='InvalidCity'), 1.0)},
            raw_text="what's the weather in InvalidCity"
        )
        
        result = await handler.handle(intent)
        assert not result.success
        assert result.needs_followup
        assert result.followup_type == "location"
        assert "invalid" in result.feedback.text.lower()
        
    async def test_missing_location(self, handler):
        """Test handling missing location."""
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
        assert "where" in result.feedback.text.lower()