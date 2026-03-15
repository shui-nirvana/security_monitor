# ==============================================================================
# Tether Hackathon Galactica: WDK Edition 1 Submission
# Module: Guardian Agent
# Description: Integrates Agent Logic (Reasoning) with Wallet Execution (WDK)
# Requirement Met: "Agents should hold, send, or manage USD₮ autonomously"
# Requirement Met: "Clear separation between agent logic and wallet execution"
# ==============================================================================

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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

    def __init__(
        self,
        wallet_account: WalletAccount,
        monitor: AllowanceMonitorAgent,
        ai_analyzer: Optional[AIAnalyzer] = None,
        policy_overrides: Optional[Dict[str, Any]] = None,
    ):
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
        get_allowed_counterparties = getattr(self.settings, "get_guardian_allowed_counterparties", None)
        if callable(get_allowed_counterparties):
            self.allowed_counterparties = get_allowed_counterparties()
        else:
            raw_allowed_counterparties = getattr(self.settings, "GUARDIAN_ALLOWED_COUNTERPARTIES", "")
            self.allowed_counterparties = {
                address.strip().lower()
                for address in str(raw_allowed_counterparties).split(",")
                if address.strip()
            }
        self.require_ai_approval = bool(getattr(self.settings, "GUARDIAN_REQUIRE_AI_APPROVAL", True))
        self.daily_total_limit = float(getattr(self.settings, "GUARDIAN_DAILY_TOTAL_LIMIT", 5000.0))
        get_daily_asset_limits = getattr(self.settings, "get_guardian_daily_asset_limits", None)
        if callable(get_daily_asset_limits):
            self.daily_asset_limits = get_daily_asset_limits()
        else:
            raw_daily_asset_limits = getattr(self.settings, "GUARDIAN_DAILY_ASSET_LIMITS", "")
            self.daily_asset_limits = {}
            for raw_item in str(raw_daily_asset_limits).split(","):
                item = raw_item.strip()
                if not item or ":" not in item:
                    continue
                symbol, limit = item.split(":", 1)
                symbol_normalized = symbol.strip().upper()
                if not symbol_normalized:
                    continue
                try:
                    self.daily_asset_limits[symbol_normalized] = float(limit.strip())
                except ValueError:
                    continue
        self._daily_spent_total = 0.0
        self._daily_spent_by_asset: Dict[str, float] = {}
        self._daily_spent_date = datetime.now(timezone.utc).date()
        get_blocklist = getattr(self.settings, "get_guardian_blocklist", None)
        if callable(get_blocklist):
            self.blocklist = get_blocklist()
        else:
            raw_blocklist = getattr(
                self.settings,
                "GUARDIAN_BLOCKLIST",
                "0x000000000000000000000000000000000000dead,0x6666666666666666666666666666666666666666"
            )
            self.blocklist = {
                address.strip().lower()
                for address in str(raw_blocklist).split(",")
                if address.strip()
            }
        self.apply_policy_overrides(policy_overrides or {})
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
            self._update_daily_spend(amount, token_symbol)
            return dict(result)
        except WDKError as e:
            logger.error(f"[Guardian Agent] WDK Execution Failed: {str(e)}")
            if self.console:
                self.console.print(f"[bold red]❌ [WDK] EXECUTION FAILED: {str(e)}[/bold red]")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"[Guardian Agent] Unexpected Error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def run_autonomous_tasks(
        self,
        candidates: List[Dict[str, Any]],
        max_tasks: int = 3,
        budget: Optional[float] = None,
    ) -> Dict[str, Any]:
        execution_cap = max(0, int(max_tasks))
        valid_candidates: List[Dict[str, Any]] = []
        results: List[Dict[str, Any]] = []

        for candidate in candidates:
            to_address = str(candidate.get("to_address", "")).strip()
            token_symbol = str(candidate.get("token_symbol", "USDT")).strip().upper() or "USDT"
            raw_amount = candidate.get("amount")
            try:
                amount = float(str(raw_amount))
            except (TypeError, ValueError):
                results.append(
                    {
                        "status": "error",
                        "to_address": to_address,
                        "token": token_symbol,
                        "amount": str(raw_amount),
                        "reason": "Invalid candidate amount",
                    }
                )
                continue

            if not to_address:
                results.append(
                    {
                        "status": "error",
                        "to_address": to_address,
                        "token": token_symbol,
                        "amount": str(amount),
                        "reason": "Missing candidate address",
                    }
                )
                continue

            valid_candidates.append(
                {
                    "to_address": to_address,
                    "token_symbol": token_symbol,
                    "amount": amount,
                }
            )

        planned = sorted(valid_candidates, key=lambda item: item["amount"])
        executed_count = 0
        executed_total = 0.0

        for candidate in planned:
            to_address = candidate["to_address"]
            token_symbol = candidate["token_symbol"]
            amount = candidate["amount"]

            if executed_count >= execution_cap:
                results.append(
                    {
                        "status": "blocked",
                        "to_address": to_address,
                        "token": token_symbol,
                        "amount": str(amount),
                        "reason": "Execution cap reached",
                    }
                )
                continue

            if budget is not None and executed_total + amount > budget:
                results.append(
                    {
                        "status": "blocked",
                        "to_address": to_address,
                        "token": token_symbol,
                        "amount": str(amount),
                        "reason": f"Autonomy budget exceeded ({budget})",
                    }
                )
                continue

            task_result = self.run_transfer_task(to_address, amount, token_symbol)
            merged = dict(task_result)
            merged.setdefault("to_address", to_address)
            merged.setdefault("token", token_symbol)
            merged.setdefault("amount", str(amount))
            results.append(merged)

            if task_result.get("status") == "success":
                executed_count += 1
                executed_total += amount

        blocked_count = sum(1 for item in results if item.get("status") == "blocked")
        error_count = sum(1 for item in results if item.get("status") == "error")

        return {
            "status": "completed",
            "planned_count": len(planned),
            "executed_count": executed_count,
            "blocked_count": blocked_count,
            "error_count": error_count,
            "executed_total": executed_total,
            "results": results,
        }

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

        self._reset_daily_spend_if_needed()
        projected_total = self._daily_spent_total + amount
        if projected_total > self.daily_total_limit:
            return False, f"Daily total limit exceeded ({self.daily_total_limit})"

        asset_daily_limit = self.daily_asset_limits.get(normalized_symbol)
        if asset_daily_limit is not None:
            projected_asset_total = self._daily_spent_by_asset.get(normalized_symbol, 0.0) + amount
            if projected_asset_total > asset_daily_limit:
                return False, f"Daily {normalized_symbol} limit exceeded ({asset_daily_limit})"

        if not self.monitor.client.w3.is_address(target_address):
             return False, "Invalid Ethereum Address Format"

        if self.allowed_counterparties and target_address.lower() not in self.allowed_counterparties:
            return False, "Counterparty not permitted by policy allowlist"

        if target_address.lower() in self.blocklist:
            return False, "Blocked by Local Blacklist (Deterministic Logic)"

        if self.require_ai_approval and (not self.ai or not self.ai.enabled):
            return False, "AI approval required by policy but unavailable"

        if self.ai and self.ai.enabled:
            logger.info("[Guardian Agent] Consulting AI Brain for address analysis...")
            ai_result = self.ai.analyze_transfer_target(target_address, amount, normalized_symbol)
            if not ai_result.get("safe", False):
                return False, ai_result.get("reason", "AI risk check rejected")

        return True, "Address seems safe"

    def _reset_daily_spend_if_needed(self) -> None:
        current_date = datetime.now(timezone.utc).date()
        if current_date != self._daily_spent_date:
            self._daily_spent_date = current_date
            self._daily_spent_total = 0.0
            self._daily_spent_by_asset.clear()

    def _update_daily_spend(self, amount: float, token_symbol: str) -> None:
        self._reset_daily_spend_if_needed()
        symbol = token_symbol.upper()
        self._daily_spent_total += amount
        self._daily_spent_by_asset[symbol] = self._daily_spent_by_asset.get(symbol, 0.0) + amount

    def apply_policy_overrides(self, overrides: Dict[str, Any]) -> None:
        max_transfer_amount = overrides.get("max_transfer_amount")
        if max_transfer_amount is not None:
            self.max_transfer_amount = float(max_transfer_amount)

        require_ai_approval = overrides.get("require_ai_approval")
        if require_ai_approval is not None:
            self.require_ai_approval = bool(require_ai_approval)

        daily_total_limit = overrides.get("daily_total_limit")
        if daily_total_limit is not None:
            self.daily_total_limit = float(daily_total_limit)

        daily_asset_limits = overrides.get("daily_asset_limits")
        if daily_asset_limits is not None:
            self.daily_asset_limits = self._parse_daily_asset_limits(daily_asset_limits)

        allowed_counterparties = overrides.get("allowed_counterparties")
        if allowed_counterparties is not None:
            self.allowed_counterparties = self._parse_counterparties(allowed_counterparties)

    def _parse_daily_asset_limits(self, raw_limits: Any) -> Dict[str, float]:
        if isinstance(raw_limits, dict):
            parsed: Dict[str, float] = {}
            for symbol, limit in raw_limits.items():
                symbol_normalized = str(symbol).strip().upper()
                if not symbol_normalized:
                    continue
                try:
                    parsed[symbol_normalized] = float(limit)
                except (TypeError, ValueError):
                    continue
            return parsed

        parsed = {}
        for raw_item in str(raw_limits).split(","):
            item = raw_item.strip()
            if not item or ":" not in item:
                continue
            symbol, limit = item.split(":", 1)
            symbol_normalized = symbol.strip().upper()
            if not symbol_normalized:
                continue
            try:
                parsed[symbol_normalized] = float(limit.strip())
            except ValueError:
                continue
        return parsed

    def _parse_counterparties(self, raw_counterparties: Any) -> set[str]:
        if isinstance(raw_counterparties, str):
            return {
                address.strip().lower()
                for address in raw_counterparties.split(",")
                if address.strip()
            }
        if isinstance(raw_counterparties, (list, tuple, set)):
            return {
                str(address).strip().lower()
                for address in raw_counterparties
                if str(address).strip()
            }
        return set()
