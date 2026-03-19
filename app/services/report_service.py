from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.journal_entry import JournalEntry, LineItem
from app.models.enums import AccountType
from app.schemas.reports import (
    AccountBalance,
    TrialBalanceResponse,
    BalanceSheetSection,
    BalanceSheetResponse,
    IncomeStatementResponse,
    LedgerEntry,
    AccountLedgerResponse,
)


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def get_trial_balance(self, as_of_date: date) -> TrialBalanceResponse:
        accounts = self.db.execute(
            select(Account)
            .where(Account.is_active == True)
            .order_by(Account.code)
        )
        accounts = list(accounts.scalars().all())

        account_balances = []
        total_debits = Decimal("0.00")
        total_credits = Decimal("0.00")

        for account in accounts:
            result = self.db.execute(
                select(
                    func.coalesce(func.sum(LineItem.debit), Decimal("0.00")).label("debit_total"),
                    func.coalesce(func.sum(LineItem.credit), Decimal("0.00")).label("credit_total"),
                )
                .join(JournalEntry)
                .where(
                    LineItem.account_id == account.id,
                    JournalEntry.date <= as_of_date,
                    JournalEntry.posted_at.isnot(None),
                )
            )
            row = result.one_or_none()
            if row:
                debit_total = Decimal(str(row.debit_total))
                credit_total = Decimal(str(row.credit_total))
            else:
                debit_total = Decimal("0.00")
                credit_total = Decimal("0.00")

            if account.account_type.is_debit_positive:
                debit_balance = debit_total - credit_total
                credit_balance = Decimal("0.00")
                if debit_balance < 0:
                    credit_balance = -debit_balance
                    debit_balance = Decimal("0.00")
            else:
                credit_balance = credit_total - debit_total
                debit_balance = Decimal("0.00")
                if credit_balance < 0:
                    debit_balance = -credit_balance
                    credit_balance = Decimal("0.00")

            if debit_balance != Decimal("0.00") or credit_balance != Decimal("0.00"):
                account_balances.append(
                    AccountBalance(
                        id=account.id,
                        code=account.code,
                        name=account.name,
                        account_type=account.account_type,
                        debit_balance=debit_balance,
                        credit_balance=credit_balance,
                        balance=debit_balance - credit_balance,
                    )
                )
                total_debits += debit_balance
                total_credits += credit_balance

        return TrialBalanceResponse(
            as_of_date=as_of_date,
            accounts=account_balances,
            total_debits=total_debits,
            total_credits=total_credits,
            is_balanced=total_debits == total_credits,
        )

    def get_balance_sheet(self, as_of_date: date) -> BalanceSheetResponse:
        accounts = self.db.execute(
            select(Account).where(Account.is_active == True).order_by(Account.code)
        )
        accounts = list(accounts.scalars().all())

        def get_account_balance(account: Account) -> Decimal:
            result = self.db.execute(
                select(
                    func.coalesce(func.sum(LineItem.debit), Decimal("0.00")).label("debit_total"),
                    func.coalesce(func.sum(LineItem.credit), Decimal("0.00")).label("credit_total"),
                )
                .join(JournalEntry)
                .where(
                    LineItem.account_id == account.id,
                    JournalEntry.date <= as_of_date,
                    JournalEntry.posted_at.isnot(None),
                )
            )
            row = result.one_or_none()
            if row:
                debit_total = Decimal(str(row.debit_total))
                credit_total = Decimal(str(row.credit_total))
            else:
                return Decimal("0.00")

            if account.account_type.is_debit_positive:
                return debit_total - credit_total
            else:
                return credit_total - debit_total

        asset_accounts = []
        liability_accounts = []
        equity_accounts = []

        for account in accounts:
            balance = get_account_balance(account)
            if balance != Decimal("0.00"):
                ab = AccountBalance(
                    id=account.id,
                    code=account.code,
                    name=account.name,
                    account_type=account.account_type,
                    balance=balance,
                )
                if account.account_type == AccountType.ASSET:
                    asset_accounts.append(ab)
                elif account.account_type == AccountType.LIABILITY:
                    liability_accounts.append(ab)
                elif account.account_type == AccountType.EQUITY:
                    equity_accounts.append(ab)

        total_assets = sum(acc.balance for acc in asset_accounts)
        total_liabilities = sum(acc.balance for acc in liability_accounts)
        total_equity = sum(acc.balance for acc in equity_accounts)

        net_income_result = self.get_net_income(
            date(1900, 1, 1), as_of_date
        )
        if net_income_result != Decimal("0.00"):
            equity_accounts.append(
                AccountBalance(
                    id=UUID(int=0),
                    code="NET_INCOME",
                    name="Net Income (Current Period)",
                    account_type=AccountType.EQUITY,
                    balance=net_income_result,
                )
            )
            total_equity += net_income_result

        return BalanceSheetResponse(
            as_of_date=as_of_date,
            assets=BalanceSheetSection(
                name="Assets", accounts=asset_accounts, total=Decimal(str(total_assets))
            ),
            liabilities=BalanceSheetSection(
                name="Liabilities", accounts=liability_accounts, total=Decimal(str(total_liabilities))
            ),
            equity=BalanceSheetSection(
                name="Equity", accounts=equity_accounts, total=Decimal(str(total_equity))
            ),
            total_liabilities_and_equity=Decimal(str(total_liabilities)) + Decimal(str(total_equity)),
            is_balanced=Decimal(str(total_assets)) == (Decimal(str(total_liabilities)) + Decimal(str(total_equity))),
        )

    def get_net_income(self, start_date: date, end_date: date) -> Decimal:
        revenue_accounts = self.db.execute(
            select(Account).where(
                Account.is_active == True,
                Account.account_type == AccountType.REVENUE,
            )
        )
        revenue_accounts = list(revenue_accounts.scalars().all())

        expense_accounts = self.db.execute(
            select(Account).where(
                Account.is_active == True,
                Account.account_type == AccountType.EXPENSE,
            )
        )
        expense_accounts = list(expense_accounts.scalars().all())

        total_revenue = Decimal("0.00")
        for account in revenue_accounts:
            result = self.db.execute(
                select(
                    func.coalesce(func.sum(LineItem.credit), Decimal("0.00")).label("credit_total"),
                    func.coalesce(func.sum(LineItem.debit), Decimal("0.00")).label("debit_total"),
                )
                .join(JournalEntry)
                .where(
                    LineItem.account_id == account.id,
                    JournalEntry.date >= start_date,
                    JournalEntry.date <= end_date,
                    JournalEntry.posted_at.isnot(None),
                )
            )
            row = result.one_or_none()
            if row:
                total_revenue += Decimal(str(row.credit_total)) - Decimal(str(row.debit_total))

        total_expenses = Decimal("0.00")
        for account in expense_accounts:
            result = self.db.execute(
                select(
                    func.coalesce(func.sum(LineItem.debit), Decimal("0.00")).label("debit_total"),
                    func.coalesce(func.sum(LineItem.credit), Decimal("0.00")).label("credit_total"),
                )
                .join(JournalEntry)
                .where(
                    LineItem.account_id == account.id,
                    JournalEntry.date >= start_date,
                    JournalEntry.date <= end_date,
                    JournalEntry.posted_at.isnot(None),
                )
            )
            row = result.one_or_none()
            if row:
                total_expenses += Decimal(str(row.debit_total)) - Decimal(str(row.credit_total))

        return total_revenue - total_expenses

    def get_income_statement(
        self, start_date: date, end_date: date
    ) -> IncomeStatementResponse:
        accounts = self.db.execute(
            select(Account).where(Account.is_active == True).order_by(Account.code)
        )
        accounts = list(accounts.scalars().all())

        revenue_accounts = []
        expense_accounts = []

        for account in accounts:
            result = self.db.execute(
                select(
                    func.coalesce(func.sum(LineItem.debit), Decimal("0.00")).label("debit_total"),
                    func.coalesce(func.sum(LineItem.credit), Decimal("0.00")).label("credit_total"),
                )
                .join(JournalEntry)
                .where(
                    LineItem.account_id == account.id,
                    JournalEntry.date >= start_date,
                    JournalEntry.date <= end_date,
                    JournalEntry.posted_at.isnot(None),
                )
            )
            row = result.one_or_none()
            if row:
                debit_total = Decimal(str(row.debit_total))
                credit_total = Decimal(str(row.credit_total))

                if account.account_type == AccountType.REVENUE:
                    balance = credit_total - debit_total
                    if balance != Decimal("0.00"):
                        revenue_accounts.append(
                            AccountBalance(
                                id=account.id,
                                code=account.code,
                                name=account.name,
                                account_type=account.account_type,
                                balance=balance,
                            )
                        )
                elif account.account_type == AccountType.EXPENSE:
                    balance = debit_total - credit_total
                    if balance != Decimal("0.00"):
                        expense_accounts.append(
                            AccountBalance(
                                id=account.id,
                                code=account.code,
                                name=account.name,
                                account_type=account.account_type,
                                balance=balance,
                            )
                        )

        total_revenue = sum(acc.balance for acc in revenue_accounts)
        total_expenses = sum(acc.balance for acc in expense_accounts)
        net_income = total_revenue - total_expenses

        return IncomeStatementResponse(
            start_date=start_date,
            end_date=end_date,
            revenue=BalanceSheetSection(
                name="Revenue", accounts=revenue_accounts, total=Decimal(str(total_revenue))
            ),
            expenses=BalanceSheetSection(
                name="Expenses", accounts=expense_accounts, total=Decimal(str(total_expenses))
            ),
            gross_profit=Decimal(str(total_revenue)),
            net_income=Decimal(str(net_income)),
        )

    def get_account_ledger(
        self, account_id: UUID, start_date: date | None = None, end_date: date | None = None
    ) -> AccountLedgerResponse | None:
        account = self.db.execute(
            select(Account).where(Account.id == account_id)
        )
        account = account.scalar_one_or_none()
        if not account:
            return None

        query = (
            select(JournalEntry, LineItem)
            .join(LineItem, JournalEntry.id == LineItem.journal_entry_id)
            .where(
                LineItem.account_id == account_id,
                JournalEntry.posted_at.isnot(None),
            )
        )

        if start_date:
            query = query.where(JournalEntry.date >= start_date)
        if end_date:
            query = query.where(JournalEntry.date <= end_date)

        query = query.order_by(JournalEntry.date, JournalEntry.entry_number)

        result = self.db.execute(query)
        rows = result.all()

        opening_balance = Decimal("0.00")
        if start_date:
            prev_result = self.db.execute(
                select(
                    func.coalesce(func.sum(LineItem.debit), Decimal("0.00")).label("debit_total"),
                    func.coalesce(func.sum(LineItem.credit), Decimal("0.00")).label("credit_total"),
                )
                .join(JournalEntry)
                .where(
                    LineItem.account_id == account_id,
                    JournalEntry.date < start_date,
                    JournalEntry.posted_at.isnot(None),
                )
            )
            prev_row = prev_result.one_or_none()
            if prev_row:
                debit_total = Decimal(str(prev_row.debit_total))
                credit_total = Decimal(str(prev_row.credit_total))
                if account.account_type.is_debit_positive:
                    opening_balance = debit_total - credit_total
                else:
                    opening_balance = credit_total - debit_total

        entries = []
        running_balance = opening_balance
        total_debits = Decimal("0.00")
        total_credits = Decimal("0.00")

        for journal_entry, line_item in rows:
            debit = line_item.debit
            credit = line_item.credit

            if account.account_type.is_debit_positive:
                running_balance += debit - credit
            else:
                running_balance += credit - debit

            entries.append(
                LedgerEntry(
                    date=journal_entry.date,
                    entry_number=journal_entry.entry_number,
                    description=journal_entry.description,
                    debit=debit,
                    credit=credit,
                    balance=running_balance,
                    entry_id=journal_entry.id,
                )
            )
            total_debits += debit
            total_credits += credit

        return AccountLedgerResponse(
            account_id=account.id,
            account_code=account.code,
            account_name=account.name,
            account_type=account.account_type,
            start_date=start_date,
            end_date=end_date,
            opening_balance=opening_balance,
            entries=entries,
            closing_balance=running_balance,
            total_debits=total_debits,
            total_credits=total_credits,
        )
