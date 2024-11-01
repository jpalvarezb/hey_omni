"""Tests for weather handler."""
import pytest
from datetime import datetime
import logging
from omni.models.intent import Intent, IntentType, IntentSlot, Location, IntentResult
from omni.services.intent.handlers.weather_handler import WeatherHandler
from omni.core.exceptions import APIError

@pytest.mark.asyncio
class TestWeatherHandler:
    """Test weather handler functionality."""
    
    @pytest.fixture
    async def handler(self, mock_weather_api):
        """Create weather handler."""
        return WeatherHandler(mock_weather_api)
        
    async def test_handle_current_weather(self, handler):
        """Test handling current weather request."""
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
        assert '72' in result.feedback.text  # Mock temperature
        assert 'Clear' in result.feedback.text  # Mock condition
        
    async def test_handle_forecast(self, handler):
        """Test handling forecast request."""
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
        assert 'Partly Cloudy' in result.feedback.text  # Mock condition
        
    async def test_handle_invalid_location(self, handler):
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
        
    async def test_low_confidence(self, handler):
        """Test handling low confidence intent."""
        intent = Intent(
            type=IntentType.WEATHER,
            confidence=0.3,  # Below threshold
            slots={'location': IntentSlot('location', Location(city='London'), 1.0)},
            raw_text="maybe weather London"
        )
        
        result = await handler.handle(intent)
        assert not result.success
        assert "confidence" in result.error.lower()
        
    async def test_invalid_city_format(self, handler):
        """Test handling invalid city format."""
        intent = Intent(
            type=IntentType.WEATHER,
            confidence=0.9,
            slots={'location': IntentSlot('location', Location(city='123'), 1.0)},
            raw_text="what's the weather in 123"
        )
        
        result = await handler.handle(intent)
        assert not result.success
        assert result.needs_followup
        assert result.followup_type == "location"
        assert "invalid" in result.feedback.text.lower()
        
    async def test_complex_location(self, handler):
        """Test handling complex location."""
        intent = Intent(
            type=IntentType.WEATHER,
            confidence=0.9,
            slots={'location': IntentSlot('location', Location(city='São Paulo'), 1.0)},
            raw_text="what's the weather in São Paulo"
        )
        
        result = await handler.handle(intent)
        assert result.success
        assert 'São Paulo' in result.feedback.text
        assert '72' in result.feedback.text  # Mock temperature
        
    async def test_location_with_state(self, handler):
        """Test handling location with state."""
        intent = Intent(
            type=IntentType.WEATHER,
            confidence=0.9,
            slots={'location': IntentSlot('location', Location(city='Miami', state='FL'), 1.0)},
            raw_text="what's the weather in Miami, FL"
        )
        
        result = await handler.handle(intent)
        assert result.success
        assert 'Miami' in result.feedback.text
        assert '72' in result.feedback.text  # Mock temperature