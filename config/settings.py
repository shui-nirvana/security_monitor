from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """
    Application Configuration
    Loads from environment variables or .env file
    """
    # Blockchain
    RPC_URL: str = "https://eth-mainnet.public.blastapi.io"
    CHAIN_ID: int = 1
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "security_monitor.log"

    # Monitoring Targets (Demo Defaults)
    # USDC Contract on Mainnet
    TARGET_TOKEN_ADDRESS: str = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48" 
    
    # LLM Integration (DeepSeek / Gemini / OpenAI)
    ENABLE_AI_ANALYSIS: bool = False
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"  # Default to DeepSeek
    LLM_MODEL: str = "deepseek-chat"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings() -> Settings:
    return Settings()
