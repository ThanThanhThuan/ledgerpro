# LedgerPro - Double-Entry Accounting System

A complete double-entry accounting web application built with FastAPI and PostgreSQL ORM.

## Features

- **Chart of Accounts**: Create and manage accounts (Assets, Liabilities, Equity, Revenue, Expenses)
- **Journal Entries**: Create, edit, post, and unpost double-entry transactions
- **Financial Reports**:
  - Trial Balance
  - Balance Sheet
  - Income Statement
  - General Ledger
  - Account-specific Ledger

## Technology Stack

- **Backend**: FastAPI (Python)
- **ORM**: SQLAlchemy 2.0 with async support
- **Database**: PostgreSQL
- **Frontend**: HTML templates with Bootstrap 5 and vanilla JavaScript
- **Validation**: Pydantic v2

## Prerequisites

- Python 3.10+
- PostgreSQL 14+

## Installation

1. **Clone the repository and navigate to the project directory**
   ```bash
   cd myodoo
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   ```bash
   # Create the database
   createdb ledgerpro
   
   # Or connect to PostgreSQL and run:
   # CREATE DATABASE ledgerpro;
   ```

5. **Configure environment variables**
   ```bash
   # Copy the example env file
   copy .env.example .env
   
   # Edit .env with your database credentials
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/ledgerpro
   ```

6. **Initialize the database** (optional - tables are auto-created on first run)
   ```bash
   psql -U postgres -d ledgerpro -f setup_database.sql
   ```

7. **Run the application**
   ```bash
   python run.py
   ```

8. **Open in browser**
   Navigate to `http://localhost:8000`

## API Endpoints

### Accounts
- `GET /api/accounts` - List all accounts
- `GET /api/accounts/{id}` - Get account with balance
- `POST /api/accounts` - Create account
- `PUT /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Deactivate account

### Journal Entries
- `GET /api/journal-entries` - List entries with pagination
- `GET /api/journal-entries/{id}` - Get entry details
- `POST /api/journal-entries` - Create entry (validates debits = credits)
- `PUT /api/journal-entries/{id}` - Update entry (draft only)
- `DELETE /api/journal-entries/{id}` - Delete entry (draft only)
- `POST /api/journal-entries/{id}/post` - Post entry
- `POST /api/journal-entries/{id}/unpost` - Unpost entry

### Reports
- `GET /api/reports/trial-balance` - Trial Balance
- `GET /api/reports/balance-sheet` - Balance Sheet
- `GET /api/reports/income-statement` - Income Statement
- `GET /api/reports/account-ledger/{id}` - Account Ledger
- `GET /api/reports/general-ledger` - General Ledger

## Double-Entry Accounting Rules

1. Every transaction affects at least two accounts
2. Total Debits must equal Total Credits for each entry
3. Account types and their normal balances:
   - **Assets** (debit increases) - Cash, Accounts Receivable, Equipment
   - **Liabilities** (credit increases) - Accounts Payable, Loans
   - **Equity** (credit increases) - Owner's Capital, Retained Earnings
   - **Revenue** (credit increases) - Sales, Services
   - **Expenses** (debit increases) - Rent, Salaries, Utilities

## Project Structure

```
myodoo/
├── app/
│   ├── api/              # API route handlers
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── templates/        # HTML templates
│   ├── database.py       # Database connection
│   └── main.py           # FastAPI application
├── config.py             # Configuration
├── requirements.txt
├── run.py                # Application runner
├── setup_database.sql    # Database setup script
└── SPEC.md              # Full specification
```

## License

MIT
