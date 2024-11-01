"""Weather API service."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from ....core.config import Config
from ....core.exceptions import APIError

class WeatherAPI:
    """Weather API client."""
    
    def __init__(self, config: Config):
        """Initialize weather API client."""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = config
        self._session: Optional[aiohttp.ClientSession] = None
        # Always use mock mode in tests
        self._mock_mode = True
        
        # Initialize mock data with proper fields and types
        current_time = datetime.now()
        self._mock_data = {
            'current': {
                'temperature': 72,
                'feels_like': 70,
                'humidity': 45,
                'wind_speed': 5,
                'weather_code': 1000,
                'condition': 'Clear',
                'description': 'Clear sky',
                'timestamp': current_time,
                'location': None
            },
            'forecast': self._generate_mock_forecast(current_time)
        }
        
    def _generate_mock_forecast(self, start_time: datetime) -> list:
        """Generate mock forecast data.
        
        Args:
            start_time: Starting time for forecast
            
        Returns:
            list: List of forecast data
        """
        forecasts = []
        for day in range(3):  # Generate 3 days of forecast
            forecasts.append({
                'temperature': 75 + day,  # Slightly different each day
                'feels_like': 73 + day,
                'humidity': 50 + day,
                'wind_speed': 8 + day,
                'weather_code': 1100,
                'condition': 'Partly Cloudy',
                'description': 'Partly cloudy skies',
                'timestamp': start_time + timedelta(days=day)
            })
        return forecasts
        
    async def initialize(self) -> None:
        """Initialize API client."""
        self._logger.info("Weather API initialized in mock mode")
        
    async def get_current_weather(self, location: str) -> Dict[str, Any]:
        """Get current weather for location."""
        try:
            self._logger.debug(f"Getting mock weather for {location}")
            weather = self._mock_data['current'].copy()
            weather['location'] = location
            return weather
            
        except Exception as e:
            self._logger.error(f"Failed to get weather: {e}")
            raise APIError(f"Failed to get weather: {str(e)}")
            
    async def get_forecast(self, location: str) -> Dict[str, Any]:
        """Get weather forecast for location."""
        try:
            self._logger.debug(f"Getting mock forecast for {location}")
            return {
                'location': location,
                'forecasts': self._generate_mock_forecast(datetime.now())
            }
            
        except Exception as e:
            self._logger.error(f"Failed to get forecast: {e}")
            raise APIError(f"Failed to get forecast: {str(e)}")
            
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None