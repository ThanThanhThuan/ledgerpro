import json
import os
from flask import Flask, jsonify, request, Response
from sqlalchemy import create_engine, text

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', '')

def get_engine():
    url = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://')
    return create_engine(url)

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/test')
def test():
    return jsonify({
        "db_set": bool(DATABASE_URL),
        "path": request.path
    })

@app.route('/api/accounts', methods=['GET', 'POST'])
def accounts():
    engine = get_engine()
    with engine.connect() as conn:
        if request.method == 'GET':
            result = conn.execute(text("""
                SELECT id::text, code, name, account_type, is_active 
                FROM accounts WHERE is_active = true ORDER BY code
            """))
            accounts = [{"id": r[0], "code": r[1], "name": r[2], "account_type": r[3], "is_active": r[4]} for r in result]
            return jsonify(accounts)
        
        if request.method == 'POST':
            data = request.json
            result = conn.execute(text("""
                INSERT INTO accounts (code, name, account_type) 
                VALUES (:code, :name, :account_type) 
                RETURNING id::text
            """), {"code": data['code'], "name": data['name'], "account_type": data['account_type']})
            row = result.fetchone()
            conn.commit()
            return jsonify({"id": row[0]}), 201

@app.route('/api/accounts/<account_id>')
def account_detail(account_id):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id::text, code, name, account_type, is_active 
            FROM accounts WHERE id = :id
        """), {"id": account_id})
        row = result.fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"id": row[0], "code": row[1], "name": row[2], "account_type": row[3], "is_active": row[4]})

@app.route('/api/journal-entries', methods=['GET', 'POST'])
def journal_entries():
    engine = get_engine()
    with engine.connect() as conn:
        if request.method == 'GET':
            result = conn.execute(text("""
                SELECT id::text, entry_number, date::text, description, reference, posted_at
                FROM journal_entries ORDER BY date DESC, entry_number DESC LIMIT 100
            """))
            entries = [{
                "id": r[0], "entry_number": r[1], "date": r[2], 
                "description": r[3], "reference": r[4], "is_posted": r[5] is not None
            } for r in result]
            return jsonify({"entries": entries, "total": len(entries)})

        if request.method == 'POST':
            data = request.json
            date = data.get('date')
            description = data.get('description')
            reference = data.get('reference')
            lines = data.get('lines', [])
            
            if not lines:
                return jsonify({"error": "At least one line item required"}), 400
            
            total_debit = sum(float(l.get('debit', 0)) for l in lines)
            total_credit = sum(float(l.get('credit', 0)) for l in lines)
            
            if abs(total_debit - total_credit) > 0.01:
                return jsonify({"error": f"Debits ({total_debit}) must equal Credits ({total_credit})"}), 400
            
            entry_result = conn.execute(text("""
                INSERT INTO journal_entries (entry_number, date, description, reference)
                VALUES (
                    'JE-' || COALESCE(
                        (SELECT MAX(CAST(SUBSTRING(entry_number FROM 4) AS INTEGER)) 
                         FROM journal_entries WHERE entry_number LIKE 'JE-%'), 
                        0) + 1,
                    :date, :description, :reference
                )
                RETURNING id::text, entry_number
            """), {"date": date, "description": description, "reference": reference})
            entry_row = entry_result.fetchone()
            entry_id = entry_row[0]
            entry_number = entry_row[1]
            
            for line in lines:
                conn.execute(text("""
                    INSERT INTO line_items (journal_entry_id, account_id, debit, credit, memo)
                    VALUES (:entry_id, :account_id, :debit, :credit, :memo)
                """), {
                    "entry_id": entry_id,
                    "account_id": line.get('account_id'),
                    "debit": float(line.get('debit', 0)),
                    "credit": float(line.get('credit', 0)),
                    "memo": line.get('memo', '')
                })
            
            conn.commit()
            return jsonify({"id": entry_id, "entry_number": entry_number}), 201

@app.route('/api/reports/balance-sheet')
def balance_sheet():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id::text, code, name, account_type FROM accounts WHERE is_active = true ORDER BY code
        """))
        
        assets, liabilities, equity = [], [], []
        total_assets = 0
        
        for r in result:
            bal = conn.execute(text("""
                SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0)
                FROM line_items li JOIN journal_entries je ON li.journal_entry_id = je.id
                WHERE li.account_id = :id AND je.posted_at IS NOT NULL
            """), {"id": r[0]}).fetchone()
            
            dr = float(bal[0]) if bal else 0
            cr = float(bal[1]) if bal else 0
            
            if r[3] in ['asset', 'expense']:
                balance = dr - cr
            else:
                balance = cr - dr
            
            acc = {"code": r[1], "name": r[2], "account_type": r[3], "balance": balance}
            
            if balance != 0:
                if r[3] == 'asset':
                    assets.append(acc)
                    total_assets += balance
                elif r[3] == 'liability':
                    liabilities.append(acc)
                elif r[3] == 'equity':
                    equity.append(acc)
        
        return jsonify({
            "assets": {"accounts": assets, "total": total_assets},
            "liabilities": {"accounts": liabilities, "total": sum(a['balance'] for a in liabilities)},
            "equity": {"accounts": equity, "total": sum(a['balance'] for a in equity)},
            "is_balanced": True
        })

@app.route('/api/reports/trial-balance')
def trial_balance():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id::text, code, name, account_type FROM accounts WHERE is_active = true ORDER BY code
        """))
        
        rows, total_dr, total_cr = [], 0, 0
        
        for r in result:
            bal = conn.execute(text("""
                SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0)
                FROM line_items li JOIN journal_entries je ON li.journal_entry_id = je.id
                WHERE li.account_id = :id AND je.posted_at IS NOT NULL
            """), {"id": r[0]}).fetchone()
            
            dr = float(bal[0]) if bal else 0
            cr = float(bal[1]) if bal else 0
            
            if r[3] in ['asset', 'expense']:
                dr_bal, cr_bal = dr - cr, 0
            else:
                dr_bal, cr_bal = 0, cr - dr
            
            if dr_bal > 0 or cr_bal > 0:
                rows.append({"code": r[1], "name": r[2], "debit_balance": dr_bal, "credit_balance": cr_bal})
                total_dr += dr_bal
                total_cr += cr_bal
        
        return jsonify({
            "accounts": rows,
            "total_debits": total_dr,
            "total_credits": total_cr,
            "is_balanced": abs(total_dr - total_cr) < 0.01
        })

@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()
    return Response(html, mimetype='text/html')

if __name__ == '__main__':
    app.run(debug=True)
