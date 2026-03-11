import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.allowance_monitor import AllowanceMonitorAgent
from agents.guardian_agent import GuardianAgent
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

class TestGuardianPolicy(unittest.TestCase):
    def setUp(self):
        self.wallet = MagicMock()
        self.wallet.address = "0x1111111111111111111111111111111111111111"
        self.wallet.send_transaction.return_value = {
            "status": "success",
            "tx_hash": "0x" + "b" * 64,
            "from_address": self.wallet.address,
            "to_address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "amount": "10",
            "token": "USDT",
            "block_number": 123,
            "nonce": 1
        }
        self.monitor = MagicMock()
        self.monitor.client.w3.is_address.return_value = True

    @patch("agents.guardian_agent.get_settings")
    def test_block_unsupported_asset(self, mock_settings):
        mock_settings.return_value = SimpleNamespace(
            GUARDIAN_MAX_TRANSFER_AMOUNT=1000,
            GUARDIAN_SUPPORTED_ASSETS="USDT,USAT,XAUT"
        )
        guardian = GuardianAgent(self.wallet, self.monitor, None)
        result = guardian.run_transfer_task(
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            10,
            "BTC"
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("Unsupported asset", result["reason"])

    @patch("agents.guardian_agent.get_settings")
    def test_block_exceed_limit(self, mock_settings):
        mock_settings.return_value = SimpleNamespace(
            GUARDIAN_MAX_TRANSFER_AMOUNT=100,
            GUARDIAN_SUPPORTED_ASSETS="USDT,USAT,XAUT"
        )
        guardian = GuardianAgent(self.wallet, self.monitor, None)
        result = guardian.run_transfer_task(
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            101,
            "USDT"
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("policy limit", result["reason"])

    @patch("agents.guardian_agent.get_settings")
    def test_block_when_ai_service_unavailable(self, mock_settings):
        mock_settings.return_value = SimpleNamespace(
            GUARDIAN_MAX_TRANSFER_AMOUNT=1000,
            GUARDIAN_SUPPORTED_ASSETS="USDT,USAT,XAUT"
        )
        mock_ai = MagicMock()
        mock_ai.enabled = True
        mock_ai.analyze_transfer_target.return_value = {"safe": False, "reason": "AI service unavailable (Fail-Safe Block)"}
        guardian = GuardianAgent(self.wallet, self.monitor, mock_ai)
        result = guardian.run_transfer_task(
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            10,
            "USDT"
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("Fail-Safe", result["reason"])

    @patch("agents.guardian_agent.get_settings")
    def test_allow_valid_transfer(self, mock_settings):
        mock_settings.return_value = SimpleNamespace(
            GUARDIAN_MAX_TRANSFER_AMOUNT=1000,
            GUARDIAN_SUPPORTED_ASSETS="USDT,USAT,XAUT"
        )
        mock_ai = MagicMock()
        mock_ai.enabled = True
        mock_ai.analyze_transfer_target.return_value = {"safe": True, "reason": "LOW"}
        guardian = GuardianAgent(self.wallet, self.monitor, mock_ai)
        result = guardian.run_transfer_task(
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            10,
            "USAT"
        )
        self.assertEqual(result["status"], "success")
        self.wallet.send_transaction.assert_called_once()


if __name__ == '__main__':
    unittest.main()
