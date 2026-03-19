import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import AccountType
from app.database import Base

if TYPE_CHECKING:
    from app.models.journal_entry import LineItem, JournalEntry


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(
        SQLEnum(AccountType, name="account_type", values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    parent: Mapped["Account | None"] = relationship(
        "Account", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Account"]] = relationship(
        "Account", back_populates="parent"
    )
    line_items: Mapped[list["LineItem"]] = relationship(  # type: ignore
        "LineItem", back_populates="account"
    )

    def __repr__(self):
        return f"<Account {self.code} - {self.name}>"
