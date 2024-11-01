"""Tests for weather handling."""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from omni.models.intent import Intent, IntentSlot, IntentType, IntentFeedback, IntentResult, Location
from omni.services.intent.handlers.weather_handler import WeatherHandler
from omni.services.cloud.api.weather_service import WeatherAPI
from omni.core.exceptions import APIError
from omni.core.config import Config

@pytest.fixture
async def weather_service():
    """Create mock weather service."""
    config = Config()
    config._config = {
        'tomorrow_api': {
            'api_key': 'test_key',
            'units': 'imperial'
        }
    }
    
    service = WeatherAPI(config)
    
    # Mock API methods
    async def get_current_weather(location: str):
        if location == "InvalidCity":
            raise APIError("Location not found")
        return {
            'location': location,
            'temperature': 72,
            'feels_like': 70,
            'condition': 'Clear',
            'description': 'Clear sky',
            'humidity': 45,
            'wind_speed': 5,
            'timestamp': datetime.now()
        }
        
    async def get_forecast(location: str):
        if location == "InvalidCity":
            raise APIError("Location not found")
        return {
            'location': location,
            'forecasts': [
                {
                    'timestamp': datetime.now(),
                    'temperature': 72,
                    'feels_like': 70,
                    'condition': 'Clear',
                    'description': 'Clear sky',
                    'humidity': 45,
                    'wind_speed': 5
                }
            ]
        }
        
    service.get_current_weather = AsyncMock(side_effect=get_current_weather)
    service.get_forecast = AsyncMock(side_effect=get_forecast)
    return service

@pytest.fixture
async def weather_handler(weather_service):
    """Create weather handler with mock service."""
    return WeatherHandler(weather_service)

@pytest.mark.asyncio
async def test_handle_current_weather(weather_handler):
    """Test handling current weather."""
    location = Location(city="London")
    intent = Intent(
        type=IntentType.WEATHER,
        confidence=0.9,
        slots={'location': IntentSlot('location', location, 1.0)},
        raw_text="what's the weather in London"
    )
    
    result = await weather_handler.handle(intent)
    assert isinstance(result, IntentResult)
    assert result.success
    assert isinstance(result.feedback, IntentFeedback)
    assert 'London' in result.feedback.text
    assert '72°F' in result.feedback.text
    assert result.data['condition'] == 'Clear'

@pytest.mark.asyncio
async def test_handle_forecast(weather_handler):
    """Test handling forecast request."""
    location = Location(city="London")
    intent = Intent(
        type=IntentType.WEATHER,
        confidence=0.9,
        slots={
            'location': IntentSlot('location', location, 1.0),
            'time': IntentSlot('time', 'forecast', 1.0)
        },
        raw_text="what's the forecast for London"
    )
    
    result = await weather_handler.handle(intent)
    assert isinstance(result, IntentResult)
    assert result.success
    assert isinstance(result.feedback, IntentFeedback)
    assert 'London' in result.feedback.text
    assert 'forecast' in result.feedback.text.lower()

@pytest.mark.asyncio
async def test_handle_invalid_location(weather_handler):
    """Test handling invalid location."""
    location = Location(city="InvalidCity")
    intent = Intent(
        type=IntentType.WEATHER,
        confidence=0.9,
        slots={'location': IntentSlot('location', location, 1.0)},
        raw_text="what's the weather in InvalidCity"
    )
    
    result = await weather_handler.handle(intent)
    assert isinstance(result, IntentResult)
    assert not result.success
    assert isinstance(result.feedback, IntentFeedback)
    assert "couldn't get the weather" in result.feedback.text.lower()
    assert result.error is not None

@pytest.mark.asyncio
async def test_can_handle(weather_handler):
    """Test intent handling capability check."""
    # Should handle weather intent
    weather_intent = Intent(
        type=IntentType.WEATHER,
        confidence=0.9,
        slots={},
        raw_text="what's the weather"
    )
    assert await weather_handler.can_handle(weather_intent)
    
    # Should not handle other intents
    calendar_intent = Intent(
        type=IntentType.CALENDAR,
        confidence=0.9,
        slots={},
        raw_text="what's on my calendar"
    )
    assert not await weather_handler.can_handle(calendar_intent)

@pytest.mark.asyncio
async def test_get_help(weather_handler):
    """Test help text."""
    help_text = await weather_handler.get_help()
    assert isinstance(help_text, str)
    assert 'weather' in help_text.lower()
    assert 'forecast' in help_text.lower()
    assert 'location' in help_text.lower()