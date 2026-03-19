# Double-Entry Accounting Web Application

## Project Overview

**Project Name:** LedgerPro  
**Type:** REST API + Web Interface for Double-Entry Accounting  
**Core Functionality:** A complete double-entry accounting system with chart of accounts, journal entries, and financial reports  
**Target Users:** Small businesses, freelancers, and accounting students

## Technology Stack

- **Backend Framework:** FastAPI
- **ORM:** SQLAlchemy 2.0 with async support
- **Database:** PostgreSQL
- **Frontend:** HTML templates with vanilla JavaScript
- **Validation:** Pydantic v2

## Accounting Concepts Implemented

### Account Types
1. **Assets** - Resources owned (debit increases, credit decreases)
2. **Liabilities** - Amounts owed (credit increases, debit decreases)
3. **Equity** - Owner's interest (credit increases, debit decreases)
4. **Revenue** - Income earned (credit increases, debit decreases)
5. **Expenses** - Costs incurred (debit increases, credit decreases)

### Fundamental Equation
```
Assets = Liabilities + Equity + (Revenue - Expenses)
```

### Double-Entry Rules
- Every transaction affects at least two accounts
- Total Debits = Total Credits (for each journal entry)
- Debits are always on the left, Credits on the right

## Database Schema

### Tables

#### 1. accounts
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| code | VARCHAR(20) | Account code (e.g., 1000, 1100) |
| name | VARCHAR(100) | Account name |
| account_type | ENUM | asset, liability, equity, revenue, expense |
| parent_id | UUID | FK to accounts (for sub-accounts) |
| is_active | BOOLEAN | Whether account is active |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

#### 2. journal_entries
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| entry_number | VARCHAR(20) | Auto-generated sequential number |
| date | DATE | Transaction date |
| description | VARCHAR(255) | Entry description |
| reference | VARCHAR(50) | External reference number |
| created_at | TIMESTAMP | Creation timestamp |
| posted_at | TIMESTAMP | When entry was posted |

#### 3. line_items
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| journal_entry_id | UUID | FK to journal_entries |
| account_id | UUID | FK to accounts |
| debit | DECIMAL(15,2) | Debit amount |
| credit | DECIMAL(15,2) | Credit amount |
| memo | VARCHAR(255) | Line item description |

## API Endpoints

### Accounts API
- `GET /api/accounts` - List all accounts
- `GET /api/accounts/{id}` - Get account details
- `POST /api/accounts` - Create account
- `PUT /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Deactivate account
- `GET /api/accounts/{id}/ledger` - Get account ledger (transactions)

### Journal Entries API
- `GET /api/journal-entries` - List entries (with pagination, date filter)
- `GET /api/journal-entries/{id}` - Get entry with line items
- `POST /api/journal-entries` - Create new entry
- `PUT /api/journal-entries/{id}` - Update entry (if not posted)
- `DELETE /api/journal-entries/{id}` - Delete entry (if not posted)
- `POST /api/journal-entries/{id}/post` - Post an entry

### Reports API
- `GET /api/reports/trial-balance` - Trial Balance (all accounts with balances)
- `GET /api/reports/balance-sheet` - Balance Sheet report
- `GET /api/reports/income-statement` - Income Statement report
- `GET /api/reports/general-ledger` - General Ledger with all accounts
- `GET /api/reports/account-ledger/{id}` - Specific account ledger

## Web Interface Pages

### 1. Dashboard (`/`)
- Summary cards: Total Assets, Total Liabilities, Total Equity, Net Income
- Recent journal entries list
- Quick action buttons

### 2. Chart of Accounts (`/accounts`)
- Hierarchical list of all accounts
- Account type indicators with color coding
- Add/Edit/Delete account modals
- Search and filter functionality

### 3. Journal Entries (`/journal`)
- Sortable table of all entries
- Date range filter
- Status indicators (draft/posted)
- Create new entry button
- Entry detail view modal

### 4. Financial Reports (`/reports`)
- Report type selector
- Date range selector
- Generate report button
- Printable report view
- Export options (print)

### 5. Create/Edit Journal Entry (`/journal/new`, `/journal/{id}/edit`)
- Date picker
- Description field
- Dynamic line items (add/remove rows)
- Account selector with search
- Debit/Credit inputs with auto-balance indicator
- Validation: Total debits must equal total credits

## Financial Report Formulas

### Trial Balance
```
For each account:
  Debit Balance = SUM(debits) - SUM(credits) if normal balance is debit
  Credit Balance = SUM(credits) - SUM(debits) if normal balance is credit
```

### Balance Sheet (as of date)
```
ASSETS
  Current Assets: Cash, Accounts Receivable, Inventory, etc.
  Fixed Assets: Property, Equipment, etc.
  Total Assets

LIABILITIES
  Current Liabilities: Accounts Payable, etc.
  Long-term Liabilities: Loans, etc.
  Total Liabilities

EQUITY
  Owner's Capital
  Retained Earnings
  Net Income (Revenue - Expenses)
  Total Equity

Total Liabilities + Equity
```

### Income Statement (period)
```
REVENUE
  Service Revenue
  Product Sales
  Total Revenue

EXPENSES
  Operating Expenses
  Salaries
  Rent
  Utilities
  Total Expenses

NET INCOME = Total Revenue - Total Expenses
```

## Acceptance Criteria

### Core Functionality
- [ ] Can create accounts of all 5 types
- [ ] Can create journal entries with multiple line items
- [ ] System validates that total debits = total credits
- [ ] Can post/unpost journal entries
- [ ] Account balances update correctly with transactions

### Reports
- [ ] Trial Balance shows all accounts with correct balances
- [ ] Balance Sheet shows assets = liabilities + equity
- [ ] Income Statement calculates net income correctly
- [ ] Reports filter by date range

### Data Integrity
- [ ] Cannot delete posted entries
- [ ] Cannot modify posted entries without unposting first
- [ ] All monetary values stored with 2 decimal precision
- [ ] Proper decimal handling for calculations

### UI/UX
- [ ] Responsive design works on desktop and tablet
- [ ] Form validation with clear error messages
- [ ] Loading states for async operations
- [ ] Confirmation dialogs for destructive actions

## Project Structure

```
F:\PythonProjs\myodoo\
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database connection
│   ├── models/
│   │   ├── __init__.py
│   │   ├── account.py       # Account model
│   │   ├── journal_entry.py # JournalEntry and LineItem models
│   │   └── enums.py         # AccountType enum
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── account.py       # Account Pydantic schemas
│   │   ├── journal_entry.py # JournalEntry schemas
│   │   └── reports.py       # Report schemas
│   ├── api/
│   │   ├── __init__.py
│   │   ├── accounts.py      # Account endpoints
│   │   ├── journal_entries.py # Journal endpoints
│   │   └── reports.py       # Report endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── account_service.py
│   │   ├── journal_service.py
│   │   └── report_service.py
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── accounts.html
│       ├── journal.html
│       ├── journal_form.html
│       └── reports.html
├── config.py                # Configuration
├── requirements.txt
├── run.py                   # Application runner
└── SPEC.md
```
