from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.enums import AccountType


class AccountBase(BaseModel):
    code: str = Field(..., max_length=20, description="Unique account code")
    name: str = Field(..., max_length=100, description="Account name")
    account_type: str = Field(..., description="Type of account")
    parent_id: UUID | None = Field(None, description="Parent account ID for sub-accounts")

    @field_serializer('parent_id')
    def serialize_uuid(self, value: UUID | None) -> str | None:
        return str(value) if value else None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    code: str | None = Field(None, max_length=20)
    name: str | None = Field(None, max_length=100)
    account_type: str | None = None
    parent_id: UUID | None = None
    is_active: bool | None = None


class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer('id')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


class AccountWithBalance(AccountResponse):
    balance: Decimal = Decimal("0.00")
    debit_total: Decimal = Decimal("0.00")
    credit_total: Decimal = Decimal("0.00")

    @field_serializer('balance', 'debit_total', 'credit_total')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)
