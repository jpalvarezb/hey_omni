import asyncio
import logging
import os
import platform
import sys
import argparse
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from omni.core.config import Config
from omni.core.exceptions import ConfigurationError
from omni.services.edge.processor import EdgeProcessor

class OmniApp:
    """Main application orchestrator."""
    
    def __init__(self, args: Optional[argparse.Namespace] = None):
        self._processor: Optional[EdgeProcessor] = None
        self._running = False
        self._logger = logging.getLogger(self.__class__.__name__)
        self._platform = platform.system()
        self._args = args or self._parse_args()
        self._config = Config()
        
    @staticmethod
    def _parse_args() -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(description='OmniClip Application')
        parser.add_argument('--offline', action='store_true', help='Run in offline mode')
        parser.add_argument('--skip-audio-validation', action='store_true', 
                          help='Skip audio device validation')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')
        return parser.parse_args()
    
    @asynccontextmanager
    async def _processor_context(self):
        """Context manager for processor lifecycle."""
        try:
            self._processor = EdgeProcessor(
                offline_mode=self._args.offline,
                **self._config.platform_config.__dict__
            )
            await self._processor.start()
            yield self._processor
        finally:
            if self._processor:
                await self._processor.stop()
                
    async def _download_model(self, model_type: str, retries: int = 3) -> None:
        """Download model files with retry."""
        model_config = self._config.models[model_type]
        url = model_config['url']
        path = Path(__file__).parent / "models" / model_config['path']
        
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            async with aiofiles.open(path, 'wb') as f:
                                await f.write(await response.read())
                            self._logger.info(f"Downloaded {model_type} model successfully")
                            return
                        else:
                            raise Exception(f"Download failed with status {response.status}")
            except Exception as e:
                if attempt < retries - 1:
                    delay = self._config.platform_config.retry_delay * (attempt + 1)
                    self._logger.warning(
                        f"Download attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    raise ConfigurationError(f"Failed to download {model_type} model: {str(e)}")
                    
    async def start(self) -> None:
        """Initialize and start all components with enhanced validation."""
        try:
            # Load configuration
            await self._config.load()
            
            # Configure logging
            if self._args.debug:
                logging.getLogger().setLevel(logging.DEBUG)
                
            async with self._processor_context() as processor:
                self._running = True
                self._logger.info(
                    f"OmniApp started successfully on {self._platform} "
                    f"({'offline' if self._args.offline else 'online'} mode)"
                )
                
                while self._running:
                    try:
                        await asyncio.sleep(1)
                    except asyncio.CancelledError:
                        break
                        
        except Exception as e:
            self._logger.error(f"Failed to start OmniApp: {str(e)}")
            raise
            
    async def stop(self) -> None:
        """Stop all components."""
        self._running = False
        self._logger.info(f"OmniApp stopped on {self._platform}")

def main():
    """Enhanced main entry point with argument parsing."""
    # Configure base logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app = OmniApp()
    
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        sys.exit(1)
    finally:
        asyncio.run(app.stop())

if __name__ == "__main__":
    main() 