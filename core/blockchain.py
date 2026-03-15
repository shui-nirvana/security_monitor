import logging
import time
from typing import Any

from security_monitor.config.settings import get_settings
from web3 import Web3

# Configure Logging
settings = get_settings()
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BlockchainClient:
    """
    Core Blockchain Interaction Layer
    Handles connection, retries, and error logging.
    """
    def __init__(self, chain_key: str | None = None):
        self.settings = get_settings()
        self.chain_key = (chain_key or self.settings.DEFAULT_CHAIN_KEY).lower()
        self.rpc_url = self.settings.get_rpc_url(self.chain_key)
        self.expected_chain_id = self.settings.get_chain_id(self.chain_key)
        self.w3 = self._connect()

    def _connect(self) -> Web3:
        """Establishes connection to RPC node with retries"""
        retries = 3
        for attempt in range(retries):
            try:
                w3 = Web3(Web3.HTTPProvider(self.rpc_url))
                if w3.is_connected():
                    logger.info(
                        f"Connected to RPC: {self.rpc_url} (Detected Chain ID: {w3.eth.chain_id}, Expected: {self.expected_chain_id}, Key: {self.chain_key})"
                    )
                    # Inject middleware for PoA chains if needed (e.g. BSC, Polygon)
                    # For Web3.py v6+, geth_poa_middleware is handled differently or not needed for basic reads
                    # w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    return w3
            except Exception as e:
                logger.warning(f"Connection attempt {attempt+1}/{retries} failed: {str(e)}")
                time.sleep(2)

        logger.critical("Failed to connect to Blockchain RPC after multiple attempts.")
        raise ConnectionError("Could not connect to RPC Node")

    def get_contract(self, address: str, abi: list) -> Any:
        """Returns a contract instance with checksum validation"""
        try:
            checksum_address = Web3.to_checksum_address(address)
            return self.w3.eth.contract(address=checksum_address, abi=abi)
        except Exception as e:
            logger.error(f"Failed to load contract at {address}: {str(e)}")
            raise

    def call_contract_function(self, contract_func, *args, **kwargs) -> Any:
        """
        Executes a contract read call with robust error handling.
        """
        try:
            return contract_func(*args, **kwargs).call()
        except Exception as e:
            logger.error(f"Contract call failed: {str(e)}")
            return None
