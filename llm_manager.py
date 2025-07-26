"""LLM Manager to handle session-based LLM instances and avoid event loop conflicts."""

import asyncio
import threading
from typing import Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from config import Config
import uuid

class LLMManager:
    """Manages LLM instances per session to avoid event loop conflicts."""
    
    def __init__(self):
        self._instances: Dict[str, ChatGoogleGenerativeAI] = {}
        self._lock = threading.Lock()
    
    def get_llm_for_session(self, session_id: Optional[str] = None) -> ChatGoogleGenerativeAI:
        """Get or create an LLM instance for a specific session."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        with self._lock:
            if session_id not in self._instances:
                self._instances[session_id] = self._create_llm()
            return self._instances[session_id]
    
    def _create_llm(self) -> ChatGoogleGenerativeAI:
        """Create a new LLM instance with proper configuration."""
        return ChatGoogleGenerativeAI(
            model=Config.GEMINI_MODEL,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS,
            google_api_key=Config.GOOGLE_API_KEY
        )
    
    def cleanup_session(self, session_id: str):
        """Clean up LLM instance for a session."""
        with self._lock:
            if session_id in self._instances:
                del self._instances[session_id]
    
    def cleanup_all(self):
        """Clean up all LLM instances."""
        with self._lock:
            self._instances.clear()

# Global LLM manager instance
_llm_manager = None

def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance."""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager

async def safe_llm_invoke(llm: ChatGoogleGenerativeAI, messages, session_id: Optional[str] = None):
    """Safely invoke LLM with proper error handling and cleanup."""
    import gc
    
    try:
        # Use a timeout to prevent hanging
        response = await asyncio.wait_for(llm.ainvoke(messages), timeout=30.0)
        return response
    except asyncio.TimeoutError:
        raise Exception("LLM call timed out after 30 seconds")
    except Exception as e:
        # Log the error and re-raise
        import logging
        logging.error(f"LLM call failed: {e}")
        raise
    finally:
        # Force garbage collection
        gc.collect()