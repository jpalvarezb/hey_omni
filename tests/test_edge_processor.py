import pytest
from datetime import datetime
from omni.services.edge.processor import EdgeProcessor
from omni.services.edge.cache.memory_cache import MemoryCache
from omni.models.intent import Intent, IntentType

@pytest.mark.asyncio
class TestEdgeProcessor:
    """Test edge processor functionality."""
    
    @pytest.fixture
    async def processor(self):
        """Create edge processor for testing."""
        cache = MemoryCache(max_size=100)  # Removed max_memory
        return EdgeProcessor(cache=cache)