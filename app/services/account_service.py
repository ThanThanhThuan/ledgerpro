from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.models.account import Account
from app.models.enums import AccountType
from app.models.journal_entry import LineItem
from app.schemas.account import AccountCreate, AccountUpdate


class AccountService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, include_inactive: bool = False) -> list[Account]:
        query = select(Account).order_by(Account.code)
        if not include_inactive:
            query = query.where(Account.is_active == True)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_id(self, account_id: UUID) -> Account | None:
        result = self.db.execute(
            select(Account).where(Account.id == account_id)
        )
        return result.scalar_one_or_none()

    def get_by_code(self, code: str) -> Account | None:
        result = self.db.execute(
            select(Account).where(Account.code == code)
        )
        return result.scalar_one_or_none()

    def create(self, data: AccountCreate) -> Account:
        account = Account(
            code=data.code,
            name=data.name,
            account_type=data.account_type,
            parent_id=data.parent_id,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def update(self, account_id: UUID, data: AccountUpdate) -> Account | None:
        account = self.get_by_id(account_id)
        if not account:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)

        account.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(account)
        return account

    def delete(self, account_id: UUID) -> bool:
        account = self.get_by_id(account_id)
        if not account:
            return False

        account.is_active = False
        account.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def get_account_balance(
        self, account_id: UUID, as_of_date: datetime | None = None
    ) -> dict:
        account = self.get_by_id(account_id)
        if not account:
            return {"balance": Decimal("0.00"), "debit_total": Decimal("0.00"), "credit_total": Decimal("0.00")}

        result = self.db.execute(
            select(
                func.coalesce(func.sum(LineItem.debit), Decimal("0.00")).label("debit_total"),
                func.coalesce(func.sum(LineItem.credit), Decimal("0.00")).label("credit_total"),
            ).where(LineItem.account_id == account_id)
        )
        row = result.one()

        debit_total = Decimal(str(row.debit_total))
        credit_total = Decimal(str(row.credit_total))

        if account.account_type.is_debit_positive:
            balance = debit_total - credit_total
        else:
            balance = credit_total - debit_total

        return {
            "balance": balance,
            "debit_total": debit_total,
            "credit_total": credit_total,
        }

    def get_with_balance(self, account_id: UUID) -> dict | None:
        account = self.get_by_id(account_id)
        if not account:
            return None

        balances = self.get_account_balance(account_id)
        return {
            "id": account.id,
            "code": account.code,
            "name": account.name,
            "account_type": account.account_type,
            "parent_id": account.parent_id,
            "is_active": account.is_active,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
            **balances,
        }

    def get_accounts_tree(self) -> list[dict]:
        accounts = self.get_all(include_inactive=True)

        root_accounts = [a for a in accounts if a.parent_id is None]
        children_map = {}

        for acc in accounts:
            if acc.parent_id:
                if acc.parent_id not in children_map:
                    children_map[acc.parent_id] = []
                children_map[acc.parent_id].append(acc)

        def build_tree(account: Account) -> dict:
            balances = self.get_account_balance(account.id)
            return {
                "id": str(account.id),
                "code": account.code,
                "name": account.name,
                "account_type": account.account_type.value,
                "is_active": account.is_active,
                "balance": str(balances["balance"]),
                "children": [build_tree(child) for child in children_map.get(account.id, [])],
            }

        return [build_tree(acc) for acc in root_accounts]
