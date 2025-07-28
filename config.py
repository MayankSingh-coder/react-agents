"""Configuration settings for the React Agent."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the React Agent."""
    
    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY","")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Model Configuration
    GEMINI_MODEL = "gemini-2.0-flash-lite"
    TEMPERATURE = 0.1
    MAX_TOKENS = 1000
    
    # Agent Configuration
    MAX_ITERATIONS = 10
    VERBOSE = True
    
    # Cache Configuration
    CACHE_TTL = 3600  # 1 hour in seconds
    MAX_CACHE_SIZE = 1000
    
    # Validate required keys
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required. Please set it in your .env file.")
        
        return True

# Validate configuration on import
Config.validate()