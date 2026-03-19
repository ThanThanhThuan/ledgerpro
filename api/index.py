# Vercel Serverless Function for LedgerPro API
# This handles all API routes as a single serverless function

import json
import os
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import parse_qs

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID

from app.models.account import Account
from app.models.journal_entry import JournalEntry, LineItem
from app.models.enums import AccountType

DATABASE_URL = os.environ.get('DATABASE_URL', '')

if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

engine = create_engine(DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://'))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_session():
    return SessionLocal()

def response_json(data, status=200):
    return {
        "statusCode": status,
        "body": json.dumps(data, default=str),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    }

def parse_path(path):
    parts = path.strip('/').split('/')
    return parts

def handler(event, context):
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    query = event.get('queryStringParameters') or {}
    path_params = event.get('pathParameters') or {}
    
    db = get_session()
    try:
        parts = parse_path(path)
        
        # CORS preflight
        if method == 'OPTIONS':
            return response_json({}, 200)
        
        # API Routes
        if parts[0] == 'api':
            if len(parts) == 1 or parts[1] == '':
                return response_json({"error": "Not found"}, 404)
            
            resource = parts[1]
            
            # Health check
            if resource == 'health':
                return response_json({"status": "healthy"})
            
            # Accounts
            if resource == 'accounts':
                if len(parts) == 2 or (len(parts) == 3 and parts[2] == ''):
                    if method == 'GET':
                        include_inactive = query.get('include_inactive', 'false').lower() == 'true'
                        accounts = db.execute(
                            select(Account).order_by(Account.code)
                        ).scalars().all()
                        result = []
                        for a in accounts:
                            if not include_inactive and not a.is_active:
                                continue
                            result.append({
                                "id": str(a.id),
                                "code": a.code,
                                "name": a.name,
                                "account_type": a.account_type.value,
                                "is_active": a.is_active,
                                "parent_id": str(a.parent_id) if a.parent_id else None,
                            })
                        return response_json(result)
                    elif method == 'POST':
                        body = json.loads(event.get('body', '{}'))
                        acc = Account(
                            code=body['code'],
                            name=body['name'],
                            account_type=AccountType(body['account_type']),
                            parent_id=body.get('parent_id')
                        )
                        db.add(acc)
                        db.commit()
                        return response_json({
                            "id": str(acc.id),
                            "code": acc.code,
                            "name": acc.name,
                            "account_type": acc.account_type.value,
                        }, 201)
                
                # Single account
                account_id = parts[2] if len(parts) > 2 else None
                if account_id and len(parts) == 3:
                    if method == 'GET':
                        acc = db.get(Account, account_id)
                        if not acc:
                            return response_json({"error": "Not found"}, 404)
                        return response_json({
                            "id": str(acc.id),
                            "code": acc.code,
                            "name": acc.name,
                            "account_type": acc.account_type.value,
                            "is_active": acc.is_active,
                            "parent_id": str(acc.parent_id) if acc.parent_id else None,
                        })
                    elif method == 'PUT':
                        acc = db.get(Account, account_id)
                        if not acc:
                            return response_json({"error": "Not found"}, 404)
                        body = json.loads(event.get('body', '{}'))
                        if 'name' in body:
                            acc.name = body['name']
                        if 'code' in body:
                            acc.code = body['code']
                        db.commit()
                        return response_json({"message": "Updated"})
                    elif method == 'DELETE':
                        acc = db.get(Account, account_id)
                        if not acc:
                            return response_json({"error": "Not found"}, 404)
                        acc.is_active = False
                        db.commit()
                        return response_json({"message": "Deactivated"})
                
                # Account balance
                if account_id == 'balance' and len(parts) == 4:
                    result = db.execute(
                        select(
                            func.coalesce(func.sum(LineItem.debit), Decimal("0.00")).label("debit"),
                            func.coalesce(func.sum(LineItem.credit), Decimal("0.00")).label("credit"),
                        ).where(LineItem.account_id == parts[3])
                    ).one_or_none()
                    return response_json({
                        "debit": float(result[0]) if result else 0,
                        "credit": float(result[1]) if result else 0,
                    })
            
            # Journal Entries
            if resource == 'journal-entries':
                if method == 'GET':
                    skip = int(query.get('skip', 0))
                    limit = int(query.get('limit', 100))
                    
                    entries = db.execute(
                        select(JournalEntry)
                        .order_by(JournalEntry.date.desc(), JournalEntry.entry_number.desc())
                        .offset(skip).limit(limit)
                    ).scalars().all()
                    
                    result = []
                    for e in entries:
                        line_items = db.execute(
                            select(LineItem).where(LineItem.journal_entry_id == e.id)
                        ).scalars().all()
                        total_dr = sum(li.debit for li in line_items)
                        total_cr = sum(li.credit for li in line_items)
                        result.append({
                            "id": str(e.id),
                            "entry_number": e.entry_number,
                            "date": e.date.isoformat() if e.date else None,
                            "description": e.description,
                            "reference": e.reference,
                            "is_posted": e.posted_at is not None,
                            "total_debits": float(total_dr),
                            "total_credits": float(total_cr),
                        })
                    
                    return response_json({"entries": result, "total": len(result)})
                
                elif method == 'POST':
                    body = json.loads(event.get('body', '{}'))
                    
                    # Generate entry number
                    last_entry = db.execute(
                        select(JournalEntry.entry_number)
                        .where(JournalEntry.entry_number.like('JE-%'))
                        .order_by(JournalEntry.entry_number.desc())
                        .limit(1)
                    ).scalar_one_or_none()
                    
                    if last_entry:
                        num = int(last_entry.split('-')[1]) + 1
                    else:
                        num = 1
                    entry_num = f"JE-{num:05d}"
                    
                    entry = JournalEntry(
                        entry_number=entry_num,
                        date=body.get('date', date.today()),
                        description=body['description'],
                        reference=body.get('reference'),
                    )
                    db.add(entry)
                    db.flush()
                    
                    for item in body.get('line_items', []):
                        line = LineItem(
                            journal_entry_id=entry.id,
                            account_id=item['account_id'],
                            debit=Decimal(str(item.get('debit', 0))),
                            credit=Decimal(str(item.get('credit', 0))),
                            memo=item.get('memo'),
                        )
                        db.add(line)
                    
                    db.commit()
                    return response_json({"id": str(entry.id), "entry_number": entry_num}, 201)
            
            # Reports
            if resource == 'reports':
                report_type = parts[2] if len(parts) > 2 else None
                as_of_date = query.get('as_of_date', date.today().isoformat())
                as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date() if as_of_date else date.today()
                
                if report_type == 'balance-sheet':
                    accounts = db.execute(
                        select(Account).where(Account.is_active == True).order_by(Account.code)
                    ).scalars().all()
                    
                    assets, liabilities, equity = [], [], []
                    total_assets = Decimal(0)
                    
                    for acc in accounts:
                        result = db.execute(
                            select(
                                func.coalesce(func.sum(LineItem.debit), Decimal("0.00")).label("dr"),
                                func.coalesce(func.sum(LineItem.credit), Decimal("0.00")).label("cr"),
                            ).join(JournalEntry)
                            .where(
                                LineItem.account_id == acc.id,
                                JournalEntry.date <= as_of_date,
                                JournalEntry.posted_at.isnot(None),
                            )
                        ).one_or_none()
                        
                        dr = Decimal(str(result[0])) if result else Decimal(0)
                        cr = Decimal(str(result[1])) if result else Decimal(0)
                        
                        if acc.account_type.is_debit_positive:
                            balance = dr - cr
                        else:
                            balance = cr - dr
                        
                        if balance != 0:
                            acc_data = {
                                "code": acc.code,
                                "name": acc.name,
                                "account_type": acc.account_type.value,
                                "balance": float(balance),
                            }
                            if acc.account_type == AccountType.ASSET:
                                assets.append(acc_data)
                                total_assets += balance
                            elif acc.account_type == AccountType.LIABILITY:
                                liabilities.append(acc_data)
                            elif acc.account_type == AccountType.EQUITY:
                                equity.append(acc_data)
                    
                    return response_json({
                        "assets": {"accounts": assets, "total": float(total_assets)},
                        "liabilities": {"accounts": liabilities, "total": float(sum(a['balance'] for a in liabilities))},
                        "equity": {"accounts": equity, "total": float(sum(a['balance'] for a in equity))},
                        "is_balanced": True,
                    })
                
                if report_type == 'trial-balance':
                    accounts = db.execute(
                        select(Account).where(Account.is_active == True).order_by(Account.code)
                    ).scalars().all()
                    
                    rows = []
                    total_dr, total_cr = Decimal(0), Decimal(0)
                    
                    for acc in accounts:
                        result = db.execute(
                            select(
                                func.coalesce(func.sum(LineItem.debit), Decimal("0.00")).label("dr"),
                                func.coalesce(func.sum(LineItem.credit), Decimal("0.00")).label("cr"),
                            ).join(JournalEntry)
                            .where(
                                LineItem.account_id == acc.id,
                                JournalEntry.date <= as_of_date,
                            )
                        ).one_or_none()
                        
                        dr = Decimal(str(result[0])) if result else Decimal(0)
                        cr = Decimal(str(result[1])) if result else Decimal(0)
                        
                        if acc.account_type.is_debit_positive:
                            dr_bal = dr - cr
                            cr_bal = Decimal(0)
                        else:
                            cr_bal = cr - dr
                            dr_bal = Decimal(0)
                        
                        if dr_bal > 0 or cr_bal > 0:
                            rows.append({
                                "code": acc.code,
                                "name": acc.name,
                                "debit_balance": float(dr_bal),
                                "credit_balance": float(cr_bal),
                            })
                            total_dr += dr_bal
                            total_cr += cr_bal
                    
                    return response_json({
                        "accounts": rows,
                        "total_debits": float(total_dr),
                        "total_credits": float(total_cr),
                        "is_balanced": total_dr == total_cr,
                    })
            
            return response_json({"error": "Not found"}, 404)
        
        # SPA fallback - return index.html
        return {
            "statusCode": 200,
            "body": open("index.html").read() if os.path.exists("index.html") else "<html><body><h1>LedgerPro</h1><p>API is running</p></body></html>",
            "headers": {"Content-Type": "text/html"}
        }
    
    except Exception as e:
        import traceback
        return response_json({"error": str(e), "trace": traceback.format_exc()}, 500)
    finally:
        db.close()
