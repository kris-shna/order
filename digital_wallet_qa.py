import unittest
from datetime import datetime, timedelta
from digital_wallet import DigitalWallet

class TestWalletSecurityQA(unittest.TestCase):

    def setUp(self):
        self.wallet = DigitalWallet()
        self.wallet.create_account("ACC001", "1234", daily_limit=500.0)
        self.wallet.create_account("ACC002", "5678", daily_limit=1000.0)
        self.wallet.deposit("ACC001", 1000.0)

    # 1. Normal transaction
    def test_01_normal_transaction(self):
        res = self.wallet.withdraw("ACC001", 100.0, "1234")
        self.assertTrue(res["success"])
        self.assertFalse(res["is_suspicious"])
        self.assertEqual(res["balance"], 900.0)

    # 2. Insufficient balance
    def test_02_insufficient_balance(self):
        res = self.wallet.withdraw("ACC001", 2000.0, "1234")
        self.assertFalse(res["success"])
        self.assertEqual(res["message"], "Insufficient balance.")

    # 3. Daily limit breach
    def test_03_daily_limit_exceeded(self):
        res = self.wallet.withdraw("ACC001", 600.0, "1234")
        self.assertFalse(res["success"])
        self.assertEqual(res["message"], "Exceeds daily transaction limit.")

    # 4. Multiple failed PINs & Fraud Flag
    def test_04_multiple_failed_pins(self):
        self.wallet.withdraw("ACC001", 50.0, "wrong")
        self.wallet.withdraw("ACC001", 50.0, "wrong")
        self.wallet.withdraw("ACC001", 50.0, "wrong")
        res = self.wallet.withdraw("ACC001", 50.0, "1234")
        self.assertTrue(res["success"])
        self.assertTrue(res["is_suspicious"])

    # 5. Suspicious Large Transaction
    def test_05_suspicious_large_transaction(self):
        self.wallet.deposit("ACC001", 10000.0)
        self.wallet.accounts["ACC001"].daily_limit = 15000.0
        res = self.wallet.withdraw("ACC001", 6000.0, "1234")
        self.assertTrue(res["success"])
        self.assertTrue(res["is_suspicious"])

    # 6. Duplicate/Self Transfer Prevention
    def test_06_self_transfer_prevention(self):
        res = self.wallet.transfer("ACC001", "ACC001", 50.0, "1234")
        self.assertFalse(res["success"])
        self.assertEqual(res["message"], "Cannot transfer to the same account.")

    # 7. Negative Amount Deposit
    def test_07_negative_amount_deposit(self):
        res = self.wallet.deposit("ACC001", -100.0)
        self.assertFalse(res["success"])

    # 8. High Frequency Fraud Detection (>5 txns in 10 mins)
    def test_08_high_frequency_fraud_detection(self):
        now = datetime.now()
        for i in range(5):
            self.wallet.deposit("ACC001", 10.0, current_time=now + timedelta(seconds=i))
        
        res = self.wallet.deposit("ACC001", 10.0, current_time=now + timedelta(seconds=20))
        self.assertTrue(res["success"])
        self.assertTrue(res["is_suspicious"])

    # 9. Successful Money Transfer
    def test_09_money_transfer(self):
        res = self.wallet.transfer("ACC001", "ACC002", 200.0, "1234")
        self.assertTrue(res["success"])
        self.assertEqual(self.wallet.accounts["ACC002"].balance, 200.0)

    # 10. Account Creation Duplicate Check
    def test_10_duplicate_account_creation(self):
        res = self.wallet.create_account("ACC001", "0000")
        self.assertFalse(res["success"])

    # 11. Negative Withdrawal Handling
    def test_11_negative_withdrawal(self):
        res = self.wallet.withdraw("ACC001", -50.0, "1234")
        self.assertFalse(res["success"])

    # 12. Non-existent Account Withdrawal
    def test_12_non_existent_account(self):
        res = self.wallet.withdraw("GHOST_ACC", 50.0, "1234")
        self.assertFalse(res["success"])

    # 13. Transfer to Non-existent Recipient
    def test_13_transfer_bad_recipient(self):
        res = self.wallet.transfer("ACC001", "GHOST_ACC", 50.0, "1234")
        self.assertFalse(res["success"])

    # 14. Zero Amount Deposit
    def test_14_zero_amount_deposit(self):
        res = self.wallet.deposit("ACC001", 0.0)
        self.assertFalse(res["success"])

    # 15. Transaction History Logging
    def test_15_transaction_history_logging(self):
        self.wallet.withdraw("ACC001", 50.0, "1234")
        acc = self.wallet.accounts["ACC001"]
        self.assertEqual(len(acc.history), 2)  # Initial deposit + withdrawal

    # 16. Daily Limit Reset on Next Day
    def test_16_daily_limit_reset(self):
        self.wallet.withdraw("ACC001", 400.0, "1234")
        future_time = datetime.now() + timedelta(days=1)
        res = self.wallet.withdraw("ACC001", 400.0, "1234", current_time=future_time)
        self.assertTrue(res["success"])

    # 17. PIN Failure Counter Reset on Success
    def test_17_pin_failure_reset_on_success(self):
        self.wallet.withdraw("ACC001", 10.0, "wrong")
        self.wallet.withdraw("ACC001", 10.0, "1234")
        self.assertEqual(self.wallet.accounts["ACC001"].failed_pin_attempts, 0)

    # 18. Transfer Insufficient Balance
    def test_18_transfer_insufficient_balance(self):
        res = self.wallet.transfer("ACC001", "ACC002", 5000.0, "1234")
        self.assertFalse(res["success"])

    # 19. Transfer Daily Limit Enforcement
    def test_19_transfer_daily_limit(self):
        res = self.wallet.transfer("ACC001", "ACC002", 600.0, "1234")
        self.assertFalse(res["success"])

    # 20. Rapid Concurrent Deposits Sequence
    def test_20_rapid_deposits_sequence(self):
        for _ in range(3):
            self.wallet.deposit("ACC001", 10.0)
        self.assertEqual(self.wallet.accounts["ACC001"].balance, 1030.0)

if __name__ == "__main__":
    unittest.main()