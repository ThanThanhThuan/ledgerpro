from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.reports import (
    TrialBalanceResponse,
    BalanceSheetResponse,
    IncomeStatementResponse,
    AccountLedgerResponse,
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/trial-balance", response_model=TrialBalanceResponse)
def get_trial_balance(
    as_of_date: date = Query(default=None),
    db: Session = Depends(get_db),
):
    if as_of_date is None:
        as_of_date = date.today()

    service = ReportService(db)
    return service.get_trial_balance(as_of_date)


@router.get("/balance-sheet", response_model=BalanceSheetResponse)
def get_balance_sheet(
    as_of_date: date = Query(default=None),
    db: Session = Depends(get_db),
):
    if as_of_date is None:
        as_of_date = date.today()

    service = ReportService(db)
    return service.get_balance_sheet(as_of_date)


@router.get("/income-statement", response_model=IncomeStatementResponse)
def get_income_statement(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    return service.get_income_statement(start_date, end_date)


@router.get("/account-ledger/{account_id}", response_model=AccountLedgerResponse)
def get_account_ledger(
    account_id: UUID,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    ledger = service.get_account_ledger(account_id, start_date, end_date)
    if not ledger:
        raise HTTPException(status_code=404, detail="Account not found")
    return ledger


@router.get("/general-ledger")
def get_general_ledger(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    from app.services.account_service import AccountService

    account_service = AccountService(db)
    accounts = account_service.get_all()

    service = ReportService(db)
    ledgers = []
    for account in accounts:
        ledger = service.get_account_ledger(account.id, start_date, end_date)
        if ledger and (ledger.total_debits > 0 or ledger.total_credits > 0):
            ledgers.append(ledger)

    return {"ledgers": ledgers, "start_date": start_date, "end_date": end_date}
