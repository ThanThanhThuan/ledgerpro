from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountWithBalance,
)
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
):
    service = AccountService(db)
    return service.get_all(include_inactive=include_inactive)


@router.get("/{account_id}", response_model=AccountWithBalance)
def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
):
    service = AccountService(db)
    account = service.get_with_balance(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
):
    service = AccountService(db)

    existing = service.get_by_code(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Account code already exists")

    return service.create(data)


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: UUID,
    data: AccountUpdate,
    db: Session = Depends(get_db),
):
    service = AccountService(db)

    if data.code:
        existing = service.get_by_code(data.code)
        if existing and existing.id != account_id:
            raise HTTPException(status_code=400, detail="Account code already exists")

    account = service.update(account_id, data)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: UUID,
    db: Session = Depends(get_db),
):
    service = AccountService(db)
    deleted = service.delete(account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")


@router.get("/{account_id}/ledger")
def get_account_ledger(
    account_id: UUID,
    db: Session = Depends(get_db),
):
    from app.services.report_service import ReportService
    from datetime import date as date_type

    service = ReportService(db)
    ledger = service.get_account_ledger(account_id, None, date_type.today())
    if not ledger:
        raise HTTPException(status_code=404, detail="Account not found")
    return ledger
