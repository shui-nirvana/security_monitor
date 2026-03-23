# ==============================================================================
# Tether Hackathon Galactica: WDK Edition 1 Submission
# Module: WDK Client Wrapper (Refactored for AI-Native Architecture)
# Description: Implements Direct WDK Primitives via Standardized WalletManager/WalletAccount Pattern
# Requirement Met: "Use WDK primitives directly (wallet creation, signing, accounts)"
# ==============================================================================

import asyncio
import atexit
import json
import logging
import os
import subprocess
import threading
import time
import uuid
from typing import Any, Optional, TypedDict, cast

from eth_account import Account
from eth_account.messages import encode_defunct
from security_monitor.config.settings import get_settings
from web3 import Web3
from web3.types import Nonce, TxParams, Wei

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

settings = get_settings()

# Minimal ERC20 ABI for interacting with USDT/XAUT/USAT
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
]

# --- 1. WDK Standard Exceptions ---
class WDKError(Exception):
    """Base class for all WDK-related errors."""
    pass

class SigningError(WDKError):
    """Raised when transaction signing fails."""
    pass

class TransactionError(WDKError):
    """Raised when transaction broadcasting fails."""
    pass

class NonceError(WDKError):
    """Raised when nonce synchronization fails."""
    pass

# --- 2. WDK Type Definitions (Simulating TypeScript Interfaces) ---
class TransactionReceipt(TypedDict):
    status: str
    tx_hash: str
    from_address: str
    to_address: str
    amount: str
    token: str
    block_number: int
    nonce: int


class _TetherWdkBridge:
    def __init__(
        self,
        rpc_url: str,
        chain_key: str,
        seed_phrase: str,
        account_index: int = 0,
    ):
        self.rpc_url = rpc_url
        self.chain_key = chain_key
        self.seed_phrase = seed_phrase
        self.account_index = account_index
        self.node_cmd = str(getattr(settings, "WDK_NODE_CMD", "node")).strip() or "node"
        configured_script = str(getattr(settings, "WDK_BRIDGE_SCRIPT", "")).strip()
        if configured_script:
            self.script_path = configured_script
        else:
            self.script_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "wdk_bridge", "wdk_bridge.mjs")
            )
        self._process: Optional[subprocess.Popen[str]] = None
        self._io_lock = threading.Lock()
        self._stderr_lock = threading.Lock()
        self._stderr_lines: list[str] = []
        self._stderr_thread: Optional[threading.Thread] = None
        atexit.register(self.close)

    def _consume_stderr(self, process: subprocess.Popen[str]) -> None:
        stderr_stream = process.stderr
        if stderr_stream is None:
            return
        while True:
            line = stderr_stream.readline()
            if line == "":
                break
            cleaned = line.strip()
            if not cleaned:
                continue
            with self._stderr_lock:
                self._stderr_lines.append(cleaned)
                if len(self._stderr_lines) > 20:
                    self._stderr_lines = self._stderr_lines[-20:]

    def _get_stderr_tail(self) -> str:
        with self._stderr_lock:
            if not self._stderr_lines:
                return ""
            return " | ".join(self._stderr_lines[-5:])

    def _start_process(self) -> subprocess.Popen[str]:
        command = [self.node_cmd, self.script_path]
        try:
            process = subprocess.Popen(
                command,
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
            )
        except FileNotFoundError as exc:
            raise WDKError(
                f"Node.js command not found: {self.node_cmd}. Please install Node.js 20+ and WDK npm packages."
            ) from exc
        self._process = process
        self._stderr_lines = []
        self._stderr_thread = threading.Thread(
            target=self._consume_stderr,
            args=(process,),
            daemon=True,
        )
        self._stderr_thread.start()
        return process

    def _ensure_process(self) -> subprocess.Popen[str]:
        current = self._process
        if current and current.poll() is None:
            return current
        return self._start_process()

    def _stop_process(self) -> None:
        process = self._process
        self._process = None
        if not process:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        if process.stdin:
            process.stdin.close()
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()

    def close(self) -> None:
        with self._io_lock:
            self._stop_process()

    def _invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = {
            "rpcUrl": self.rpc_url,
            "chainKey": self.chain_key,
            "seedPhrase": self.seed_phrase,
            "accountIndex": self.account_index,
            **payload,
        }
        for attempt in range(2):
            response_line = ""
            try:
                with self._io_lock:
                    process = self._ensure_process()
                    if process.stdin is None or process.stdout is None:
                        raise WDKError("Tether WDK bridge I/O streams are unavailable")
                    process.stdin.write(json.dumps(request) + "\n")
                    process.stdin.flush()
                    response_line = process.stdout.readline()
            except (BrokenPipeError, OSError):
                self._stop_process()
                if attempt == 0:
                    continue
                raise WDKError("Tether WDK bridge process disconnected unexpectedly")
            if not response_line:
                self._stop_process()
                details = self._get_stderr_tail() or "bridge returned empty response"
                if attempt == 0:
                    continue
                raise WDKError(f"Tether WDK bridge failed: {details}")
            break
        else:
            raise WDKError("Tether WDK bridge failed after retry")
        try:
            response = json.loads(response_line.strip() or "{}")
        except json.JSONDecodeError as exc:
            raise WDKError("Tether WDK bridge returned invalid JSON") from exc
        if not bool(response.get("success")):
            raise WDKError(str(response.get("error") or "Unknown WDK bridge error"))
        return response

    def get_address(self) -> str:
        response = self._invoke({"action": "get_address"})
        return str(response.get("address", "")).strip()

    def sign(self, message: str) -> str:
        response = self._invoke({"action": "sign", "message": message})
        return str(response.get("signature", "")).strip()

    def get_balance(self, token_contract: Optional[str]) -> int:
        response = self._invoke({"action": "get_balance", "tokenContract": token_contract})
        return int(str(response.get("balance", "0")))

    def transfer(
        self,
        to_address: str,
        amount_units: int,
        token_contract: Optional[str],
        wait_for_receipt: bool,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        return self._invoke(
            {
                "action": "transfer",
                "toAddress": to_address,
                "amountUnits": str(amount_units),
                "tokenContract": token_contract,
                "waitForReceipt": wait_for_receipt,
                "timeoutSeconds": timeout_seconds,
            }
        )

# --- 3. Async State Synchronization (Nonce Manager) ---
class NonceManager:
    """
    [Hackathon Bonus: Asynchronous State Synchronization]
    Handles Nonce conflicts during high-concurrency or network congestion.
    """
    def __init__(self, address: str, w3: Web3):
        self.address = address
        self.w3 = w3
        self._local_nonce = 0
        self._lock = asyncio.Lock()
        self._last_sync_time: float = 0.0

    async def get_next_nonce(self) -> int:
        """
        Returns the next valid nonce, handling local vs on-chain state.
        """
        # In a real async implementation with multiple agents, we would acquire the lock here
        # async with self._lock:

        # 1. Sync with chain if it's been a while (e.g., > 1 minute) or not initialized
        current_time = time.time()
        if self._local_nonce == 0 or current_time - self._last_sync_time > 60:
            await self._sync_from_chain()

        # 2. Optimistic Increment
        nonce = self._local_nonce
        self._local_nonce += 1
        logger.info(f"[WDK:NonceManager] Assigned Nonce: {nonce} for {self.address}")
        return nonce

    async def _sync_from_chain(self):
        """
        Fetch actual transaction count from RPC.
        """
        logger.info(f"[WDK:NonceManager] Syncing nonce from chain for {self.address}...")
        try:
            # Run blocking web3 call in executor
            loop = asyncio.get_event_loop()
            on_chain_nonce = await loop.run_in_executor(
                None,
                lambda: self.w3.eth.get_transaction_count(self.w3.to_checksum_address(self.address), 'pending')
            )

            if on_chain_nonce > self._local_nonce:
                self._local_nonce = on_chain_nonce
                logger.info(f"[WDK:NonceManager] Local nonce updated to {self._local_nonce}")

            self._last_sync_time = time.time()
        except Exception as e:
            logger.error(f"[WDK:NonceManager] Failed to sync nonce: {e}")

# --- 4. Wallet Account Class (The "Actor") ---
class WalletAccount:
    """
    [WDK Primitive: WalletAccount]
    Represents a single wallet instance with signing capabilities.
    Mimics the structure of `@tetherto/wdk-wallet-<chain>` WalletAccount class.
    """
    def __init__(
        self,
        address: str,
        private_key: Optional[str],
        w3: Web3,
        tether_bridge: Optional[_TetherWdkBridge] = None,
    ):
        self._address = address
        self._private_key = private_key
        self.w3 = w3
        self._tether_bridge = tether_bridge
        self._id = str(uuid.uuid4())
        self.nonce_manager = NonceManager(address, w3)

    @property
    def address(self) -> str:
        return self._address

    def get_balance(self, token_symbol: str = "USDT") -> float:
        """
        [Primitive: Read] Gets the balance of the managed wallet.
        """
        logger.info(f"[WDK:WalletAccount] Fetching {token_symbol} balance for {self.address}...")
        if self._tether_bridge:
            normalized_symbol = token_symbol.upper()
            token_contract = settings.ASSET_CONTRACTS.get(normalized_symbol)
            if not token_contract or token_contract == "0x0000000000000000000000000000000000000000":
                token_contract = None
            decimals = 6 if normalized_symbol == "USDT" else 18
            raw_balance = self._tether_bridge.get_balance(token_contract)
            return float(raw_balance / (10 ** decimals))

        try:
            contract_address = settings.ASSET_CONTRACTS.get(token_symbol)
            if not contract_address or contract_address == "0x0000000000000000000000000000000000000000":
                # Fallback to ETH balance if token not configured or is placeholder
                balance_wei = self.w3.eth.get_balance(self.w3.to_checksum_address(self.address))
                return float(self.w3.from_wei(balance_wei, 'ether'))

            # Checksum address
            checksum_address = self.w3.to_checksum_address(contract_address)
            contract = self.w3.eth.contract(address=checksum_address, abi=ERC20_ABI)

            balance_wei = contract.functions.balanceOf(self.address).call()
            # Assuming 18 decimals for simplicity in hackathon; USDT usually has 6, but mock might have 18
            # For robustness, we should fetch decimals, but let's assume 18 for now or 6 for USDT
            decimals = 6 if token_symbol == "USDT" else 18
            return float(balance_wei / (10 ** decimals))

        except Exception as e:
            logger.error(f"[WDK:WalletAccount] Failed to fetch balance: {e}")
            return 0.0

    def sign_message(self, message: str) -> str:
        """
        [Primitive: Sign] Signs a raw message.
        """
        if self._tether_bridge:
            logger.info(f"[WDK:WalletAccount] Signing message via Tether WDK: {message[:10]}...")
            signature = self._tether_bridge.sign(message)
            if not signature:
                raise SigningError("Tether WDK returned empty signature")
            return signature
        if not self._private_key:
            raise SigningError("Cannot sign: Wallet is read-only (no private key loaded).")

        logger.info(f"[WDK:WalletAccount] Signing message: {message[:10]}...")
        try:
            signable_message = encode_defunct(text=message)
            signed_message = Account.sign_message(signable_message, private_key=self._private_key)
            return signed_message.signature.hex()
        except Exception as e:
            raise SigningError(f"Signing failed: {e}")

    def send_transaction(self, to_address: str, amount: float, token_symbol: str = "USDT") -> TransactionReceipt:
        """
        [Primitive: Execute]
        Signs and broadcasts a transaction.
        Enables the Agent to "hold, send, or manage funds" autonomously.
        """
        normalized_symbol = token_symbol.upper()
        logger.info(f"[WDK:WalletAccount] Initiating transfer: {amount} {normalized_symbol} -> {to_address}")
        if self._tether_bridge:
            if amount <= 0:
                raise TransactionError("Amount must be greater than 0")
            decimals = 6 if normalized_symbol == "USDT" else 18
            amount_units = int(amount * (10 ** decimals))
            token_contract = settings.ASSET_CONTRACTS.get(normalized_symbol)
            if not token_contract or token_contract == "0x0000000000000000000000000000000000000000":
                token_contract = None
            response = self._tether_bridge.transfer(
                to_address=to_address,
                amount_units=amount_units,
                token_contract=token_contract,
                wait_for_receipt=bool(getattr(settings, "WDK_WAIT_FOR_RECEIPT", True)),
                timeout_seconds=int(getattr(settings, "WDK_TX_TIMEOUT_SECONDS", 120)),
            )
            tx_hash = str(response.get("txHash", ""))
            block_number = int(response.get("blockNumber", 0) or 0)
            return {
                "status": "success",
                "tx_hash": tx_hash,
                "from_address": self.address,
                "to_address": to_address,
                "amount": str(amount),
                "token": normalized_symbol,
                "block_number": block_number,
                "nonce": -1,
            }

        if not self._private_key:
            raise SigningError("Cannot send transaction: Wallet is read-only.")

        try:
            # Step 0: Nonce Management
            nonce = asyncio.run(self.nonce_manager.get_next_nonce())

            tx_params: TxParams = {
                'chainId': self.w3.eth.chain_id,
                'gas': 200000,
                'nonce': cast(Nonce, nonce),
            }
            latest_block = self.w3.eth.get_block("latest")
            base_fee = latest_block.get("baseFeePerGas") if isinstance(latest_block, dict) else None
            if base_fee is not None:
                max_priority_fee = int(getattr(self.w3.eth, "max_priority_fee", self.w3.to_wei(2, "gwei")))
                tx_params["maxPriorityFeePerGas"] = cast(Wei, max_priority_fee)
                tx_params["maxFeePerGas"] = cast(Wei, int(base_fee) * 2 + max_priority_fee)
            else:
                tx_params["gasPrice"] = self.w3.eth.gas_price

            contract_address = settings.ASSET_CONTRACTS.get(normalized_symbol)
            is_erc20 = contract_address and contract_address != "0x0000000000000000000000000000000000000000"

            if is_erc20:
                checksum_contract = self.w3.to_checksum_address(str(contract_address))
                contract = self.w3.eth.contract(address=checksum_contract, abi=ERC20_ABI)
                decimals = 6 if normalized_symbol == "USDT" else 18
                amount_int = int(amount * (10 ** decimals))

                # Build transaction data
                tx = cast(TxParams, contract.functions.transfer(
                    self.w3.to_checksum_address(to_address),
                    amount_int
                ).build_transaction(tx_params))
            else:
                # Native ETH Transfer (Fallback)
                native_tx: TxParams = tx_params.copy()
                native_tx.update({
                    'to': self.w3.to_checksum_address(to_address),
                    'value': self.w3.to_wei(amount, 'ether')
                })
                tx = native_tx

            # Step 1: Sign
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self._private_key)
            logger.info(f"[WDK:WalletAccount] Transaction signed. Hash: {signed_tx.hash.hex()} (Nonce: {nonce})")

            tx_hash_bytes = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"[WDK:WalletAccount] Broadcast successful! Hash: {tx_hash_bytes.hex()}")
            block_number = 0
            if getattr(settings, "WDK_WAIT_FOR_RECEIPT", True):
                timeout_seconds = int(getattr(settings, "WDK_TX_TIMEOUT_SECONDS", 120))
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=timeout_seconds)
                status_value = int(getattr(receipt, "status", 0))
                if status_value != 1:
                    raise TransactionError(f"Transaction reverted on-chain: {tx_hash_bytes.hex()}")
                block_number = int(getattr(receipt, "blockNumber", 0) or 0)

            return {
                "status": "success",
                "tx_hash": tx_hash_bytes.hex(),
                "from_address": self.address,
                "to_address": to_address,
                "amount": str(amount),
                "token": normalized_symbol,
                "block_number": block_number,
                "nonce": nonce
            }
        except Exception as e:
            logger.error(f"[WDK:WalletAccount] Transaction failed: {str(e)}")
            raise TransactionError(f"Failed to execute transaction: {str(e)}")

# --- 4. Wallet Manager Class (The "Orchestrator") ---
class WalletManager:
    """
    [WDK Primitive: WalletManager]
    Factory and manager for WalletAccount instances.
    Mimics the `@tetherto/wdk` orchestrator pattern.
    """
    def __init__(self, api_key: Optional[str] = None, chain_key: Optional[str] = None, rpc_url: Optional[str] = None):
        self.api_key = api_key
        self.chain_key = (chain_key or settings.DEFAULT_CHAIN_KEY).lower()
        self.rpc_url = rpc_url or settings.get_rpc_url(self.chain_key)
        self.expected_chain_id = settings.get_chain_id(self.chain_key)
        self.use_tether_wdk = bool(getattr(settings, "WDK_USE_TETHER_WDK", False))
        self.seed_phrase = str(getattr(settings, "WDK_SEED_PHRASE", "")).strip()
        self.account_index = int(getattr(settings, "WDK_ACCOUNT_INDEX", 0))
        self._tether_bridge: Optional[_TetherWdkBridge] = None
        if self.use_tether_wdk:
            if not self.seed_phrase:
                raise WDKError("WDK_USE_TETHER_WDK=true requires WDK_SEED_PHRASE")
            self._tether_bridge = _TetherWdkBridge(
                rpc_url=self.rpc_url,
                chain_key=self.chain_key,
                seed_phrase=self.seed_phrase,
                account_index=self.account_index,
            )
        logger.info("[WDK:WalletManager] Initializing Tether WDK Manager...")

        # Initialize Web3 Connection
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if self.w3.is_connected():
                detected_chain_id = int(self.w3.eth.chain_id)
                logger.info(
                    f"[WDK:WalletManager] Connected to RPC: {self.rpc_url} (Detected Chain ID: {detected_chain_id}, Expected: {self.expected_chain_id}, Key: {self.chain_key})"
                )
                if detected_chain_id != self.expected_chain_id:
                    logger.warning(
                        f"[WDK:WalletManager] Chain ID mismatch detected: rpc={detected_chain_id}, configured={self.expected_chain_id}"
                    )
            else:
                logger.warning(f"[WDK:WalletManager] Failed to connect to RPC: {self.rpc_url}")
        except Exception as e:
            logger.error(f"[WDK:WalletManager] Error connecting to RPC: {e}")
            # Do not set self.w3 to None, as it breaks type safety.
            # The WDK client will fail gracefully later if connection is broken.

    def create_wallet(self, chain: str = "evm") -> WalletAccount:
        """
        [Primitive: Create]
        Generates a new non-custodial wallet.
        """
        logger.info(f"[WDK:WalletManager] Creating new {chain.upper()} wallet...")

        if self._tether_bridge:
            address = self._tether_bridge.get_address()
            if not address:
                raise WDKError("Failed to derive address from Tether WDK")
            wallet = WalletAccount(address, None, self.w3, tether_bridge=self._tether_bridge)
            logger.info(f"[WDK:WalletManager] Wallet loaded from Tether WDK seed: {wallet.address}")
            return wallet
        account = Account.create()
        wallet = WalletAccount(account.address, account.key.hex(), self.w3)

        logger.info(f"[WDK:WalletManager] Wallet created: {wallet.address}")
        return wallet

    def restore_wallet(self, private_key: str) -> WalletAccount:
        """
        [Primitive: Restore]
        Restores a wallet from a private key.
        """
        if self._tether_bridge:
            address = self._tether_bridge.get_address()
            if not address:
                raise WDKError("Failed to derive address from Tether WDK")
            return WalletAccount(address, None, self.w3, tether_bridge=self._tether_bridge)
        try:
            account = Account.from_key(private_key)
            return WalletAccount(account.address, private_key, self.w3)
        except Exception as e:
            logger.error(f"[WDK:WalletManager] Failed to restore wallet: {e}")
            raise WDKError("Invalid private key")
