"""Test configuration and fixtures."""
import pytest
import os
from datetime import datetime
from omni.core.config import Config, WeatherConfig
from omni.core.exceptions import ConfigError

@pytest.fixture
async def test_config():
    """Create test configuration."""
    config = Config()
    
    # Set required values
    config.weather.api_key = 'test_api_key'  # This is required
    config.weather.base_url = 'http://test.api'
    config.weather.units = 'imperial'
    
    # Skip validation for testing
    config.weather.validate = lambda: None
    
    # Load default values
    await config.load()
    
    return config

@pytest.fixture
async def mock_weather_api(test_config):
    """Create mock weather API."""
    from omni.services.cloud.api.weather_service import WeatherAPI
    
    api = WeatherAPI(test_config)
    await api.initialize()
    
    # Mock response data
    api._mock_data = {
        'current': {
            'temperature': 72,
            'temperatureApparent': 70,
            'humidity': 45,
            'windSpeed': 5,
            'weatherCode': 1000,
            'condition': 'Clear',
            'description': 'Clear sky',
            'timestamp': datetime.now()
        },
        'forecast': [{
            'temperature': 75,
            'temperatureApparent': 73,
            'humidity': 50,
            'windSpeed': 8,
            'weatherCode': 1100,
            'condition': 'Partly Cloudy',
            'description': 'Partly cloudy skies',
            'timestamp': datetime.now()
        }]
    }
    
    return api

@pytest.fixture
async def mock_intent_engine(test_config):
    """Create mock intent engine."""
    from omni.services.intent.engine import IntentEngine
    return IntentEngine(test_config)

@pytest.fixture
async def mock_weather_handler(mock_weather_api):
    """Create mock weather handler."""
    from omni.services.intent.handlers.weather_handler import WeatherHandler
    return WeatherHandler(mock_weather_api)

@pytest.fixture(autouse=True)
def cleanup_env():
    """Clean up environment after tests."""
    yield
    # Clean up any environment variables
    if 'WEATHER_API_KEY' in os.environ:
        del os.environ['WEATHER_API_KEY']