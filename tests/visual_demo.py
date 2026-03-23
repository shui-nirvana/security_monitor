import argparse
import re
import time
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, List, cast
from unittest.mock import patch

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from security_monitor.agents.ai_analyzer import AIAnalyzer
from security_monitor.agents.guardian_agent import GuardianAgent

console = Console()


class DemoWeb3:
    @staticmethod
    def is_address(value: str) -> bool:
        return bool(re.fullmatch(r"0x[a-fA-F0-9]{40}", value))


class DemoWallet:
    def __init__(self):
        self.address = "0x1111111111111111111111111111111111111111"
        self.tx_count = 0

    def send_transaction(self, to_address: str, amount: float, token_symbol: str) -> Dict[str, Any]:
        self.tx_count += 1
        tx_hash = "0x" + format(self.tx_count, "064x")
        return {
            "status": "success",
            "tx_hash": tx_hash,
            "from_address": self.address,
            "to_address": to_address,
            "amount": str(amount),
            "token": token_symbol,
            "block_number": 12345678 + self.tx_count,
            "nonce": self.tx_count,
        }


@dataclass
class DemoOutcome:
    scene: str
    requirement: str
    expected: str
    actual: str
    passed: bool


class CompetitionDemo:
    def __init__(self, speed: float):
        self.speed = speed

    @staticmethod
    def _settings(
        max_transfer: float = 1000,
        supported_assets: str = "USDT,USAT,XAUT",
        blocklist: str = "0x000000000000000000000000000000000000dead,0x6666666666666666666666666666666666666666",
        require_ai_approval: bool = True,
        daily_total_limit: float = 5000,
        daily_asset_limits: str = "USDT:3000,USAT:3000,XAUT:5",
    ) -> SimpleNamespace:
        return SimpleNamespace(
            GUARDIAN_MAX_TRANSFER_AMOUNT=max_transfer,
            GUARDIAN_SUPPORTED_ASSETS=supported_assets,
            GUARDIAN_BLOCKLIST=blocklist,
            GUARDIAN_ALLOWED_COUNTERPARTIES="",
            GUARDIAN_REQUIRE_AI_APPROVAL=require_ai_approval,
            GUARDIAN_DAILY_TOTAL_LIMIT=daily_total_limit,
            GUARDIAN_DAILY_ASSET_LIMITS=daily_asset_limits,
        )

    def _guardian(
        self,
        wallet: DemoWallet,
        require_ai_approval: bool = True,
        max_transfer: float = 1000,
        daily_total_limit: float = 5000,
        daily_asset_limits: str = "USDT:3000,USAT:3000,XAUT:5",
    ) -> GuardianAgent:
        monitor = SimpleNamespace(client=SimpleNamespace(w3=DemoWeb3()))
        ai = AIAnalyzer()
        if ai.enabled:
            ai.simulation_mode = True
        with patch(
            "security_monitor.agents.guardian_agent.get_settings",
            return_value=self._settings(
                require_ai_approval=require_ai_approval,
                max_transfer=max_transfer,
                daily_total_limit=daily_total_limit,
                daily_asset_limits=daily_asset_limits,
            ),
        ):
            return GuardianAgent(cast(Any, wallet), cast(Any, monitor), ai)

    def _pause(self):
        if self.speed > 0:
            time.sleep(self.speed)

    def run(self) -> List[DemoOutcome]:
        outcomes: List[DemoOutcome] = []
        console.clear()
        console.print(
            Panel.fit(
                "Tether WDK Guardian Demo\n"
                "Goal: Cover safety, autonomy, and end-to-end WDK execution in one run",
                title="Competition Demo",
                border_style="cyan",
            )
        )
        self._pause()

        wallet_success = DemoWallet()
        guardian_success = self._guardian(wallet_success, require_ai_approval=False)
        with console.status("[bold yellow]Scene 1/5: Executing safe transfer...[/bold yellow]", spinner="dots"):
            result_success = guardian_success.run_transfer_task(
                "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                30,
                "USDT",
            )
        outcomes.append(
            DemoOutcome(
                scene="Scene 1: Safe Transfer",
                requirement="Real WDK execution path",
                expected="status=success and tx_hash generated",
                actual=f"status={result_success.get('status')}, tx={result_success.get('tx_hash', '-')}",
                passed=result_success.get("status") == "success" and "tx_hash" in result_success,
            )
        )
        self._pause()

        wallet_limit = DemoWallet()
        guardian_limit = self._guardian(wallet_limit, require_ai_approval=False, max_transfer=40)
        with console.status("[bold yellow]Scene 2/5: Validating policy limit block...[/bold yellow]", spinner="line"):
            result_limit = guardian_limit.run_transfer_task(
                "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                60,
                "USDT",
            )
        outcomes.append(
            DemoOutcome(
                scene="Scene 2: Policy Limit Block",
                requirement="Permission and amount risk controls",
                expected="status=blocked and WDK not invoked",
                actual=f"status={result_limit.get('status')}, wallet_tx_count={wallet_limit.tx_count}",
                passed=result_limit.get("status") == "blocked" and wallet_limit.tx_count == 0,
            )
        )
        self._pause()

        wallet_blacklist = DemoWallet()
        guardian_blacklist = self._guardian(wallet_blacklist, require_ai_approval=False)
        with console.status("[bold yellow]Scene 3/5: Validating blacklist override...[/bold yellow]", spinner="runner"):
            result_blacklist = guardian_blacklist.run_transfer_task(
                "0x000000000000000000000000000000000000dEaD",
                10,
                "USDT",
            )
        outcomes.append(
            DemoOutcome(
                scene="Scene 3: Blacklist Override",
                requirement="Safety-first deterministic guardrail",
                expected="status=blocked and no WDK signing",
                actual=f"status={result_blacklist.get('status')}, wallet_tx_count={wallet_blacklist.tx_count}",
                passed=result_blacklist.get("status") == "blocked" and wallet_blacklist.tx_count == 0,
            )
        )
        self._pause()

        wallet_auto = DemoWallet()
        guardian_auto = self._guardian(wallet_auto, require_ai_approval=False, daily_total_limit=1000)
        with console.status("[bold yellow]Scene 4/5: Validating autonomous planner...[/bold yellow]", spinner="earth"):
            auto_result = guardian_auto.run_autonomous_tasks(
                candidates=[
                    {"to_address": "0x1111111111111111111111111111111111111111", "amount": 8, "token_symbol": "USDT"},
                    {"to_address": "0x2222222222222222222222222222222222222222", "amount": 5, "token_symbol": "USDT"},
                    {"to_address": "0x3333333333333333333333333333333333333333", "amount": 20, "token_symbol": "USDT"},
                ],
                max_tasks=2,
                budget=12,
            )
        outcomes.append(
            DemoOutcome(
                scene="Scene 4: Autonomous Planner",
                requirement="Autonomous planning with budget control",
                expected="execute 1, block 2, total<=12",
                actual=(
                    f"executed={auto_result.get('executed_count')}, "
                    f"blocked={auto_result.get('blocked_count')}, "
                    f"total={auto_result.get('executed_total')}"
                ),
                passed=(
                    auto_result.get("executed_count") == 1
                    and auto_result.get("blocked_count") == 2
                    and float(auto_result.get("executed_total", 0)) <= 12
                ),
            )
        )
        self._pause()

        wallet_ai = DemoWallet()
        guardian_ai = self._guardian(
            wallet_ai,
            require_ai_approval=True,
            max_transfer=10000,
            daily_total_limit=10000,
            daily_asset_limits="USDT:10000,USAT:3000,XAUT:5",
        )
        with console.status("[bold yellow]Scene 5/5: Validating AI veto path...[/bold yellow]", spinner="dots12"):
            ai_result = guardian_ai.run_transfer_task(
                "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                6001,
                "USDT",
            )
        outcomes.append(
            DemoOutcome(
                scene="Scene 5: AI Veto",
                requirement="Dual-engine risk control (AI + rules)",
                expected="High-risk transfer blocked by AI without WDK call",
                actual=(
                    f"status={ai_result.get('status')}, "
                    f"reason={ai_result.get('reason', '-')}, "
                    f"wallet_tx_count={wallet_ai.tx_count}"
                ),
                passed=ai_result.get("status") == "blocked" and wallet_ai.tx_count == 0,
            )
        )
        return outcomes


def render_results(outcomes: List[DemoOutcome]) -> int:
    table = Table(title="Competition Requirement Mapping", header_style="bold cyan")
    table.add_column("Scene", style="bold")
    table.add_column("Requirement")
    table.add_column("Expected")
    table.add_column("Actual")
    table.add_column("Result", justify="center")

    passed_count = 0
    for item in outcomes:
        verdict = "[green]PASS[/green]" if item.passed else "[red]FAIL[/red]"
        if item.passed:
            passed_count += 1
        table.add_row(item.scene, item.requirement, item.expected, item.actual, verdict)

    console.print()
    console.print(table)
    console.print()
    if passed_count == len(outcomes):
        console.print(Panel.fit("✅ Demo passed all scenarios and is ready for the competition pitch", border_style="green"))
        return 0
    console.print(Panel.fit("❌ Demo has failed scenarios. Please fix them before pitching", border_style="red"))
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Tether WDK Competition Demo Runner")
    parser.add_argument(
        "--speed",
        type=float,
        default=0.2,
        help="Wait time in seconds between scenes, use 0 for fast mode",
    )
    args = parser.parse_args()

    outcomes = CompetitionDemo(speed=max(args.speed, 0)).run()
    return render_results(outcomes)


if __name__ == "__main__":
    raise SystemExit(main())
