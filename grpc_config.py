"""gRPC configuration and utilities to handle async issues."""

import os
import warnings
import logging
import asyncio
from contextlib import asynccontextmanager

# Suppress gRPC warnings and errors
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = ''

# Configure logging to suppress gRPC warnings
logging.getLogger('grpc').setLevel(logging.ERROR)

# Suppress specific warnings
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*coroutine.*was never awaited.*')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*Enable tracemalloc.*')

def configure_grpc():
    """Configure gRPC settings for better compatibility."""
    try:
        import grpc
        
        # Set gRPC options for better async handling
        grpc_options = [
            ('grpc.keepalive_time_ms', 30000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', True),
            ('grpc.http2.max_pings_without_data', 0),
            ('grpc.http2.min_time_between_pings_ms', 10000),
            ('grpc.http2.min_ping_interval_without_data_ms', 300000)
        ]
        
        return grpc_options
    except ImportError:
        return []

@asynccontextmanager
async def safe_llm_call():
    """Context manager for safe LLM calls that handles gRPC cleanup."""
    import gc
    import asyncio
    
    # Get the current event loop
    current_loop = None
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        pass
    
    try:
        yield
    except Exception as e:
        # Log the error but don't re-raise to prevent cascading failures
        logging.error(f"LLM call error: {e}")
        raise
    finally:
        # Clean up any pending tasks in the current loop
        if current_loop:
            try:
                # Cancel any pending tasks that might be lingering
                pending_tasks = [task for task in asyncio.all_tasks(current_loop) 
                               if not task.done() and 'grpc' in str(task).lower()]
                for task in pending_tasks:
                    if not task.cancelled():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                        except Exception:
                            pass
            except Exception:
                pass
        
        # Force garbage collection to clean up any lingering gRPC objects
        gc.collect()

def create_isolated_llm():
    """Create an LLM instance with isolated gRPC configuration."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from config import Config
    
    return ChatGoogleGenerativeAI(
        model=Config.GEMINI_MODEL,
        temperature=Config.TEMPERATURE,
        max_tokens=Config.MAX_TOKENS,
        google_api_key=Config.GOOGLE_API_KEY,
        convert_system_message_to_human=True,
        # Add gRPC-specific configurations
        transport='grpc',
        client_options={
            'api_endpoint': 'generativelanguage.googleapis.com'
        }
    )

# Apply configuration on import
configure_grpc()