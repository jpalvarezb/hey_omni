"""Configuration management."""
import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Set
from pathlib import Path
from .exceptions import ConfigError, ResourceInitializationError, ValidationError

# Recognition patterns for intent matching
RECOGNITION_CONTEXTS: Dict[str, List[str]] = {
    'weather': [
        'weather', 'temperature', 'forecast', 'rain', 'sunny',
        'cloudy', 'humidity', 'wind', 'hot', 'cold'
    ],
    'calendar': [
        'calendar', 'schedule', 'meeting', 'appointment', 'event',
        'reminder', 'agenda', 'plan', 'book'
    ],
    'timer': [
        'timer', 'alarm', 'remind', 'wait', 'countdown'
    ],
    'device': [
        'device', 'turn', 'switch', 'set', 'change',
        'on', 'off', 'toggle', 'adjust'
    ]
}

# Tomorrow.io weather codes and descriptions
WEATHER_CODES: Dict[int, Dict[str, str]] = {
    0: {"condition": "Unknown", "description": "Unknown conditions"},
    1000: {"condition": "Clear", "description": "Clear, sunny skies"},
    1100: {"condition": "Mostly Clear", "description": "Mostly clear skies"},
    1101: {"condition": "Partly Cloudy", "description": "Partly cloudy skies"},
    1102: {"condition": "Mostly Cloudy", "description": "Mostly cloudy skies"},
    1001: {"condition": "Cloudy", "description": "Cloudy conditions"},
    2000: {"condition": "Fog", "description": "Foggy conditions"},
    2100: {"condition": "Light Fog", "description": "Light fog"},
    3000: {"condition": "Light Wind", "description": "Light winds"},
    3001: {"condition": "Wind", "description": "Windy conditions"},
    3002: {"condition": "Strong Wind", "description": "Strong winds"},
    4000: {"condition": "Drizzle", "description": "Light drizzle"},
    4001: {"condition": "Rain", "description": "Rain"},
    4200: {"condition": "Light Rain", "description": "Light rain"},
    4201: {"condition": "Heavy Rain", "description": "Heavy rain"},
    5000: {"condition": "Snow", "description": "Snow"},
    5001: {"condition": "Flurries", "description": "Snow flurries"},
    5100: {"condition": "Light Snow", "description": "Light snow"},
    5101: {"condition": "Heavy Snow", "description": "Heavy snow"},
    6000: {"condition": "Freezing Drizzle", "description": "Freezing drizzle"},
    6001: {"condition": "Freezing Rain", "description": "Freezing rain"},
    6200: {"condition": "Light Freezing Rain", "description": "Light freezing rain"},
    6201: {"condition": "Heavy Freezing Rain", "description": "Heavy freezing rain"},
    7000: {"condition": "Ice Pellets", "description": "Ice pellets"},
    7101: {"condition": "Heavy Ice Pellets", "description": "Heavy ice pellets"},
    7102: {"condition": "Light Ice Pellets", "description": "Light ice pellets"},
    8000: {"condition": "Thunderstorm", "description": "Thunderstorm conditions"}
}

@dataclass
class WeatherConfig:
    """Weather API configuration."""
    api_key: str = field(default_factory=lambda: os.getenv('WEATHER_API_KEY', ''))
    base_url: str = "https://api.tomorrow.io/v4"
    units: str = "imperial"
    max_forecast_days: int = 7
    min_forecast_days: int = 3
    default_forecast_days: int = 3
    forecast_patterns: List[str] = field(default_factory=lambda: [
        r'forecast',
        r'tomorrow',
        r'next\s+(?:week|day|month)',
        r'later\s+(?:today|tonight)',
        r'upcoming',
        r'will\s+it\s+(?:rain|snow|be)'
    ])
    location_prompts: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("Where would you like to know the weather for?", 
         "What location would you like the weather for?"),
        ("Which city's weather are you interested in?",
         "Which city would you like to check?"),
        ("Could you tell me the location you're asking about?",
         "What place did you want to check?")
    ])
    invalid_cities: Set[str] = field(default_factory=lambda: {
        'invalidcity', 'invalid', 'null', 'undefined', 'none'
    })
    city_pattern: str = r'^[A-Za-zÀ-ÿ\s\-]+$'
    timesteps: Dict[str, str] = field(default_factory=lambda: {
        'current': 'current',
        'daily': '1d'
    })
    fields: Dict[str, List[str]] = field(default_factory=lambda: {
        'current': [
            'temperature',
            'temperatureApparent',
            'humidity',
            'windSpeed',
            'weatherCode'
        ],
        'daily': [
            'temperatureMax',
            'temperatureMin',
            'temperatureApparent',
            'humidity',
            'windSpeed',
            'weatherCode'
        ]
    })
    weather_codes: Dict[int, Dict[str, str]] = field(default_factory=lambda: WEATHER_CODES)
    
    def is_valid(self) -> bool:
        """Check if the configuration is valid."""
        return bool(self.api_key and self.base_url)
        
    def validate(self) -> None:
        """Validate configuration and raise error if invalid."""
        if not self.api_key:
            raise ConfigError("Weather API key is missing")
        if not self.base_url:
            raise ConfigError("Weather API base URL is missing")
        if not self.units in ['imperial', 'metric']:
            raise ConfigError(f"Invalid units: {self.units}")
        if not 0 < self.min_forecast_days <= self.max_forecast_days:
            raise ConfigError("Invalid forecast day limits")
        if not self.min_forecast_days <= self.default_forecast_days <= self.max_forecast_days:
            raise ConfigError("Invalid default forecast days")
        if not self.timesteps or not all(self.timesteps.values()):
            raise ConfigError("Invalid timesteps configuration")
        if not self.fields or not all(self.fields.values()):
            raise ConfigError("Invalid fields configuration")

@dataclass
class IntentConfig:
    """Intent configuration."""
    confidence: Dict[str, float] = field(default_factory=lambda: {
        'base': 0.8,
        'high': 0.9,
        'context': 0.6,
        'boost': 0.2
    })
    context_expiry_minutes: int = 5
    recognition_contexts: Dict[str, List[str]] = field(default_factory=lambda: RECOGNITION_CONTEXTS)
    
    def is_valid(self) -> bool:
        """Check if the configuration is valid."""
        return (
            all(0 <= v <= 1 for v in self.confidence.values()) and
            self.context_expiry_minutes > 0 and
            bool(self.recognition_contexts)
        )
        
    def validate(self) -> None:
        """Validate configuration and raise error if invalid."""
        if not all(0 <= v <= 1 for v in self.confidence.values()):
            raise ConfigError("Confidence values must be between 0 and 1")
        if self.context_expiry_minutes <= 0:
            raise ConfigError("Context expiry must be positive")
        if not self.recognition_contexts:
            raise ConfigError("Recognition contexts are missing")

@dataclass
class Config:
    """Application configuration."""
    intent: IntentConfig = field(default_factory=IntentConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    config_path: str = field(default='config.yaml')
    
    async def load(self) -> None:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f)
                    if data:
                        # Load intent configuration
                        if 'intent' in data:
                            intent_data = data['intent']
                            if 'confidence' in intent_data:
                                self.intent.confidence.update(intent_data['confidence'])
                            if 'context_expiry_minutes' in intent_data:
                                self.intent.context_expiry_minutes = intent_data['context_expiry_minutes']
                            if 'recognition_contexts' in intent_data:
                                self.intent.recognition_contexts.update(intent_data['recognition_contexts'])
                                
                        # Load weather configuration
                        if 'weather' in data:
                            weather_data = data['weather']
                            if 'api_key' in weather_data:
                                self.weather.api_key = weather_data['api_key']
                            if 'base_url' in weather_data:
                                self.weather.base_url = weather_data['base_url']
                            if 'units' in weather_data:
                                self.weather.units = weather_data['units']
                            if 'timesteps' in weather_data:
                                self.weather.timesteps.update(weather_data['timesteps'])
                            if 'fields' in weather_data:
                                self.weather.fields.update(weather_data['fields'])
                                
            # Validate configurations
            self.validate()
            
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {str(e)}")
            
    def validate(self) -> None:
        """Validate all configurations."""
        self.intent.validate()
        self.weather.validate()
            
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value by path."""
        try:
            value = self
            for key in path.split('.'):
                value = getattr(value, key)
            return value
        except AttributeError:
            return default
