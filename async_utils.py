"""Async utilities for handling event loop issues in Streamlit."""

import asyncio
import threading
import concurrent.futures
from typing import Any, Awaitable, TypeVar
import functools

T = TypeVar('T')

class AsyncExecutor:
    """Thread-safe async executor for Streamlit applications."""
    
    def __init__(self):
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._loop = None
        self._thread = None
        self._setup_event_loop()
    
    def _setup_event_loop(self):
        """Set up a dedicated event loop in a separate thread."""
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        
        # Wait for the loop to be ready
        while self._loop is None:
            threading.Event().wait(0.01)
    
    def run_async(self, coro: Awaitable[T]) -> T:
        """Run an async coroutine in the dedicated event loop."""
        if self._loop is None or self._loop.is_closed():
            self._setup_event_loop()
        
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=60)  # 60 second timeout
    
    def shutdown(self):
        """Shutdown the executor and event loop."""
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._executor:
            self._executor.shutdown(wait=True)

# Global executor instance
_executor = None

def get_executor() -> AsyncExecutor:
    """Get the global async executor instance."""
    global _executor
    if _executor is None:
        _executor = AsyncExecutor()
    return _executor

def run_async_safe(coro: Awaitable[T]) -> T:
    """Safely run an async coroutine, handling event loop conflicts."""
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're already in an event loop, use the executor
        return get_executor().run_async(coro)
    except RuntimeError:
        # No event loop running, we can use asyncio.run
        return asyncio.run(coro)

def async_to_sync(func):
    """Decorator to convert async functions to sync for Streamlit."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        return run_async_safe(coro)
    return wrapper