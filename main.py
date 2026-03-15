import argparse
import logging
import sys
from typing import Dict, List

from security_monitor.agents.ai_analyzer import AIAnalyzer
from security_monitor.agents.allowance_monitor import AllowanceMonitorAgent
from security_monitor.agents.guardian_agent import GuardianAgent
from security_monitor.config.settings import get_settings
from security_monitor.core.blockchain import BlockchainClient
from security_monitor.core.wdk_client import WalletManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main Entry Point for the Security Monitor & Guardian Agent.

    Supports two modes:
    1. Monitor Mode: Passive scanning (Standard Auditing).
    2. Guardian Mode: Active Agent using Tether WDK (Hackathon Galactica).
    """
    settings = get_settings()

    # CLI Argument Parsing
    parser = argparse.ArgumentParser(
        description="""
        Blockchain Security Monitor & WDK Guardian Agent
        ================================================

        Features:
        - AI Guardian Agent (NEW): Autonomous agent that holds funds and executes transactions via Tether WDK.
        - WDK Integration: Direct implementation of Wallet Development Kit primitives.
        - Dual-Engine Risk Control: Deterministic Logic + Probabilistic AI.

        Usage Modes:
        1. Monitor Mode: Passive scanning (Standard Auditing).
        2. Guardian Mode: Active Agent using Tether WDK (Hackathon Galactica).
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Mode Selection (Monitor vs Guardian)
    parser.add_argument("--mode", choices=['monitor', 'guardian'], default='monitor', help="Operational Mode: 'monitor' (Passive) or 'guardian' (Active Agent with WDK)")

    # Monitor Mode Arguments
    parser.add_argument("--owner", type=str, help="Wallet address to check (Monitor Mode)")
    parser.add_argument("--spender", type=str, help="Spender contract address to check (Monitor Mode)")

    # Guardian Mode Arguments (WDK Actions)
    parser.add_argument("--action", choices=['transfer', 'approve', 'autonomous'], help="Action to perform (Guardian Mode)")
    parser.add_argument("--to", type=str, help="Destination address (Guardian Mode)")
    parser.add_argument("--amount", type=float, help="Amount to transfer (Guardian Mode)")
    parser.add_argument("--asset", choices=['USDT', 'USAT', 'XAUT'], default='USDT', help="Asset symbol for Guardian transfer")
    parser.add_argument(
        "--candidate",
        action="append",
        default=None,
        help="Autonomous candidate transfer. Format: <to>:<amount>[:<asset>], repeatable"
    )
    parser.add_argument(
        "--max-autonomous-tasks",
        type=int,
        default=3,
        help="Maximum successful transfers the autonomous planner can execute"
    )
    parser.add_argument(
        "--autonomous-budget",
        type=float,
        default=None,
        help="Maximum total amount the autonomous planner can execute in one run"
    )
    parser.add_argument(
        "--max-transfer-amount",
        type=float,
        default=None,
        help="Override policy max transfer amount for this run"
    )
    parser.add_argument(
        "--require-ai-approval",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override whether AI approval is required for transfer execution"
    )
    parser.add_argument(
        "--daily-total-limit",
        type=float,
        default=None,
        help="Override daily total transfer limit for this run"
    )
    parser.add_argument(
        "--daily-asset-limits",
        type=str,
        default=None,
        help="Override daily per-asset limits, format: USDT:3000,USAT:3000,XAUT:5"
    )
    parser.add_argument(
        "--allow-counterparty",
        action="append",
        default=None,
        help="Restrict transfers to specific counterparty address, repeatable"
    )

    # Common Arguments
    parser.add_argument("--token", type=str, help="Token contract address", default=settings.TARGET_TOKEN_ADDRESS)
    parser.add_argument(
        "--chain",
        choices=sorted(settings.CHAIN_RPC_URLS.keys()),
        default=settings.DEFAULT_CHAIN_KEY,
        help="Blockchain network key used for RPC and signing"
    )

    args = parser.parse_args()

    logger.info(f"Initializing Framework in {args.mode.upper()} Mode on {args.chain.upper()}...")

    try:
        # 1. Initialize Core Infrastructure
        client = BlockchainClient(chain_key=args.chain)

        # 2. Initialize Logic Engine (The Brain)
        monitor = AllowanceMonitorAgent(client, args.token)
        ai_analyzer = AIAnalyzer() # Optional AI Component

        if args.mode == 'monitor':
            run_monitor_mode(args, monitor, ai_analyzer)
        elif args.mode == 'guardian':
            run_guardian_mode(args, monitor, ai_analyzer)

    except Exception as e:
        logger.critical(f"Critical System Failure: {str(e)}")
        sys.exit(1)

def run_monitor_mode(args, monitor, ai_analyzer):
    """
    Standard Security Auditing Mode.
    Passive scan of allowances.
    """
    if not args.owner or not args.spender:
        logger.error("Monitor Mode requires --owner and --spender arguments.")
        sys.exit(1)

    logger.info(f"Checking allowance for Owner: {args.owner} -> Spender: {args.spender}")
    result = monitor.check_allowance(args.owner, args.spender)

    # AI Risk Analysis
    ai_feedback = ai_analyzer.analyze_risk(result)

    # Output Results
    if "error" in result:
        logger.error(f"Check Failed: {result['error']}")
        sys.exit(1)

    print("\n" + "="*50)
    print(f"SECURITY SCAN REPORT: {result['token']}")
    print("="*50)
    print(f"Owner:   {result['owner']}")
    print(f"Spender: {result['spender']}")
    print(f"Balance: {result['owner_balance']:,.2f} {result['token']}")
    print(f"Allowance: {result['allowance_formatted']:,.2f} {result['token']}")
    print(f"Risk Level: {result['risk_level']}")

    if ai_feedback:
        print("-" * 50)
        print("🤖 AI SECURITY ADVISOR (DeepSeek/Gemini)")
        print("-" * 50)
        print(ai_feedback)

    print("="*50 + "\n")

def run_guardian_mode(args, monitor, ai_analyzer):
    """
    [Hackathon Galactica Mode]
    Active Agent Mode integrating Tether WDK.
    Demonstrates autonomous fund management and secure execution.
    """
    if not args.action:
        logger.error("Guardian Mode requires --action.")
        sys.exit(1)
    if args.action in {"transfer", "approve"} and (not args.to or args.amount is None):
        logger.error("Guardian transfer/approve requires --to and --amount.")
        sys.exit(1)
    if args.action == "autonomous" and not args.candidate:
        logger.error("Guardian autonomous action requires at least one --candidate.")
        sys.exit(1)

    # Initialize WDK Manager (Orchestrator)
    logger.info("Initializing WDK Wallet Manager...")
    wdk_manager = WalletManager(chain_key=args.chain)

    # Create or Load a Wallet Account (The Actor)
    # Check for private key in environment variables (Secure Pattern)
    import os
    env_key = os.getenv("WDK_PRIVATE_KEY")

    if env_key:
        logger.info("[Main] Found WDK_PRIVATE_KEY in environment. Restoring wallet...")
        wallet_account = wdk_manager.restore_wallet(env_key)
    else:
        logger.info("[Main] No private key found. Creating new ephemeral wallet...")
        wallet_account = wdk_manager.create_wallet(chain="evm")

    # Initialize Guardian Agent (The Brain + Hands)
    policy_overrides = {}
    if args.max_transfer_amount is not None:
        policy_overrides["max_transfer_amount"] = args.max_transfer_amount
    if args.require_ai_approval is not None:
        policy_overrides["require_ai_approval"] = args.require_ai_approval
    if args.daily_total_limit is not None:
        policy_overrides["daily_total_limit"] = args.daily_total_limit
    if args.daily_asset_limits:
        policy_overrides["daily_asset_limits"] = args.daily_asset_limits
    if args.allow_counterparty:
        policy_overrides["allowed_counterparties"] = args.allow_counterparty

    guardian = GuardianAgent(wallet_account, monitor, ai_analyzer, policy_overrides=policy_overrides)

    if args.action == 'transfer':
        # Enhanced UX for Guardian Mode
        try:
            from rich.console import Console
            console = Console()
            console.rule("[bold green]STARTING GUARDIAN SEQUENCE[/bold green]")
        except ImportError:
            pass

        logger.info("Guardian Agent: Initiating secure transfer via WDK...")
        result = guardian.run_transfer_task(args.to, args.amount, args.asset)

        # Clean Output for Results
        if 'console' in locals():
            console.rule("[bold green]MISSION REPORT[/bold green]")
        else:
            print("\n" + "="*50)
            print(f"GUARDIAN AGENT REPORT: {result.get('status', 'UNKNOWN').upper()}")
            print("="*50)

        if result.get('status') == 'success':
            if 'console' in locals():
                from rich.panel import Panel
                console.print(Panel(
                    f"[bold]Transaction Hash:[/bold] {result.get('tx_hash')}\n"
                    f"[bold]From:[/bold]   {result.get('from_address')}\n"
                    f"[bold]To:[/bold]     {result.get('to_address')}\n"
                    f"[bold]Amount:[/bold] {result.get('amount')} {result.get('token')}\n"
                    f"[bold]Nonce:[/bold]  {result.get('nonce')}",
                    title="[bold green]✅ TRANSACTION EXECUTED VIA WDK[/bold green]",
                    border_style="green"
                ))
            else:
                print("✅ TRANSACTION EXECUTED VIA WDK")
                print(f"Transaction Hash: {result.get('tx_hash')}")
                print(f"From:   {result.get('from_address')}")
                print(f"To:     {result.get('to_address')}")
                print(f"Amount: {result.get('amount')} {result.get('token')}")
        else:
            if 'console' in locals():
                from rich.panel import Panel
                console.print(Panel(
                    f"[bold]Reason:[/bold] {result.get('reason', 'Unknown Error')}\n"
                    f"[bold]Risk Level:[/bold] {result.get('risk_level', 'UNKNOWN')}",
                    title="[bold red]🛑 TRANSACTION BLOCKED BY AI GUARDIAN[/bold red]",
                    border_style="red"
                ))
            else:
                print("🛑 TRANSACTION BLOCKED BY AI GUARDIAN")
                print(f"Reason: {result.get('reason', 'Unknown Error')}")
                print(f"Risk Level: {result.get('risk_level', 'UNKNOWN')}")

        print("="*50 + "\n")
    elif args.action == "autonomous":
        candidates = _parse_autonomous_candidates(args.candidate or [], args.asset)
        result = guardian.run_autonomous_tasks(
            candidates=candidates,
            max_tasks=args.max_autonomous_tasks,
            budget=args.autonomous_budget,
        )
        print("\n" + "=" * 50)
        print("GUARDIAN AUTONOMOUS RUN REPORT")
        print("=" * 50)
        print(f"Planned:   {result.get('planned_count', 0)}")
        print(f"Executed:  {result.get('executed_count', 0)}")
        print(f"Blocked:   {result.get('blocked_count', 0)}")
        print(f"Errors:    {result.get('error_count', 0)}")
        print(f"Total Sent:{result.get('executed_total', 0)}")
        print("-" * 50)
        for item in result.get("results", []):
            status = str(item.get("status", "unknown")).upper()
            to_address = item.get("to_address", "N/A")
            amount = item.get("amount", "N/A")
            token = item.get("token", "N/A")
            reason = item.get("reason", "")
            tx_hash = item.get("tx_hash", "")
            line = f"[{status}] {amount} {token} -> {to_address}"
            if tx_hash:
                line = f"{line} | tx={tx_hash}"
            if reason:
                line = f"{line} | reason={reason}"
            print(line)
        print("=" * 50 + "\n")


def _parse_autonomous_candidates(raw_candidates: List[str], default_asset: str) -> List[Dict[str, object]]:
    parsed: List[Dict[str, object]] = []
    for raw in raw_candidates:
        item = str(raw).strip()
        parts = [segment.strip() for segment in item.split(":")]
        if len(parts) not in {2, 3}:
            raise ValueError(f"Invalid candidate format: {raw}")
        to_address = parts[0]
        amount = float(parts[1])
        token_symbol = parts[2].upper() if len(parts) == 3 else default_asset.upper()
        parsed.append(
            {
                "to_address": to_address,
                "amount": amount,
                "token_symbol": token_symbol,
            }
        )
    return parsed

if __name__ == "__main__":
    main()
