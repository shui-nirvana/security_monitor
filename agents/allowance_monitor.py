from typing import Any, Dict

from web3 import Web3

from security_monitor.core.blockchain import BlockchainClient, logger

# Standard ERC-20 ABI (Minimal for Allowance)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

class AllowanceMonitorAgent:
    """
    Agent responsible for monitoring token approvals (allowances).
    High allowances to unknown spenders are a major security risk.
    """
    def __init__(self, client: BlockchainClient, token_address: str):
        self.client = client
        self.contract = self.client.get_contract(token_address, ERC20_ABI)
        self.token_symbol = self._get_symbol()
        self.decimals = self._get_decimals()

        logger.info(f"Initialized Monitor for {self.token_symbol} ({token_address})")

    def _get_symbol(self) -> str:
        try:
            symbol = self.client.call_contract_function(self.contract.functions.symbol)
            return symbol if symbol else "UNKNOWN"
        except Exception:
            return "UNKNOWN"

    def _get_decimals(self) -> int:
        try:
            decimals = self.client.call_contract_function(self.contract.functions.decimals)
            return decimals if decimals is not None else 18
        except Exception:
            return 18

    def check_allowance(self, owner: str, spender: str) -> Dict[str, Any]:
        """
        Checks the allowance granted by owner to spender.
        Returns a risk assessment object.
        """
        try:
            # Ensure addresses are checksummed
            owner_checksum = Web3.to_checksum_address(owner)
            spender_checksum = Web3.to_checksum_address(spender)

            # Get Raw Allowance
            # Note: client.call_contract_function expects (func, *args)
            allowance_wei = self.client.call_contract_function(
                self.contract.functions.allowance, owner_checksum, spender_checksum
            )

            if allowance_wei is None:
                logger.error(f"Failed to fetch allowance for {owner} -> {spender}")
                return {"status": "error", "error": "Failed to fetch allowance"}

            # Get User Balance (for context)
            balance_wei = self.client.call_contract_function(
                self.contract.functions.balanceOf, owner_checksum
            )

            if balance_wei is None:
                balance_wei = 0
                logger.warning(f"Failed to fetch balance for {owner}, assuming 0")


            # Format Values
            allowance_fmt = allowance_wei / (10 ** self.decimals)
            balance_fmt = balance_wei / (10 ** self.decimals) if balance_wei else 0

            risk_level = "LOW"
            if allowance_wei > 0:
                if allowance_wei > balance_wei and balance_wei > 0:
                     risk_level = "HIGH (Unlimited/Excessive)"
                elif allowance_wei > (10000 * (10**self.decimals)):
                     risk_level = "MEDIUM (Large Amount)"

            logger.info(f"Checked Allowance: Owner={owner[:6]}... -> Spender={spender[:6]}... | Amount={allowance_fmt:.2f} {self.token_symbol} | Risk={risk_level}")

            return {
                "token": self.token_symbol,
                "owner": owner,
                "spender": spender,
                "allowance_raw": allowance_wei,
                "allowance_formatted": allowance_fmt,
                "owner_balance": balance_fmt,
                "risk_level": risk_level
            }

        except Exception as e:
            logger.error(f"Error checking allowance: {str(e)}")
            return {"status": "error", "error": str(e)}
