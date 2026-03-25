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
    DEFAULT_CHAIN_KEY: str = "ethereum"
    CHAIN_RPC_URLS: dict = {
        "ethereum": "https://eth-mainnet.public.blastapi.io",
        "sepolia": "https://ethereum-sepolia-rpc.publicnode.com",
        "arbitrum": "https://arb1.arbitrum.io/rpc",
        "optimism": "https://mainnet.optimism.io",
        "base": "https://mainnet.base.org",
        "polygon": "https://polygon-rpc.com",
        "avalanche": "https://api.avax.network/ext/bc/C/rpc",
    }
    CHAIN_ID_MAP: dict = {
        "ethereum": 1,
        "sepolia": 11155111,
        "arbitrum": 42161,
        "optimism": 10,
        "base": 8453,
        "polygon": 137,
        "avalanche": 43114,
    }

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
    GUARDIAN_BLOCKLIST: str = "0x000000000000000000000000000000000000dead,0x6666666666666666666666666666666666666666"
    GUARDIAN_ALLOWED_COUNTERPARTIES: str = ""
    GUARDIAN_REQUIRE_AI_APPROVAL: bool = True
    GUARDIAN_DAILY_TOTAL_LIMIT: float = 5000.0
    GUARDIAN_DAILY_ASSET_LIMITS: str = "USDT:3000,USAT:3000,XAUT:5"
    WDK_USE_TETHER_WDK: bool = True
    WDK_SEED_PHRASE: str = ""
    WDK_ACCOUNT_INDEX: int = 0
    WDK_NODE_CMD: str = "node"
    WDK_BRIDGE_SCRIPT: str = ""
    WDK_WAIT_FOR_RECEIPT: bool = True
    WDK_TX_TIMEOUT_SECONDS: int = 120

    # Asset Contracts (Sepolia Testnet Defaults - REPLACE with actual addresses)
    ASSET_CONTRACTS: dict = {
        "USDT": "0x7169D38820dfd117C3FA1f22a697dBA58d90BA06", # Mock USDT
        "XAUT": "0xA43914a51A76C09D94551F33C40294C649852222", # Placeholder XAUT Address for WDK Demo
        "USAT": "0x4D224452801ACEd8B2F0aebE155379bb5D594381"  # Placeholder USAT Address for WDK Demo
    }

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

    def get_rpc_url(self, chain_key: Optional[str] = None) -> str:
        key = (chain_key or self.DEFAULT_CHAIN_KEY).lower()
        return str(self.CHAIN_RPC_URLS.get(key, self.RPC_URL))

    def get_chain_id(self, chain_key: Optional[str] = None) -> int:
        key = (chain_key or self.DEFAULT_CHAIN_KEY).lower()
        return int(self.CHAIN_ID_MAP.get(key, self.CHAIN_ID))

    def get_guardian_blocklist(self) -> set[str]:
        return {
            address.strip().lower()
            for address in self.GUARDIAN_BLOCKLIST.split(",")
            if address.strip()
        }

    def get_guardian_allowed_counterparties(self) -> set[str]:
        return {
            address.strip().lower()
            for address in self.GUARDIAN_ALLOWED_COUNTERPARTIES.split(",")
            if address.strip()
        }

    def get_guardian_daily_asset_limits(self) -> dict[str, float]:
        limits: dict[str, float] = {}
        for raw_item in self.GUARDIAN_DAILY_ASSET_LIMITS.split(","):
            item = raw_item.strip()
            if not item or ":" not in item:
                continue
            symbol, limit = item.split(":", 1)
            symbol_normalized = symbol.strip().upper()
            if not symbol_normalized:
                continue
            try:
                limits[symbol_normalized] = float(limit.strip())
            except ValueError:
                continue
        return limits

@lru_cache()
def get_settings() -> Settings:
    return Settings()
