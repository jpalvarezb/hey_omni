"""Memory cache implementation."""
import logging
from typing import Any, Optional, Dict, Union
from datetime import datetime, timedelta
from collections import OrderedDict
from ....core.exceptions import CacheError

class MemoryCache:
    """In-memory cache implementation."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize memory cache.
        
        Args:
            max_size: Maximum number of items in cache
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        
    def _convert_ttl(self, ttl: Union[int, float, timedelta, None]) -> Optional[float]:
        """Convert TTL to seconds.
        
        Args:
            ttl: Time to live value
            
        Returns:
            float: TTL in seconds or None
            
        Raises:
            CacheError: If TTL is invalid
        """
        if ttl is None:
            return None
            
        try:
            if isinstance(ttl, timedelta):
                seconds = ttl.total_seconds()
            else:
                seconds = float(ttl)
                
            if seconds < 0:
                raise CacheError("TTL cannot be negative")
                
            return seconds
            
        except (TypeError, ValueError) as e:
            raise CacheError(f"Invalid TTL value: {e}")
            
    def _generate_key(self, *args: Any) -> str:
        """Generate cache key from arguments.
        
        Args:
            *args: Key components
            
        Returns:
            str: Generated key
            
        Raises:
            CacheError: If key generation fails
        """
        try:
            return ":".join(str(arg) for arg in args)
        except Exception as e:
            raise CacheError(f"Failed to generate key: {e}")
            
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired.
        
        Args:
            entry: Cache entry to check
            
        Returns:
            bool: True if expired
        """
        expires = entry.get('expires')
        return bool(expires and datetime.now() > expires)
        
    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]
        for key in expired_keys:
            self._cache.pop(key)
            
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Any: Cached value or None if not found
            
        Raises:
            CacheError: If get operation fails
        """
        try:
            if not isinstance(key, str):
                raise CacheError("Key must be a string")
                
            # Clean up expired entries periodically
            self._cleanup_expired()
            
            entry = self._cache.get(key)
            if not entry:
                return None
                
            if self._is_expired(entry):
                self._cache.pop(key)
                return None
                
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return entry['value']
            
        except Exception as e:
            self._logger.error(f"Failed to get from cache: {e}")
            raise CacheError(f"Failed to get from cache: {str(e)}")
            
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, float, timedelta]] = None
    ) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (seconds or timedelta)
            
        Raises:
            CacheError: If set operation fails
        """
        try:
            if not isinstance(key, str):
                raise CacheError("Key must be a string")
            if key.strip() == "":
                raise CacheError("Key cannot be empty")
            if value is None:
                raise CacheError("Value cannot be None")
                
            # Convert TTL to seconds
            ttl_seconds = self._convert_ttl(ttl)
            
            # Calculate expiry
            expires = None
            if ttl_seconds is not None:
                expires = datetime.now() + timedelta(seconds=ttl_seconds)
                
            # Ensure cache size
            if len(self._cache) >= self._max_size:
                self._logger.warning("Cache full, removing oldest entry")
                self._cache.popitem(last=False)  # Remove least recently used
                
            # Store entry
            self._cache[key] = {
                'value': value,
                'expires': expires,
                'created': datetime.now()
            }
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
        except Exception as e:
            self._logger.error(f"Failed to set cache value: {e}")
            raise CacheError(f"Failed to set cache value: {str(e)}")
            
    async def delete(self, key: str) -> None:
        """Delete value from cache.
        
        Args:
            key: Cache key to delete
            
        Raises:
            CacheError: If delete operation fails
        """
        try:
            if not isinstance(key, str):
                raise CacheError("Key must be a string")
            self._cache.pop(key, None)
        except Exception as e:
            self._logger.error(f"Failed to delete from cache: {e}")
            raise CacheError(f"Failed to delete from cache: {str(e)}")
            
    def clear(self) -> None:
        """Clear all entries from cache."""
        self._cache.clear()
