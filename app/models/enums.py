from enum import Enum


class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"

    @property
    def normal_balance(self) -> str:
        return "debit" if self in (AccountType.ASSET, AccountType.EXPENSE) else "credit"

    @property
    def is_debit_positive(self) -> bool:
        return self in (AccountType.ASSET, AccountType.EXPENSE)

    @property
    def category(self) -> str:
        if self in (AccountType.ASSET,):
            return "balance_sheet"
        elif self in (AccountType.LIABILITY, AccountType.EQUITY):
            return "balance_sheet"
        else:
            return "income_statement"
