import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.allowance_monitor import AllowanceMonitorAgent
from core.blockchain import BlockchainClient

class TestAllowanceLogic(unittest.TestCase):

    def setUp(self):
        # Mock Blockchain Client
        self.mock_client = MagicMock(spec=BlockchainClient)
        
        # Mock Contract
        self.mock_contract = MagicMock()
        self.mock_client.get_contract.return_value = self.mock_contract
        
        # Mock Symbol and Decimals calls (called in __init__)
        # Sequence: symbol(), decimals()
        # call_contract_function is used for these
        self.mock_client.call_contract_function.side_effect = self._mock_contract_calls
        
        self.agent = AllowanceMonitorAgent(self.mock_client, "0xTokenAddress")
        
        # Reset side_effect for actual tests, we will set it per test case
        self.mock_client.call_contract_function.side_effect = None

    def _mock_contract_calls(self, func, *args, **kwargs):
        # Helper to handle __init__ calls
        if func == self.mock_contract.functions.symbol:
            return "TEST"
        if func == self.mock_contract.functions.decimals:
            return 18
        return None

    def test_normal_allowance(self):
        """Scenario 1: Normal Allowance (Small Amount)"""
        print("\n--- Testing Normal Allowance ---")
        owner = "0x1234567890123456789012345678901234567890"
        spender = "0x0987654321098765432109876543210987654321"
        
        # Mock Returns: Allowance=500, Balance=1000 (Decimals=18)
        allowance_val = 500 * (10**18)
        balance_val = 1000 * (10**18)
        
        self.mock_client.call_contract_function.side_effect = [
            allowance_val, # allowance
            balance_val    # balanceOf
        ]

        result = self.agent.check_allowance(owner, spender)
        
        print(f"Allowance: {result['allowance_formatted']}")
        print(f"Balance: {result['owner_balance']}")
        print(f"Risk: {result['risk_level']}")

        self.assertEqual(result['risk_level'], "LOW")
        self.assertLess(result['allowance_raw'], result['owner_balance'] * (10**18))

    def test_zero_allowance(self):
        """Scenario 2: Zero Allowance (Revoked)"""
        print("\n--- Testing Zero Allowance (Revoked) ---")
        owner = "0x1234567890123456789012345678901234567890"
        spender = "0x0987654321098765432109876543210987654321"
        
        # Mock Returns: Allowance=0, Balance=1000
        allowance_val = 0
        balance_val = 1000 * (10**18)
        
        self.mock_client.call_contract_function.side_effect = [
            allowance_val,
            balance_val
        ]

        result = self.agent.check_allowance(owner, spender)
        
        print(f"Allowance: {result['allowance_formatted']}")
        print(f"Risk: {result['risk_level']}")

        self.assertEqual(result['risk_level'], "LOW")
        self.assertEqual(result['allowance_raw'], 0)

    def test_unlimited_allowance(self):
        """Scenario 3: Unlimited/High Risk (Allowance > Balance)"""
        print("\n--- Testing Unlimited/High Risk ---")
        owner = "0x1234567890123456789012345678901234567890"
        spender = "0x0987654321098765432109876543210987654321"
        
        # Mock Returns: Allowance=MaxUint, Balance=1000
        allowance_val = 2**256 - 1
        balance_val = 1000 * (10**18)
        
        self.mock_client.call_contract_function.side_effect = [
            allowance_val,
            balance_val
        ]

        result = self.agent.check_allowance(owner, spender)
        
        print(f"Allowance: {result['allowance_formatted']}")
        print(f"Balance: {result['owner_balance']}")
        print(f"Risk: {result['risk_level']}")

        self.assertIn("HIGH", result['risk_level'])
        self.assertTrue(result['allowance_raw'] > balance_val)

if __name__ == '__main__':
    unittest.main()
