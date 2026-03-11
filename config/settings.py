from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


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
    # Enable by default for Hackathon Demo (will fall back to Simulation Mode if no API Key)
    ENABLE_AI_ANALYSIS: bool = True
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"  # Default to DeepSeek
    LLM_MODEL: str = "deepseek-chat"
    GUARDIAN_MAX_TRANSFER_AMOUNT: float = 1000.0
    GUARDIAN_SUPPORTED_ASSETS: str = "USDT,USAT,XAUT"

    # Asset Contracts (Sepolia Testnet Defaults - REPLACE with actual addresses)
    ASSET_CONTRACTS: dict = {
        "USDT": "0x7169D38820dfd117C3FA1f22a697dBA58d90BA06", # Mock USDT
        "XAUT": "0xA43914a51A76C09D94551F33C40294C649852222", # Placeholder XAUT Address for WDK Demo
        "USAT": "0x4D224452801ACEd8B2F0aebE155379bb5D594381"  # Placeholder USAT Address for WDK Demo
    }

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings() -> Settings:
    return Settings()
