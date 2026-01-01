"""
Redis locking utilities for distributed operations.
"""
import redis.asyncio as redis
from typing import Optional
import asyncio
from contextlib import asynccontextmanager

class LockManager:
    """Manages Redis-based distributed locks."""

    def __init__(self, redis_client: redis.Redis, lock_timeout: int = 300):
        self.redis = redis_client
        self.lock_timeout = lock_timeout

    async def acquire_lock(self, lock_key: str) -> Optional[redis.lock.Lock]:
        """Acquire a Redis lock."""
        lock = self.redis.lock(lock_key, timeout=self.lock_timeout)
        acquired = await lock.acquire(blocking=False)
        return lock if acquired else None

    async def release_lock(self, lock: redis.lock.Lock):
        """Release a Redis lock."""
        try:
            await lock.release()
        except Exception:
            # Lock may have expired or been released already
            pass

    @asynccontextmanager
    async def with_lock(self, lock_key: str):
        """
        Context manager for Redis locking.
        Usage: async with lock_manager.with_lock(key): ...
        """
        lock = await self.acquire_lock(lock_key)
        if not lock:
            raise RuntimeError(f"Could not acquire lock for {lock_key}")

        try:
            yield
        finally:
            await self.release_lock(lock)