"""Tests for weather API."""
import pytest
from datetime import datetime
import logging
from omni.services.cloud.api.weather_service import WeatherAPI
from omni.core.exceptions import APIError

@pytest.mark.asyncio
class TestWeatherAPI:
    """Test weather API functionality."""
    
    @pytest.fixture
    async def api(self, test_config):
        """Create weather API instance."""
        api = WeatherAPI(test_config)
        await api.initialize()
        yield api
        await api.cleanup()
        
    async def test_get_current_weather(self, api):
        """Test getting current weather."""
        result = await api.get_current_weather("London")
        assert result['location'] == 'London'
        assert result['temperature'] == 72
        assert result['feels_like'] == 70
        assert result['condition'] == 'Clear'
        assert isinstance(result['timestamp'], datetime)
        
    async def test_get_forecast(self, api):
        """Test getting forecast."""
        result = await api.get_forecast("London")
        assert result['location'] == 'London'
        assert len(result['forecasts']) == 3  # 3 days of forecast
        
        forecast = result['forecasts'][0]
        assert forecast['temperature'] == 75
        assert forecast['feels_like'] == 73
        assert forecast['condition'] == 'Partly Cloudy'
        assert isinstance(forecast['timestamp'], datetime)
        
    async def test_invalid_location(self, api):
        """Test handling invalid location."""
        # In mock mode, any location should work
        result = await api.get_current_weather("InvalidCity")
        assert result['location'] == 'InvalidCity'
        assert result['temperature'] == 72
        
    async def test_special_characters(self, api):
        """Test handling location with special characters."""
        result = await api.get_current_weather("São Paulo")
        assert result['location'] == 'São Paulo'
        assert result['temperature'] == 72
        
    async def test_location_with_state(self, api):
        """Test handling location with state."""
        result = await api.get_current_weather("Miami, FL")
        assert result['location'] == 'Miami, FL'
        assert result['temperature'] == 72
        
    async def test_cleanup(self, api):
        """Test API cleanup."""
        await api.cleanup()  # Should not raise any errors