import argparse
import sys
import logging
from config.settings import get_settings
from core.blockchain import BlockchainClient
from agents.allowance_monitor import AllowanceMonitorAgent
from agents.ai_analyzer import AIAnalyzer

logger = logging.getLogger(__name__)

def main():
    """
    Main Entry Point for the Security Monitor Framework
    """
    settings = get_settings()
    
    # CLI Argument Parsing
    parser = argparse.ArgumentParser(description="Blockchain Security Monitor")
    parser.add_argument("--owner", type=str, help="Wallet address to check", required=True)
    parser.add_argument("--spender", type=str, help="Spender contract address to check", required=True)
    parser.add_argument("--token", type=str, help="Token contract address (Optional, uses default from config)", default=settings.TARGET_TOKEN_ADDRESS)
    
    args = parser.parse_args()

    logger.info("Initializing Security Monitor Framework...")
    
    try:
        # 1. Initialize Blockchain Connection
        client = BlockchainClient()
        
        # 2. Initialize Agent
        monitor = AllowanceMonitorAgent(client, args.token)
        
        # 3. Execute Check
        logger.info(f"Checking allowance for Owner: {args.owner} -> Spender: {args.spender}")
        result = monitor.check_allowance(args.owner, args.spender)
        
        # 4. AI Risk Analysis (Optional)
        ai_analyzer = AIAnalyzer()
        ai_feedback = ai_analyzer.analyze_risk(result)
        
        # 5. Output Results
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

    except Exception as e:
        logger.critical(f"Critical System Failure: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
