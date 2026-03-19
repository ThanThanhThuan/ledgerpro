import json
import os
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.models.account import Account
from app.models.journal_entry import JournalEntry, LineItem
from app.models.enums import AccountType

def get_db():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"
    
    engine = create_engine(DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://'))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def handler(request):
    path = request.path
    method = request.method
    query = dict(request.query)
    
    # Get database session
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        return {"statusCode": 500, "body": json.dumps({"error": "DATABASE_URL not set"})}
    
    engine = create_engine(DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://'))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # API routes
        if path.startswith('/api/'):
            parts = path.strip('/').split('/')
            
            # Health
            if '/health' in path:
                return {"statusCode": 200, "body": json.dumps({"status": "healthy"})}
            
            # Accounts
            if '/accounts' in path:
                if method == 'GET':
                    accounts = db.execute(select(Account).order_by(Account.code)).scalars().all()
                    result = [{
                        "id": str(a.id),
                        "code": a.code,
                        "name": a.name,
                        "account_type": a.account_type.value,
                        "is_active": a.is_active,
                    } for a in accounts if a.is_active]
                    return {"statusCode": 200, "body": json.dumps(result)}
                elif method == 'POST':
                    body = json.loads(request.body)
                    acc = Account(
                        code=body['code'],
                        name=body['name'],
                        account_type=AccountType(body['account_type'])
                    )
                    db.add(acc)
                    db.commit()
                    return {"statusCode": 201, "body": json.dumps({"id": str(acc.id)})}
            
            # Journal Entries
            if '/journal-entries' in path:
                if method == 'GET':
                    entries = db.execute(
                        select(JournalEntry).order_by(JournalEntry.date.desc())
                    ).scalars().all()
                    result = [{
                        "id": str(e.id),
                        "entry_number": e.entry_number,
                        "date": e.date.isoformat() if e.date else None,
                        "description": e.description,
                        "is_posted": e.posted_at is not None,
                    } for e in entries]
                    return {"statusCode": 200, "body": json.dumps(result)}
            
            # Reports
            if '/reports/balance-sheet' in path:
                accounts = db.execute(select(Account).order_by(Account.code)).scalars().all()
                assets, liabilities, equity = [], [], []
                total_assets = Decimal(0)
                
                for acc in accounts:
                    if not acc.is_active:
                        continue
                    
                    result = db.execute(
                        select(
                            func.coalesce(func.sum(LineItem.debit), 0).label("dr"),
                            func.coalesce(func.sum(LineItem.credit), 0).label("cr"),
                        ).join(JournalEntry)
                        .where(
                            LineItem.account_id == acc.id,
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
                            "balance": float(balance),
                        }
                        if acc.account_type == AccountType.ASSET:
                            assets.append(acc_data)
                            total_assets += balance
                        elif acc.account_type == AccountType.LIABILITY:
                            liabilities.append(acc_data)
                        elif acc.account_type == AccountType.EQUITY:
                            equity.append(acc_data)
                
                total_liab = sum(a['balance'] for a in liabilities)
                total_eq = sum(a['balance'] for a in equity)
                
                return {"statusCode": 200, "body": json.dumps({
                    "assets": {"accounts": assets, "total": float(total_assets)},
                    "liabilities": {"accounts": liabilities, "total": float(total_liab)},
                    "equity": {"accounts": equity, "total": float(total_eq)},
                    "is_balanced": True,
                })}
            
            return {"statusCode": 404, "body": json.dumps({"error": "Not found"})}
        
        # Serve index.html for all other routes (SPA)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LedgerPro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container py-5 text-center">
        <h1>LedgerPro</h1>
        <p class="lead">Double Entry Accounting System</p>
        <div class="alert alert-info">
            <strong>API is running!</strong><br>
            Go to <code>/api/health</code> to check status.
        </div>
    </div>
</body>
</html>"""
        }
    
    except Exception as e:
        import traceback
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    finally:
        db.close()
