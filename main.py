import argparse
import sys
import logging
from config.settings import get_settings
from core.blockchain import BlockchainClient
from core.wdk_client import WDKClient
from agents.allowance_monitor import AllowanceMonitorAgent
from agents.ai_analyzer import AIAnalyzer
from agents.guardian_agent import GuardianAgent

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
    parser = argparse.ArgumentParser(description="Blockchain Security Monitor & WDK Guardian Agent")
    
    # Mode Selection (Monitor vs Guardian)
    parser.add_argument("--mode", choices=['monitor', 'guardian'], default='monitor', help="Operational Mode: 'monitor' (Passive) or 'guardian' (Active Agent with WDK)")
    
    # Monitor Mode Arguments
    parser.add_argument("--owner", type=str, help="Wallet address to check (Monitor Mode)")
    parser.add_argument("--spender", type=str, help="Spender contract address to check (Monitor Mode)")
    
    # Guardian Mode Arguments (WDK Actions)
    parser.add_argument("--action", choices=['transfer', 'approve'], help="Action to perform (Guardian Mode)")
    parser.add_argument("--to", type=str, help="Destination address (Guardian Mode)")
    parser.add_argument("--amount", type=float, help="Amount to transfer (Guardian Mode)")
    
    # Common Arguments
    parser.add_argument("--token", type=str, help="Token contract address", default=settings.TARGET_TOKEN_ADDRESS)
    
    args = parser.parse_args()

    logger.info(f"Initializing Framework in {args.mode.upper()} Mode...")
    
    try:
        # 1. Initialize Core Infrastructure
        client = BlockchainClient()
        
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
    if not args.action or not args.to or not args.amount:
        logger.error("Guardian Mode requires --action, --to, and --amount.")
        sys.exit(1)

    # Initialize WDK Client (Simulated for Demo)
    wdk = WDKClient()
    wdk.create_wallet() # In a real app, we'd load an existing wallet securely
    
    # Initialize Guardian Agent (The Brain + Hands)
    guardian = GuardianAgent(wdk, monitor, ai_analyzer)
    
    if args.action == 'transfer':
        logger.info(f"Guardian Agent: Initiating secure transfer via WDK...")
        result = guardian.run_transfer_task(args.to, args.amount, "USDT")
        
        print("\n" + "="*50)
        print(f"GUARDIAN AGENT REPORT: {result.get('status', 'UNKNOWN').upper()}")
        print("="*50)
        
        if result.get('status') == 'success':
            print("✅ TRANSACTION EXECUTED VIA WDK")
            print(f"Transaction Hash: {result.get('tx_hash')}")
            print(f"From:   {result.get('from')}")
            print(f"To:     {result.get('to')}")
            print(f"Amount: {result.get('amount')} {result.get('token')}")
        else:
            print("🛑 TRANSACTION BLOCKED BY AI GUARDIAN")
            print(f"Reason: {result.get('reason', 'Unknown Error')}")
            print(f"Risk Level: {result.get('risk_level', 'UNKNOWN')}")
            
        print("="*50 + "\n")

if __name__ == "__main__":
    main()
