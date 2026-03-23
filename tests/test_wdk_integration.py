import unittest
from unittest.mock import MagicMock, patch

from security_monitor.core.wdk_client import TransactionError, WalletAccount, WalletManager


class TestWDKIntegration(unittest.TestCase):
    def setUp(self):
        # Mock Web3
        self.mock_w3 = MagicMock()
        self.mock_w3.is_connected.return_value = True
        self.mock_w3.eth.chain_id = 11155111 # Sepolia
        self.mock_w3.eth.get_transaction_count.return_value = 5
        self.mock_w3.eth.gas_price = 20000000000
        self.mock_w3.eth.get_block.return_value = {"baseFeePerGas": 1000000000}
        self.mock_w3.eth.max_priority_fee = 2000000000
        self.mock_w3.to_checksum_address = lambda x: x
        receipt = MagicMock()
        receipt.status = 1
        receipt.blockNumber = 88
        self.mock_w3.eth.wait_for_transaction_receipt.return_value = receipt
        self.mock_w3.eth.account.sign_transaction.return_value.raw_transaction = b"raw_tx"
        self.mock_w3.eth.account.sign_transaction.return_value.hash.hex.return_value = "0xTxHash"
        self.mock_w3.eth.send_raw_transaction.return_value.hex.return_value = "0xTxHash"

        # Mock Account
        self.mock_account = MagicMock()
        self.mock_account.address = "0xTestAddress"
        self.mock_account.key.hex.return_value = "0xPrivateKey"

    @patch('security_monitor.core.wdk_client.Web3')
    def test_wallet_creation_and_signing(self, mock_web3_cls):
        # Setup Mocks
        mock_web3_cls.return_value = self.mock_w3

        with patch('eth_account.Account.create', return_value=self.mock_account):
             # Test Wallet Manager
            manager = WalletManager()
            wallet = manager.create_wallet()

            self.assertEqual(wallet.address, "0xTestAddress")

        # Test Sign Message
        with patch('eth_account.Account.sign_message') as mock_sign:
            mock_sign.return_value.signature.hex.return_value = "0xSignature"
            # We need to set the private key manually as mock wallet might not have it set correctly if create() logic is complex
            wallet._private_key = "0xPrivateKey"
            signature = wallet.sign_message("Hello WDK")
            self.assertEqual(signature, "0xSignature")

    def test_send_transaction(self):
        # Create Wallet with mocked w3
        wallet = WalletAccount("0xSender", "0xPrivateKey", self.mock_w3)

        # Mock Nonce Manager Sync
        wallet.nonce_manager._local_nonce = 5

        # Execute Transfer
        # Since send_transaction is async wrapper or uses run_until_complete, wait,
        # actually send_transaction calls asyncio.run(self.nonce_manager.get_next_nonce()) inside.
        # So we need to ensure asyncio run works.

        # Mock the contract call for ERC20 check
        contract_mock = MagicMock()
        contract_mock.functions.transfer.return_value.build_transaction.return_value = {
            'to': '0xReceiver',
            'value': 0,
            'gas': 200000,
            'gasPrice': 20000000000,
            'nonce': 5,
            'chainId': 11155111
        }
        self.mock_w3.eth.contract.return_value = contract_mock

        result = wallet.send_transaction("0xReceiver", 10.0, "USDT")

        self.assertEqual(result['tx_hash'], "0xTxHash")
        self.assertEqual(result['nonce'], 5)
        self.assertEqual(result['block_number'], 88)
        self.assertEqual(result['status'], "success")

    def test_send_transaction_reverted_raises(self):
        wallet = WalletAccount("0xSender", "0xPrivateKey", self.mock_w3)
        wallet.nonce_manager._local_nonce = 5
        contract_mock = MagicMock()
        contract_mock.functions.transfer.return_value.build_transaction.return_value = {
            'to': '0xReceiver',
            'value': 0,
            'gas': 200000,
            'gasPrice': 20000000000,
            'nonce': 5,
            'chainId': 11155111
        }
        self.mock_w3.eth.contract.return_value = contract_mock
        reverted_receipt = MagicMock()
        reverted_receipt.status = 0
        reverted_receipt.blockNumber = 89
        self.mock_w3.eth.wait_for_transaction_receipt.return_value = reverted_receipt

        with self.assertRaises(TransactionError):
            wallet.send_transaction("0xReceiver", 1.0, "USDT")

    def test_tether_bridge_wallet_account_primitives(self):
        bridge = MagicMock()
        bridge.get_balance.return_value = 1234567
        bridge.sign.return_value = "0xBridgeSig"
        bridge.transfer.return_value = {"txHash": "0xBridgeTx", "blockNumber": 22}
        wallet = WalletAccount("0xSender", None, self.mock_w3, tether_bridge=bridge)

        balance = wallet.get_balance("USDT")
        signature = wallet.sign_message("hello")
        tx_result = wallet.send_transaction("0xReceiver", 1.0, "USDT")

        self.assertAlmostEqual(balance, 1.234567, places=6)
        self.assertEqual(signature, "0xBridgeSig")
        self.assertEqual(tx_result["tx_hash"], "0xBridgeTx")
        self.assertEqual(tx_result["block_number"], 22)
        self.assertEqual(tx_result["status"], "success")
        bridge.get_balance.assert_called_once()
        bridge.sign.assert_called_once_with("hello")
        bridge.transfer.assert_called_once()

    @patch("security_monitor.core.wdk_client._TetherWdkBridge")
    @patch("security_monitor.core.wdk_client.settings")
    def test_wallet_manager_uses_tether_bridge_when_enabled(self, mock_settings, mock_bridge_cls):
        mock_settings.DEFAULT_CHAIN_KEY = "sepolia"
        mock_settings.get_rpc_url.return_value = "https://sepolia.example"
        mock_settings.get_chain_id.return_value = 11155111
        mock_settings.WDK_USE_TETHER_WDK = True
        mock_settings.WDK_SEED_PHRASE = "test test test test test test test test test test test junk"
        mock_settings.WDK_ACCOUNT_INDEX = 0
        mock_settings.WDK_WAIT_FOR_RECEIPT = True
        mock_settings.WDK_TX_TIMEOUT_SECONDS = 120
        bridge = MagicMock()
        bridge.get_address.return_value = "0xBridgeAddress"
        mock_bridge_cls.return_value = bridge

        manager = WalletManager(chain_key="sepolia")
        wallet = manager.create_wallet()

        self.assertEqual(wallet.address, "0xBridgeAddress")
        self.assertIsNotNone(wallet._tether_bridge)
        mock_bridge_cls.assert_called_once()

    @patch('security_monitor.core.wdk_client.settings')
    def test_multi_asset_transactions(self, mock_settings):
        # Setup Settings
        mock_settings.ASSET_CONTRACTS = {
            "USDT": "0xUSDTAddress",
            "XAUT": "0xXAUTAddress",
            "USAT": "0xUSATAddress"
        }
        mock_settings.CHAIN_ID = 11155111

        wallet = WalletAccount("0xSender", "0xPrivateKey", self.mock_w3)
        wallet.nonce_manager._local_nonce = 10

        # Mock Contract
        contract_mock = MagicMock()
        # Mock build_transaction return
        contract_mock.functions.transfer.return_value.build_transaction.return_value = {
            'to': '0xReceiver', 'value': 0, 'gas': 200000, 'gasPrice': 20000000000, 'nonce': 10, 'chainId': 11155111
        }
        self.mock_w3.eth.contract.return_value = contract_mock

        # Test XAUT
        wallet.send_transaction("0xReceiver", 1.0, "XAUT")

        # Verify contract instantiation used XAUT address
        # Note: ANY is not imported, so use unittest.mock.ANY
        self.mock_w3.eth.contract.assert_called_with(address="0xXAUTAddress", abi=unittest.mock.ANY)

        # Test USAT
        wallet.send_transaction("0xReceiver", 5.0, "USAT")
        self.mock_w3.eth.contract.assert_called_with(address="0xUSATAddress", abi=unittest.mock.ANY)

if __name__ == '__main__':
    unittest.main()
