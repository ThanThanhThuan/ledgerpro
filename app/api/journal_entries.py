from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.journal_entry import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryWithLineItems,
)
from app.services.journal_service import JournalService

router = APIRouter(prefix="/api/journal-entries", tags=["journal-entries"])


@router.get("")
def list_journal_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    start_date: date | None = None,
    end_date: date | None = None,
    posted_only: bool | None = None,
    db: Session = Depends(get_db),
):
    service = JournalService(db)
    entries, total = service.get_all(
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        posted_only=posted_only,
    )

    result = []
    for entry in entries:
        total_debits = sum(item.debit for item in entry.line_items)
        total_credits = sum(item.credit for item in entry.line_items)
        result.append({
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
            "line_items_count": len(entry.line_items),
        })

    return {"entries": result, "total": total, "skip": skip, "limit": limit}


@router.get("/{entry_id}", response_model=JournalEntryWithLineItems)
def get_journal_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
):
    service = JournalService(db)
    entry = service.get_entry_details(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.post("", response_model=JournalEntryWithLineItems, status_code=status.HTTP_201_CREATED)
def create_journal_entry(
    data: JournalEntryCreate,
    db: Session = Depends(get_db),
):
    service = JournalService(db)

    from app.services.account_service import AccountService
    account_service = AccountService(db)

    for item in data.line_items:
        account = account_service.get_by_id(item.account_id)
        if not account:
            raise HTTPException(
                status_code=400, detail=f"Account {item.account_id} not found"
            )
        if not account.is_active:
            raise HTTPException(
                status_code=400, detail=f"Account {account.code} is inactive"
            )

    try:
        entry = service.create(data)
        return service.get_entry_details(entry.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{entry_id}", response_model=JournalEntryWithLineItems)
def update_journal_entry(
    entry_id: UUID,
    data: JournalEntryUpdate,
    db: Session = Depends(get_db),
):
    service = JournalService(db)

    try:
        entry = service.update(entry_id, data)
        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        return service.get_entry_details(entry.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_journal_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
):
    service = JournalService(db)
    try:
        deleted = service.delete(entry_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Journal entry not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/post", response_model=JournalEntryWithLineItems)
def post_journal_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
):
    service = JournalService(db)
    try:
        entry = service.post(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        return service.get_entry_details(entry.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/unpost", response_model=JournalEntryWithLineItems)
def unpost_journal_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
):
    service = JournalService(db)
    entry = service.unpost(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return service.get_entry_details(entry.id)
