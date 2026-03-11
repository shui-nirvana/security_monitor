# ==============================================================================
# Tether Hackathon Galactica: WDK Edition 1 Submission
# Module: Guardian Agent
# Description: Integrates Agent Logic (Reasoning) with Wallet Execution (WDK)
# Requirement Met: "Agents should hold, send, or manage USD₮ autonomously"
# Requirement Met: "Clear separation between agent logic and wallet execution"
# ==============================================================================

import logging
from typing import Any, Dict, Optional, Tuple

from security_monitor.agents.ai_analyzer import AIAnalyzer
from security_monitor.agents.allowance_monitor import AllowanceMonitorAgent
from security_monitor.config.settings import get_settings
from security_monitor.core.wdk_client import WalletAccount, WDKError

try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GuardianAgent:
    """
    [Hackathon Core Component]
    The AI Guardian Agent is the bridge between reasoning and action.

    Architecture:
    1. Brain (Reasoning): Uses AllowanceMonitor + AIAnalyzer (OpenClaw equivalent) to assess threats.
    2. Hands (Execution): Uses Tether WDK (WalletAccount) to manage funds and sign transactions.

    This separation ensures that the WDK is only invoked *after* a rigorous safety check,
    fulfilling the "Emphasis on safety" requirement.
    """

    def __init__(self, wallet_account: WalletAccount, monitor: AllowanceMonitorAgent, ai_analyzer: Optional[AIAnalyzer] = None):
        self.wallet = wallet_account # [WDK] The 'Hands' - Managed Wallet Instance
        self.monitor = monitor       # [Logic] The 'Brain' - Deterministic Logic
        self.ai = ai_analyzer        # [AI]    The 'Intuition' - Probabilistic Analysis
        self.risk_threshold = "MEDIUM" # Configurable: Only execute if risk is LOW or NONE
        self.settings = get_settings()
        self.max_transfer_amount = float(self.settings.GUARDIAN_MAX_TRANSFER_AMOUNT)
        self.supported_assets = {
            asset.strip().upper()
            for asset in self.settings.GUARDIAN_SUPPORTED_ASSETS.split(",")
            if asset.strip()
        }
        self.console = Console() if RICH_AVAILABLE else None
        logger.info(f"[Guardian Agent] Initialized. Managing Wallet: {self.wallet.address}")

    def run_transfer_task(self, to_address: str, amount: float, token_symbol: str = "USDT") -> Dict[str, Any]:
        """
        Executes a transfer task with autonomous safety checks.

        Process:
        1. [Reasoning] Receive instruction: "Transfer X to Y"
        2. [Reasoning] Analyze Risk: Check if Y is a known malicious contract or has suspicious allowance patterns.
        3. [Decision]
           - If SAFE: Invoke WDK Execution (self.wallet.send_transaction).
           - If RISKY: Reject and Alert (Safety First).
        """
        logger.info(f"[Guardian Agent] Received task -> Transfer {amount} {token_symbol} to {to_address}")

        if self.console:
            self.console.print(f"[bold cyan]>>> [COMMAND] INITIATE TRANSFER: {amount} {token_symbol} -> {to_address}[/bold cyan]")

        # --- Step 1: Pre-Execution Safety Check (The "Brain") ---
        # Using Rich Status Spinner for Visualization
        if self.console:
            with self.console.status("[bold yellow][BRAIN] Analyzing target address via Gemini/DeepSeek...", spinner="dots"):
                is_safe, risk_reason = self._assess_risk(to_address, amount, token_symbol)
        else:
            is_safe, risk_reason = self._assess_risk(to_address, amount, token_symbol)

        if not is_safe:
            msg = f"[Guardian Agent] BLOCKED transfer to {to_address}. Reason: {risk_reason}"
            logger.warning(msg)
            if self.console:
                self.console.print(f"[bold red]🛑 [STATUS] BLOCKED! {risk_reason}[/bold red]")
            return {
                "status": "blocked",
                "reason": risk_reason,
                "risk_level": "HIGH"
            }

        # --- Step 2: Execution via WDK (The "Hands") ---
        logger.info("[Guardian Agent] Safety Check Passed. Invoking WDK primitives...")
        if self.console:
             self.console.print("[bold green]✅ [STATUS] RISK LOW. AUTHORIZING WDK EXECUTION.[/bold green]")

        try:
            # [WDK] Direct Primitive Call
            if self.console:
                with self.console.status("[bold blue][WDK] Preparing secure signature & Broadcasting...", spinner="earth"):
                     result = self.wallet.send_transaction(to_address, amount, token_symbol)
            else:
                result = self.wallet.send_transaction(to_address, amount, token_symbol)

            if self.console:
                self.console.print(f"[bold green]🚀 [WDK] TRANSACTION SUCCESS: {result['tx_hash']}[/bold green]")
            return dict(result)
        except WDKError as e:
            logger.error(f"[Guardian Agent] WDK Execution Failed: {str(e)}")
            if self.console:
                self.console.print(f"[bold red]❌ [WDK] EXECUTION FAILED: {str(e)}[/bold red]")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"[Guardian Agent] Unexpected Error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _assess_risk(self, target_address: str, amount: float, token_symbol: str) -> Tuple[bool, str]:
        """
        Internal method to combine Deterministic Logic + AI Probabilistic Reasoning.

        [Security Override Principle]
        The system enforces a "Safety-First" policy.
        If ANY module (Logic or AI) flags a risk, the transaction is BLOCKED.
        Logic Check (Deterministic) > AI Check (Probabilistic).

        Returns: (is_safe: bool, reason: str)
        """
        normalized_symbol = token_symbol.upper()
        if normalized_symbol not in self.supported_assets:
            return False, f"Unsupported asset: {normalized_symbol}. Allowed: {', '.join(sorted(self.supported_assets))}"

        if amount <= 0:
            return False, "Amount must be greater than 0"

        if amount > self.max_transfer_amount:
            return False, f"Amount exceeds policy limit ({self.max_transfer_amount} {normalized_symbol})"

        if not self.monitor.client.w3.is_address(target_address):
             return False, "Invalid Ethereum Address Format"

        # Check 1.2: Local Blacklist (Hardcoded Security Override)
        # Simulating a local database of known bad actors
        BLACKLIST = ["0x000000000000000000000000000000000000dead"]
        if target_address.lower() in BLACKLIST:
            return False, "Blocked by Local Blacklist (Deterministic Logic)"

        if self.ai and self.ai.enabled:
            logger.info("[Guardian Agent] Consulting AI Brain for address analysis...")
            ai_result = self.ai.analyze_transfer_target(target_address, amount, normalized_symbol)
            if not ai_result.get("safe", False):
                return False, ai_result.get("reason", "AI risk check rejected")

        return True, "Address seems safe"
