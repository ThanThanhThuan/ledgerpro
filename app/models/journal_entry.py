import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.account import Account


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entry_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    line_items: Mapped[list["LineItem"]] = relationship(
        "LineItem", back_populates="journal_entry", cascade="all, delete-orphan"
    )

    @property
    def is_posted(self) -> bool:
        return self.posted_at is not None

    @property
    def total_debits(self) -> Decimal:
        return Decimal(str(sum(item.debit for item in self.line_items)))

    @property
    def total_credits(self) -> Decimal:
        return Decimal(str(sum(item.credit for item in self.line_items)))

    def __repr__(self):
        return f"<JournalEntry {self.entry_number} - {self.description}>"


class LineItem(Base):
    __tablename__ = "line_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False
    )
    debit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    credit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    memo: Mapped[str | None] = mapped_column(String(255), nullable=True)

    journal_entry: Mapped["JournalEntry"] = relationship(
        "JournalEntry", back_populates="line_items"
    )
    account: Mapped["Account"] = relationship(  # type: ignore
        "Account", back_populates="line_items"
    )

    def __repr__(self):
        return f"<LineItem {self.account_id} Dr:{self.debit} Cr:{self.credit}>"
