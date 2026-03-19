-- LedgerPro Database Setup Script
-- Run this script in PostgreSQL to create the database

-- Create database
-- CREATE DATABASE ledgerpro;

-- Connect to the database and run the following

-- Create ENUM type for account_type
DO $$ BEGIN
    CREATE TYPE account_type AS ENUM ('asset', 'liability', 'equity', 'revenue', 'expense');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    account_type account_type NOT NULL,
    parent_id UUID REFERENCES accounts(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create journal_entries table
CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_number VARCHAR(20) UNIQUE NOT NULL,
    date DATE NOT NULL,
    description VARCHAR(255) NOT NULL,
    reference VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMP
);

-- Create line_items table
CREATE TABLE IF NOT EXISTS line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id UUID REFERENCES accounts(id),
    debit NUMERIC(15, 2) DEFAULT 0.00,
    credit NUMERIC(15, 2) DEFAULT 0.00,
    memo VARCHAR(255)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_accounts_code ON accounts(code);
CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(date);
CREATE INDEX IF NOT EXISTS idx_journal_number ON journal_entries(entry_number);
CREATE INDEX IF NOT EXISTS idx_line_items_account ON line_items(account_id);
CREATE INDEX IF NOT EXISTS idx_line_items_entry ON line_items(journal_entry_id);

-- Insert sample chart of accounts
INSERT INTO accounts (code, name, account_type) VALUES
    -- Assets
    ('1000', 'Cash', 'asset'),
    ('1100', 'Accounts Receivable', 'asset'),
    ('1200', 'Inventory', 'asset'),
    ('1500', 'Equipment', 'asset'),
    ('1510', 'Accumulated Depreciation - Equipment', 'asset'),
    ('1600', 'Land', 'asset'),
    ('1700', 'Buildings', 'asset'),
    ('1710', 'Accumulated Depreciation - Buildings', 'asset'),
    -- Liabilities
    ('2000', 'Accounts Payable', 'liability'),
    ('2100', 'Notes Payable', 'liability'),
    ('2200', 'Salaries Payable', 'liability'),
    ('2300', 'Interest Payable', 'liability'),
    ('2400', 'Income Tax Payable', 'liability'),
    -- Equity
    ('3000', 'Owner''s Capital', 'equity'),
    ('3100', 'Owner''s Drawings', 'equity'),
    ('3200', 'Retained Earnings', 'equity'),
    -- Revenue
    ('4000', 'Sales Revenue', 'revenue'),
    ('4100', 'Service Revenue', 'revenue'),
    ('4200', 'Interest Revenue', 'revenue'),
    ('4300', 'Other Income', 'revenue'),
    -- Expenses
    ('5000', 'Cost of Goods Sold', 'expense'),
    ('5100', 'Salaries Expense', 'expense'),
    ('5200', 'Rent Expense', 'expense'),
    ('5300', 'Utilities Expense', 'expense'),
    ('5400', 'Depreciation Expense', 'expense'),
    ('5500', 'Insurance Expense', 'expense'),
    ('5600', 'Supplies Expense', 'expense'),
    ('5700', 'Interest Expense', 'expense'),
    ('5800', 'Income Tax Expense', 'expense'),
    ('5900', 'Other Expenses', 'expense')
ON CONFLICT (code) DO NOTHING;
