import datetime as dt
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, field_serializer

from app.models.enums import AccountType


class LineItemBase(BaseModel):
    account_id: UUID = Field(..., description="Account ID")
    debit: Decimal = Field(default=Decimal("0.00"), ge=0)
    credit: Decimal = Field(default=Decimal("0.00"), ge=0)
    memo: str | None = Field(None, max_length=255)

    @field_serializer('account_id')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    @field_serializer('debit', 'credit')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)

    @field_validator("debit", "credit")
    @classmethod
    def round_to_two_places(cls, v: Decimal) -> Decimal:
        return round(v, 2)

    @model_validator(mode="after")
    def check_debit_or_credit(self) -> "LineItemBase":
        if self.debit == 0 and self.credit == 0:
            raise ValueError("Either debit or credit must be greater than zero")
        if self.debit > 0 and self.credit > 0:
            raise ValueError("Both debit and credit cannot have values")
        return self


class LineItemCreate(LineItemBase):
    pass


class LineItemResponse(LineItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    journal_entry_id: UUID

    @field_serializer('id', 'journal_entry_id')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


class LineItemWithAccount(LineItemResponse):
    account_code: str
    account_name: str
    account_type: str


class JournalEntryBase(BaseModel):
    entry_date: dt.date = Field(..., description="Transaction date", alias="date")
    description: str = Field(..., max_length=255)
    reference: str | None = Field(None, max_length=50)

    model_config = ConfigDict(populate_by_name=True)


class JournalEntryCreate(JournalEntryBase):
    line_items: list[LineItemCreate] = Field(
        ..., min_length=2, description="At least two line items required"
    )

    @model_validator(mode="after")
    def check_balanced(self) -> "JournalEntryCreate":
        total_debits = sum(item.debit for item in self.line_items)
        total_credits = sum(item.credit for item in self.line_items)
        if total_debits != total_credits:
            raise ValueError(
                f"Journal entry must be balanced. Debits: {total_debits}, Credits: {total_credits}"
            )
        return self


class JournalEntryUpdate(BaseModel):
    entry_date: dt.date | None = None
    description: str | None = Field(None, max_length=255)
    reference: str | None = Field(None, max_length=50)
    line_items: list[LineItemCreate] | None = None

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def check_balanced(self) -> "JournalEntryUpdate":
        if self.line_items:
            total_debits = sum(item.debit for item in self.line_items)
            total_credits = sum(item.credit for item in self.line_items)
            if total_debits != total_credits:
                raise ValueError("Journal entry must be balanced")
        return self


class JournalEntryResponse(JournalEntryBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    entry_number: str
    created_at: dt.datetime
    posted_at: dt.datetime | None

    @field_serializer('id')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    @property
    def is_posted(self) -> bool:
        return self.posted_at is not None


class JournalEntryWithLineItems(JournalEntryResponse):
    line_items: list[LineItemWithAccount]
    total_debits: Decimal
    total_credits: Decimal

    @field_serializer('total_debits', 'total_credits')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)
