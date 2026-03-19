from datetime import datetime, date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, selectinload

from app.models.account import Account
from app.models.journal_entry import JournalEntry, LineItem
from app.models.enums import AccountType
from app.schemas.journal_entry import JournalEntryCreate, JournalEntryUpdate


class JournalService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_entry_number(self) -> str:
        result = self.db.execute(
            select(func.max(JournalEntry.entry_number)).where(
                JournalEntry.entry_number.like("JE-%")
            )
        )
        max_number = result.scalar()
        if max_number:
            num = int(max_number.split("-")[1]) + 1
        else:
            num = 1
        return f"JE-{num:05d}"

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        start_date: date | None = None,
        end_date: date | None = None,
        posted_only: bool | None = None,
    ) -> tuple[list[JournalEntry], int]:
        query = select(JournalEntry).options(
            selectinload(JournalEntry.line_items).selectinload(LineItem.account)
        )

        if start_date:
            query = query.where(JournalEntry.date >= start_date)
        if end_date:
            query = query.where(JournalEntry.date <= end_date)
        if posted_only is not None:
            if posted_only:
                query = query.where(JournalEntry.posted_at.isnot(None))
            else:
                query = query.where(JournalEntry.posted_at.is_(None))

        count_query = select(func.count(JournalEntry.id))
        if start_date:
            count_query = count_query.where(JournalEntry.date >= start_date)
        if end_date:
            count_query = count_query.where(JournalEntry.date <= end_date)
        if posted_only is not None:
            if posted_only:
                count_query = count_query.where(JournalEntry.posted_at.isnot(None))
            else:
                count_query = count_query.where(JournalEntry.posted_at.is_(None))

        total_result = self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(JournalEntry.date.desc(), JournalEntry.entry_number.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        return list(result.scalars().all()), total

    def get_by_id(self, entry_id: UUID) -> JournalEntry | None:
        result = self.db.execute(
            select(JournalEntry)
            .options(selectinload(JournalEntry.line_items).selectinload(LineItem.account))
            .where(JournalEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    def create(self, data: JournalEntryCreate) -> JournalEntry:
        entry = JournalEntry(
            entry_number=self._generate_entry_number(),
            date=data.entry_date,
            description=data.description,
            reference=data.reference,
        )
        self.db.add(entry)
        self.db.flush()

        for item_data in data.line_items:
            line_item = LineItem(
                journal_entry_id=entry.id,
                account_id=item_data.account_id,
                debit=item_data.debit,
                credit=item_data.credit,
                memo=item_data.memo,
            )
            self.db.add(line_item)

        self.db.commit()
        self.db.refresh(entry)
        return self.get_by_id(entry.id)

    def update(
        self, entry_id: UUID, data: JournalEntryUpdate
    ) -> JournalEntry | None:
        entry = self.get_by_id(entry_id)
        if not entry:
            return None

        if entry.is_posted:
            raise ValueError("Cannot modify a posted journal entry")

        if data.entry_date is not None:
            entry.date = data.entry_date
        if data.description is not None:
            entry.description = data.description
        if data.reference is not None:
            entry.reference = data.reference

        if data.line_items is not None:
            for item in entry.line_items:
                self.db.delete(item)

            for item_data in data.line_items:
                line_item = LineItem(
                    journal_entry_id=entry.id,
                    account_id=item_data.account_id,
                    debit=item_data.debit,
                    credit=item_data.credit,
                    memo=item_data.memo,
                )
                self.db.add(line_item)

        self.db.commit()
        return self.get_by_id(entry_id)

    def delete(self, entry_id: UUID) -> bool:
        entry = self.get_by_id(entry_id)
        if not entry:
            return False

        if entry.is_posted:
            raise ValueError("Cannot delete a posted journal entry")

        self.db.delete(entry)
        self.db.commit()
        return True

    def post(self, entry_id: UUID) -> JournalEntry | None:
        entry = self.get_by_id(entry_id)
        if not entry:
            return None

        if entry.is_posted:
            raise ValueError("Journal entry is already posted")

        total_debits = sum(item.debit for item in entry.line_items)
        total_credits = sum(item.credit for item in entry.line_items)

        if total_debits != total_credits:
            raise ValueError(
                f"Journal entry is not balanced. Debits: {total_debits}, Credits: {total_credits}"
            )

        entry.posted_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def unpost(self, entry_id: UUID) -> JournalEntry | None:
        entry = self.get_by_id(entry_id)
        if not entry:
            return None

        entry.posted_at = None
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_entry_details(self, entry_id: UUID) -> dict | None:
        entry = self.get_by_id(entry_id)
        if not entry:
            return None

        total_debits = sum(item.debit for item in entry.line_items)
        total_credits = sum(item.credit for item in entry.line_items)

        return {
            "id": entry.id,
            "entry_number": entry.entry_number,
            "date": entry.date,
            "description": entry.description,
            "reference": entry.reference,
            "created_at": entry.created_at,
            "posted_at": entry.posted_at,
            "is_posted": entry.is_posted,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "line_items": [
                {
                    "id": item.id,
                    "account_id": item.account_id,
                    "account_code": item.account.code,
                    "account_name": item.account.name,
                    "account_type": item.account.account_type,
                    "debit": item.debit,
                    "credit": item.credit,
                    "memo": item.memo,
                }
                for item in entry.line_items
            ],
        }
