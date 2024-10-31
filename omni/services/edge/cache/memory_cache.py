import asyncio
import time
import sys
import logging
from typing import Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
from ....core.exceptions import ResourceInitializationError

@dataclass
class CacheEntry:
    """Represents a cached item with metadata."""
    value: Any
    timestamp: float
    ttl: Optional[int]
    size: int
    access_count: int = 0
    last_access: float = time.time()
    is_large: bool = False
    is_critical: bool = False
    error_count: int = 0

class MemoryCache:
    """Thread-safe async memory cache with adaptive management."""
    
    # Size thresholds
    LARGE_ENTRY_THRESHOLD = 0.1  # 10% of max cache size
    CRITICAL_SIZE_THRESHOLD = 0.8  # 80% of max cache size
    
    # Cleanup thresholds
    MIN_CLEANUP_INTERVAL = 60   # 1 minute
    MAX_CLEANUP_INTERVAL = 3600 # 1 hour
    
    def __init__(self, max_size: int = 1000, cleanup_interval: int = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval
        self._adaptive_cleanup_interval = cleanup_interval
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        self._current_size = 0
        self._logger = logging.getLogger(self.__class__.__name__)
        self._large_entries: Set[str] = set()
        self._critical_entries: Set[str] = set()
        self._access_patterns: Dict[str, list] = defaultdict(list)
        self._last_cleanup_time = time.time()
        self._eviction_count = 0
        
    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate memory size of cached value."""
        try:
            # Get base size
            size = sys.getsizeof(value)
            
            # Handle common container types
            if isinstance(value, (dict, list, set)):
                size += sum(sys.getsizeof(k) + sys.getsizeof(v) 
                          for k, v in value.items()) if isinstance(value, dict) \
                          else sum(sys.getsizeof(item) for item in value)
            return size
        except Exception as e:
            self._logger.warning(f"Error calculating size: {e}, using fallback")
            return sys.getsizeof(str(value))
            
    def _is_large_entry(self, size: int) -> bool:
        """Check if entry size is considered large."""
        return size > (self._max_size * self.LARGE_ENTRY_THRESHOLD)
        
    async def _adjust_cleanup_interval(self) -> None:
        """Dynamically adjust cleanup interval based on cache pressure."""
        current_time = time.time()
        time_since_cleanup = current_time - self._last_cleanup_time
        
        # Calculate cache pressure (0 to 1)
        size_pressure = self._current_size / self._max_size
        eviction_rate = self._eviction_count / max(1, time_since_cleanup)
        
        # Adjust interval based on pressure
        if size_pressure > self.CRITICAL_SIZE_THRESHOLD or eviction_rate > 0.5:
            # Decrease interval (more frequent cleanup)
            self._adaptive_cleanup_interval = max(
                self.MIN_CLEANUP_INTERVAL,
                self._adaptive_cleanup_interval // 2
            )
            self._logger.info(f"Decreased cleanup interval to {self._adaptive_cleanup_interval}s")
        elif size_pressure < 0.5 and eviction_rate < 0.1:
            # Increase interval (less frequent cleanup)
            self._adaptive_cleanup_interval = min(
                self.MAX_CLEANUP_INTERVAL,
                self._adaptive_cleanup_interval * 2
            )
            
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup with adaptive interval."""
        while self._running:
            try:
                needs_cleanup = await self._needs_cleanup()
                if needs_cleanup:
                    await self._cleanup_expired()
                    await self._adjust_cleanup_interval()
                    self._last_cleanup_time = time.time()
                    self._eviction_count = 0
                await asyncio.sleep(self._adaptive_cleanup_interval)
            except Exception as e:
                self._logger.error(f"Error in cleanup loop: {str(e)}")
                
    async def _cleanup_expired(self) -> None:
        """Remove expired entries with priority-based eviction."""
        async with self._lock:
            current_time = time.time()
            removed_entries = []
            
            # First, remove expired entries
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.ttl and current_time > entry.timestamp + entry.ttl
            ]
            for key in expired_keys:
                entry = self._cache[key]
                self._current_size -= entry.size
                del self._cache[key]
                removed_entries.append(key)
                self._eviction_count += 1
                
            # If still over size limit, remove large non-critical entries first
            if self._current_size > self._max_size:
                for key in self._large_entries - self._critical_entries:
                    if self._current_size <= self._max_size:
                        break
                    if key in self._cache:
                        entry = self._cache[key]
                        self._current_size -= entry.size
                        del self._cache[key]
                        removed_entries.append(key)
                        self._eviction_count += 1
                        
            # If still needed, use weighted score for remaining entries
            while self._current_size > self._max_size:
                scores = {
                    key: self._calculate_entry_score(entry, current_time)
                    for key, entry in self._cache.items()
                    if not entry.is_critical
                }
                if not scores:
                    break
                    
                key_to_remove = min(scores.items(), key=lambda x: x[1])[0]
                entry = self._cache[key_to_remove]
                self._current_size -= entry.size
                del self._cache[key_to_remove]
                removed_entries.append(key_to_remove)
                self._eviction_count += 1
                
            if removed_entries:
                self._logger.info(f"Removed {len(removed_entries)} entries during cleanup")
                
    async def set(self, 
                  key: str, 
                  value: Any, 
                  ttl: Optional[int] = None,
                  is_critical: bool = False) -> None:
        """Store item in cache with optional TTL and criticality flag."""
        async with self._lock:
            size = self._calculate_size(value)
            
            # Handle large entries
            is_large = self._is_large_entry(size)
            if is_large and not is_critical:
                if size > self._max_size:
                    raise ValueError(f"Item size {size} exceeds maximum cache size {self._max_size}")
                self._logger.warning(f"Large entry detected for key {key} (size: {size})")
                
            # Remove old entry if it exists
            if key in self._cache:
                old_entry = self._cache[key]
                self._current_size -= old_entry.size
                
            # Ensure space for new entry
            while self._current_size + size > self._max_size:
                await self._cleanup_expired()
                if not self._cache:
                    if size > self._max_size:
                        raise ValueError(f"Item size {size} exceeds maximum cache size {self._max_size}")
                    break
                    
            # Add new entry
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl,
                size=size,
                is_large=is_large,
                is_critical=is_critical
            )
            self._cache[key] = entry
            self._current_size += size
            
            # Update entry sets
            if is_large:
                self._large_entries.add(key)
            if is_critical:
                self._critical_entries.add(key)
                
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve item from cache if not expired."""
        async with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
                
            current_time = time.time()
            if entry.ttl and current_time > entry.timestamp + entry.ttl:
                self._current_size -= entry.size
                del self._cache[key]
                return None
                
            # Update access metadata
            entry.access_count += 1
            entry.last_access = current_time
            return entry.value
            
    async def delete(self, key: str) -> None:
        """Remove item from cache."""
        async with self._lock:
            self._cache.pop(key, None)
            
    async def clear(self) -> None:
        """Clear all items from cache."""
        async with self._lock:
            self._cache.clear()
            
    async def get_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics."""
        async with self._lock:
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            return {
                'size': self._current_size,
                'max_size': self._max_size,
                'item_count': len(self._cache),
                'cleanup_interval': self._adaptive_cleanup_interval,
                'total_accesses': total_accesses,
                'average_item_size': self._current_size / len(self._cache) if self._cache else 0,
                'large_entries': len(self._large_entries),
                'critical_entries': len(self._critical_entries),
                'eviction_count': self._eviction_count
            }

    async def start(self) -> None:
        """Start the cache and cleanup task."""
        if self._running:
            return
            
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._logger.debug("Cache started")
        
    async def stop(self) -> None:
        """Stop the cache and cleanup task."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        self._logger.debug("Cache stopped")

    async def _needs_cleanup(self) -> bool:
        """Check if cleanup is needed."""
        async with self._lock:
            current_time = time.time()
            
            # Check for expired entries
            has_expired = any(
                entry.ttl and current_time > entry.timestamp + entry.ttl
                for entry in self._cache.values()
            )
            
            # Check size threshold
            size_pressure = self._current_size / self._max_size
            
            return has_expired or size_pressure > self.CRITICAL_SIZE_THRESHOLD
