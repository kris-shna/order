from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Transaction:
    transaction_id: str
    type: str  # DEPOSIT, WITHDRAWAL, TRANSFER_OUT, TRANSFER_IN
    amount: float
    timestamp: datetime
    is_suspicious: bool = False
    reason: Optional[str] = None

class Account:
    def __init__(self, account_id: str, pin: str, daily_limit: float = 1000.0):
        self.account_id = account_id
        self.pin = pin
        self.balance = 0.0
        self.daily_limit = daily_limit
        self.daily_spent = 0.0
        self.failed_pin_attempts = 0
        self.history: List[Transaction] = []
        self.recent_timestamps: List[datetime] = []
        self._last_reset_date = datetime.now().date()

    def _check_daily_reset(self, current_time: datetime):
        if current_time.date() > self._last_reset_date:
            self.daily_spent = 0.0
            self._last_reset_date = current_time.date()

class DigitalWallet:
    LARGE_TRANSACTION_THRESHOLD = 5000.0

    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self._tx_counter = 1000

    def create_account(self, account_id: str, pin: str, daily_limit: float = 1000.0) -> dict:
        if not account_id or not pin:
            return {"success": False, "message": "Invalid account ID or PIN."}
        if account_id in self.accounts:
            return {"success": False, "message": "Account already exists."}
        self.accounts[account_id] = Account(account_id, pin, daily_limit)
        return {"success": True, "message": "Account created successfully."}

    def verify_pin(self, account_id: str, pin: str) -> bool:
        account = self.accounts.get(account_id)
        if not account:
            return False
        if account.pin != pin:
            account.failed_pin_attempts += 1
            return False
        account.failed_pin_attempts = 0
        return True

    def _evaluate_fraud(self, account: Account, amount: float, current_time: datetime) -> tuple:
        is_suspicious = False
        reasons = []

        # 1. Multiple failed PIN attempts (>= 3)
        if account.failed_pin_attempts >= 3:
            is_suspicious = True
            reasons.append("Multiple failed PIN attempts")

        # 2. Large transaction check
        if amount >= self.LARGE_TRANSACTION_THRESHOLD:
            is_suspicious = True
            reasons.append("Large transaction amount")

        # 3. High frequency velocity (>5 transactions in 10 minutes)
        cutoff = current_time - timedelta(minutes=10)
        account.recent_timestamps = [t for t in account.recent_timestamps if t > cutoff]
        if len(account.recent_timestamps) >= 5:
            is_suspicious = True
            reasons.append("High transaction frequency (>5 txns in 10 mins)")

        return is_suspicious, ", ".join(reasons) if reasons else ""

    def deposit(self, account_id: str, amount: float, current_time: Optional[datetime] = None) -> dict:
        if amount <= 0:
            return {"success": False, "message": "Amount must be greater than zero."}
        account = self.accounts.get(account_id)
        if not account:
            return {"success": False, "message": "Account not found."}

        current_time = current_time or datetime.now()
        account._check_daily_reset(current_time)

        is_suspicious, reason = self._evaluate_fraud(account, amount, current_time)

        self._tx_counter += 1
        tx_id = f"TX{self._tx_counter}"
        tx = Transaction(tx_id, "DEPOSIT", amount, current_time, is_suspicious, reason)

        account.balance += amount
        account.history.append(tx)
        account.recent_timestamps.append(current_time)

        return {"success": True, "transaction_id": tx_id, "balance": account.balance, "is_suspicious": is_suspicious}

    def withdraw(self, account_id: str, amount: float, pin: str, current_time: Optional[datetime] = None) -> dict:
        if amount <= 0:
            return {"success": False, "message": "Amount must be greater than zero."}
        account = self.accounts.get(account_id)
        if not account:
            return {"success": False, "message": "Account not found."}

        current_time = current_time or datetime.now()
        account._check_daily_reset(current_time)

        if not self.verify_pin(account_id, pin):
            return {"success": False, "message": "Incorrect PIN."}

        if account.balance < amount:
            return {"success": False, "message": "Insufficient balance."}

        if account.daily_spent + amount > account.daily_limit:
            return {"success": False, "message": "Exceeds daily transaction limit."}

        is_suspicious, reason = self._evaluate_fraud(account, amount, current_time)

        self._tx_counter += 1
        tx_id = f"TX{self._tx_counter}"
        tx = Transaction(tx_id, "WITHDRAWAL", amount, current_time, is_suspicious, reason)

        account.balance -= amount
        account.daily_spent += amount
        account.history.append(tx)
        account.recent_timestamps.append(current_time)

        return {"success": True, "transaction_id": tx_id, "balance": account.balance, "is_suspicious": is_suspicious}

    def transfer(self, sender_id: str, recipient_id: str, amount: float, pin: str, current_time: Optional[datetime] = None) -> dict:
        if amount <= 0:
            return {"success": False, "message": "Amount must be greater than zero."}
        sender = self.accounts.get(sender_id)
        recipient = self.accounts.get(recipient_id)
        if not sender or not recipient:
            return {"success": False, "message": "Sender or recipient account not found."}
        if sender_id == recipient_id:
            return {"success": False, "message": "Cannot transfer to the same account."}

        current_time = current_time or datetime.now()
        sender._check_daily_reset(current_time)

        if not self.verify_pin(sender_id, pin):
            return {"success": False, "message": "Incorrect PIN."}

        if sender.balance < amount:
            return {"success": False, "message": "Insufficient balance."}

        if sender.daily_spent + amount > sender.daily_limit:
            return {"success": False, "message": "Exceeds daily transaction limit."}

        is_suspicious, reason = self._evaluate_fraud(sender, amount, current_time)

        self._tx_counter += 1
        tx_id = f"TX{self._tx_counter}"
        tx_send = Transaction(tx_id, "TRANSFER_OUT", amount, current_time, is_suspicious, reason)
        tx_recv = Transaction(tx_id, "TRANSFER_IN", amount, current_time, False, "")

        sender.balance -= amount
        sender.daily_spent += amount
        sender.history.append(tx_send)
        sender.recent_timestamps.append(current_time)

        recipient.balance += amount
        recipient.history.append(tx_recv)

        return {"success": True, "transaction_id": tx_id, "sender_balance": sender.balance, "is_suspicious": is_suspicious}