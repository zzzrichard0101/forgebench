from decimal import Decimal


class CreditLedger:
    def __init__(self, limits):
        self.limits = limits
        self.reservations = {}

    def reserve(self, account, amount, request_id):
        amount = Decimal(amount)
        used = sum((item[1] for item in self.reservations.values() if item[0] == account), Decimal("0"))
        if used + amount > self.limits[account]:
            return False
        self.reservations[request_id] = (account, amount, "pending")
        return True

    def commit(self, request_id):
        account, amount, _ = self.reservations[request_id]
        self.reservations[request_id] = (account, amount, "committed")

    def cancel(self, request_id):
        self.reservations.pop(request_id)
