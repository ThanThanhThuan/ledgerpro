from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models.enums import AccountType


class AccountBalance(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    account_type: str
    debit_balance: Decimal = Decimal("0.00")
    credit_balance: Decimal = Decimal("0.00")
    balance: Decimal = Decimal("0.00")

    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        return str(value)

    @field_serializer('debit_balance', 'credit_balance', 'balance')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)


class TrialBalanceResponse(BaseModel):
    as_of_date: date
    accounts: list[AccountBalance]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool

    @field_serializer('total_debits', 'total_credits')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)


class BalanceSheetSection(BaseModel):
    name: str
    accounts: list[AccountBalance]
    total: Decimal

    @field_serializer('total')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)


class BalanceSheetResponse(BaseModel):
    as_of_date: date
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection
    total_liabilities_and_equity: Decimal
    is_balanced: bool

    @field_serializer('total_liabilities_and_equity')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)


class IncomeStatementResponse(BaseModel):
    start_date: date
    end_date: date
    revenue: BalanceSheetSection
    expenses: BalanceSheetSection
    gross_profit: Decimal
    net_income: Decimal

    @field_serializer('gross_profit', 'net_income')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)


class LedgerEntry(BaseModel):
    date: date
    entry_number: str
    description: str
    debit: Decimal
    credit: Decimal
    balance: Decimal
    entry_id: UUID

    @field_serializer('debit', 'credit', 'balance')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)

    @field_serializer('entry_id')
    def serialize_id(self, value: UUID) -> str:
        return str(value)


class AccountLedgerResponse(BaseModel):
    account_id: UUID
    account_code: str
    account_name: str
    account_type: str
    start_date: date | None
    end_date: date | None
    opening_balance: Decimal
    entries: list[LedgerEntry]
    closing_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal

    @field_serializer('account_id')
    def serialize_id(self, value: UUID) -> str:
        return str(value)

    @field_serializer('opening_balance', 'closing_balance', 'total_debits', 'total_credits')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)
