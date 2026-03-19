import json
import os
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import sessionmaker

def handler(request):
    path = request.path
    method = request.method
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        return {"statusCode": 500, "body": json.dumps({"error": "DATABASE_URL not set"})}
    
    engine = create_engine(DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://'))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        if path == '/api/health':
            return {"statusCode": 200, "body": json.dumps({"status": "healthy"})}
        
        if path == '/api/accounts' and method == 'GET':
            result = db.execute(text("""
                SELECT id::text, code, name, account_type, is_active 
                FROM accounts 
                WHERE is_active = true 
                ORDER BY code
            """))
            accounts = [{"id": r[0], "code": r[1], "name": r[2], "account_type": r[3], "is_active": r[4]} for r in result]
            return {"statusCode": 200, "body": json.dumps(accounts)}
        
        if path == '/api/journal-entries' and method == 'GET':
            result = db.execute(text("""
                SELECT id::text, entry_number, date::text, description, reference, posted_at
                FROM journal_entries
                ORDER BY date DESC, entry_number DESC
                LIMIT 100
            """))
            entries = [{
                "id": r[0],
                "entry_number": r[1],
                "date": r[2],
                "description": r[3],
                "reference": r[4],
                "is_posted": r[5] is not None
            } for r in result]
            return {"statusCode": 200, "body": json.dumps({"entries": entries})}
        
        if path == '/api/reports/balance-sheet':
            result = db.execute(text("""
                SELECT id::text, code, name, account_type FROM accounts WHERE is_active = true ORDER BY code
            """))
            
            assets, liabilities, equity = [], [], []
            total_assets = 0
            
            for r in result:
                bal_result = db.execute(text("""
                    SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0)
                    FROM line_items li
                    JOIN journal_entries je ON li.journal_entry_id = je.id
                    WHERE li.account_id = :acc_id AND je.posted_at IS NOT NULL
                """), {"acc_id": r[0]}).fetchone()
                
                dr = float(bal_result[0]) if bal_result else 0
                cr = float(bal_result[1]) if bal_result else 0
                
                if r[3] in ['asset', 'expense']:
                    balance = dr - cr
                else:
                    balance = cr - dr
                
                acc_data = {"code": r[1], "name": r[2], "account_type": r[3], "balance": balance}
                
                if balance != 0:
                    if r[3] == 'asset':
                        assets.append(acc_data)
                        total_assets += balance
                    elif r[3] == 'liability':
                        liabilities.append(acc_data)
                    elif r[3] == 'equity':
                        equity.append(acc_data)
            
            total_liab = sum(a['balance'] for a in liabilities)
            total_eq = sum(a['balance'] for a in equity)
            
            return {"statusCode": 200, "body": json.dumps({
                "assets": {"accounts": assets, "total": total_assets},
                "liabilities": {"accounts": liabilities, "total": total_liab},
                "equity": {"accounts": equity, "total": total_eq},
                "is_balanced": True,
            })}
        
        if path == '/api/reports/trial-balance':
            result = db.execute(text("""
                SELECT id::text, code, name, account_type FROM accounts WHERE is_active = true ORDER BY code
            """))
            
            rows = []
            total_dr, total_cr = 0, 0
            
            for r in result:
                bal_result = db.execute(text("""
                    SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0)
                    FROM line_items li
                    JOIN journal_entries je ON li.journal_entry_id = je.id
                    WHERE li.account_id = :acc_id AND je.posted_at IS NOT NULL
                """), {"acc_id": r[0]}).fetchone()
                
                dr = float(bal_result[0]) if bal_result else 0
                cr = float(bal_result[1]) if bal_result else 0
                
                if r[3] in ['asset', 'expense']:
                    dr_bal = dr - cr
                    cr_bal = 0
                else:
                    cr_bal = cr - dr
                    dr_bal = 0
                
                if dr_bal > 0 or cr_bal > 0:
                    rows.append({
                        "code": r[1],
                        "name": r[2],
                        "debit_balance": dr_bal,
                        "credit_balance": cr_bal,
                    })
                    total_dr += dr_bal
                    total_cr += cr_bal
            
            return {"statusCode": 200, "body": json.dumps({
                "accounts": rows,
                "total_debits": total_dr,
                "total_credits": total_cr,
                "is_balanced": abs(total_dr - total_cr) < 0.01,
            })}
        
        # SPA fallback
        html = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LedgerPro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f8f9fa; margin: 0; }
        .sidebar { background: #2c3e50; min-height: 100vh; width: 200px; color: white; padding: 20px; }
        .sidebar a { color: rgba(255,255,255,0.8); text-decoration: none; display: block; padding: 10px 0; }
        .sidebar a:hover { color: white; background: rgba(255,255,255,0.1); }
        .main { padding: 40px; }
    </style>
</head>
<body>
    <div style="display: flex;">
        <div class="sidebar">
            <h4>LedgerPro</h4>
            <a href="#/">Dashboard</a>
            <a href="#/accounts">Chart of Accounts</a>
            <a href="#/journal">Journal Entries</a>
            <a href="#/reports">Financial Reports</a>
        </div>
        <div class="main">
            <h1>LedgerPro</h1>
            <p>Double Entry Accounting System</p>
            <div class="alert alert-success">
                <strong>API is running!</strong><br>
                Visit <code>/api/health</code> for status.
            </div>
            <h3>Available Endpoints:</h3>
            <ul>
                <li><code>GET /api/health</code> - Health check</li>
                <li><code>GET /api/accounts</code> - List accounts</li>
                <li><code>GET /api/journal-entries</code> - List entries</li>
                <li><code>GET /api/reports/balance-sheet</code> - Balance sheet</li>
                <li><code>GET /api/reports/trial-balance</code> - Trial balance</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
        return {"statusCode": 200, "headers": {"Content-Type": "text/html"}, "body": html}
    
    except Exception as e:
        import traceback
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    finally:
        db.close()
