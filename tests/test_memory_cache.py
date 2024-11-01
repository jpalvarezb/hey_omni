"""Tests for memory cache."""
import pytest
from datetime import timedelta
from omni.services.edge.cache.memory_cache import MemoryCache
from omni.core.exceptions import CacheError

@pytest.mark.asyncio
class TestMemoryCache:
    """Test memory cache functionality."""
    
    @pytest.fixture
    async def cache(self):
        """Create memory cache for testing."""
        return MemoryCache(max_size=100)  # Removed max_memory
        
    async def test_basic_operations(self, cache):
        """Test basic cache operations."""
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"