import yaml
import platform
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class PlatformConfig:
    """Platform-specific configuration."""
    audio_buffer_size: int
    retry_delay: float
    max_retries: int = 3
    startup_delay: float = 0.5

class Config:
    """Application configuration management."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.yaml"
        self._config: Dict[str, Any] = {}
        self._platform = platform.system()
        
    async def load(self) -> None:
        """Load configuration from file."""
        try:
            async with aiofiles.open(self.config_path, 'r') as f:
                content = await f.read()
                self._config = yaml.safe_load(content)
        except FileNotFoundError:
            self._config = self._get_default_config()
            # Save default config
            await self.save()
            
    async def save(self) -> None:
        """Save configuration to file."""
        async with aiofiles.open(self.config_path, 'w') as f:
            await f.write(yaml.dump(self._config))
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'platform_config': {
                'Darwin': {
                    'audio_buffer_size': 2048,
                    'retry_delay': 0.5,
                    'max_retries': 3,
                    'startup_delay': 0.5
                },
                'Windows': {
                    'audio_buffer_size': 4096,
                    'retry_delay': 1.0,
                    'max_retries': 3,
                    'startup_delay': 1.0
                },
                'Linux': {
                    'audio_buffer_size': 2048,
                    'retry_delay': 0.5,
                    'max_retries': 3,
                    'startup_delay': 0.5
                }
            },
            'models': {
                'vosk': {
                    'path': 'vosk-model-small-en-us-0.15',
                    'url': 'https://example.com/vosk-model.zip'
                },
                'wake_word': {
                    'path': 'Hey-Omni_en_mac_v3_0_0/Hey-Omni_en_mac_v3_0_0.ppn',
                    'url': 'https://example.com/wake-word-model.zip'
                }
            },
            'required_env_vars': {
                'PORCUPINE_API_KEY': 'API key for wake word detection'
            }
        }
        
    @property
    def platform_config(self) -> PlatformConfig:
        """Get platform-specific configuration."""
        config = self._config['platform_config'].get(self._platform, {})
        return PlatformConfig(**config)
        
    @property
    def models(self) -> Dict[str, Dict[str, str]]:
        """Get model configurations."""
        return self._config['models']
        
    @property
    def required_env_vars(self) -> Dict[str, str]:
        """Get required environment variables."""
        return self._config['required_env_vars']