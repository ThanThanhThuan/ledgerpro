import pytest


class TestHealthEndpoints:
    def test_health(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'

    def test_test_endpoint(self, client):
        response = client.get('/api/test')
        assert response.status_code == 200
        data = response.get_json()
        assert 'db_set' in data
        assert 'path' in data


class TestAccountEndpoints:
    def test_get_accounts_empty(self, client, monkeypatch):

        class MockResult:
            def __iter__(self):
                return iter([])

        class MockConn:
            def execute(self, *args, **kwargs):
                return MockResult()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class MockEngine:
            def connect(self):
                return MockConn()

        monkeypatch.setattr('api.index.get_engine', lambda: MockEngine())

        response = client.get('/api/accounts')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_accounts_structure(self, client, monkeypatch):

        class MockRow:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, key):
                return self._data[key]

            def __iter__(self):
                return iter(self._data)

            def __len__(self):
                return len(self._data)

        mock_accounts = [
            MockRow(['1', '1000', 'Cash', 'asset', True]),
            MockRow(['2', '2000', 'Accounts Payable', 'liability', True]),
        ]

        class MockResult:
            def __init__(self, rows):
                self._rows = rows

            def __iter__(self):
                return iter(self._rows)

        class MockConn:
            def execute(self, query, params=None):
                return MockResult(mock_accounts)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class MockEngine:
            def connect(self):
                return MockConn()

        monkeypatch.setattr('api.index.get_engine', lambda: MockEngine())

        response = client.get('/api/accounts')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert data[0]['code'] == '1000'
        assert data[0]['name'] == 'Cash'
        assert data[0]['account_type'] == 'asset'


class TestJournalEndpoints:
    def test_get_journal_entries_structure(self, client, monkeypatch):
        from datetime import datetime

        class MockRow:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, key):
                return self._data[key]

            def __iter__(self):
                return iter(self._data)

        mock_entries = [
            MockRow(['1', 'JE-001', '2024-01-15', 'Test entry', 'REF-001', datetime.now()]),
        ]

        class MockResult:
            def __init__(self, rows):
                self._rows = rows

            def __iter__(self):
                return iter(self._rows)

        class MockConn:
            def execute(self, query, params=None):
                return MockResult(mock_entries)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class MockEngine:
            def connect(self):
                return MockConn()

        monkeypatch.setattr('api.index.get_engine', lambda: MockEngine())

        response = client.get('/api/journal-entries')
        assert response.status_code == 200
        data = response.get_json()
        assert 'entries' in data
        assert 'total' in data
        assert len(data['entries']) == 1
        assert data['entries'][0]['entry_number'] == 'JE-001'
        assert data['entries'][0]['is_posted'] == True


class TestReportEndpoints:
    def test_balance_sheet_structure(self, client, monkeypatch):

        class MockRow:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, key):
                return self._data[key]

            def __iter__(self):
                return iter(self._data)

        class MockBalanceResult:
            def __init__(self, dr, cr):
                self._dr = dr
                self._cr = cr

            def fetchone(self):
                return (self._dr, self._cr)

        class MockResult:
            def __init__(self, rows):
                self._rows = rows

            def __iter__(self):
                return iter(self._rows)

        class MockConn:
            def __init__(self):
                self.call_count = 0

            def execute(self, query, params=None):
                self.call_count += 1
                if self.call_count == 1:
                    return MockResult([
                        MockRow(['1', '1000', 'Cash', 'asset']),
                        MockRow(['2', '2000', 'Accounts Payable', 'liability']),
                    ])
                return MockBalanceResult(1000, 0)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class MockEngine:
            def connect(self):
                return MockConn()

        monkeypatch.setattr('api.index.get_engine', lambda: MockEngine())

        response = client.get('/api/reports/balance-sheet')
        assert response.status_code == 200
        data = response.get_json()
        assert 'assets' in data
        assert 'liabilities' in data
        assert 'equity' in data
        assert 'is_balanced' in data
        assert isinstance(data['assets'], dict)
        assert 'accounts' in data['assets']
        assert 'total' in data['assets']

    def test_trial_balance_structure(self, client, monkeypatch):

        class MockRow:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, key):
                return self._data[key]

            def __iter__(self):
                return iter(self._data)

        class MockBalanceResult:
            def fetchone(self):
                return (5000, 0)

        class MockResult:
            def __init__(self, rows):
                self._rows = rows

            def __iter__(self):
                return iter(self._rows)

        class MockConn:
            def __init__(self):
                self.call_count = 0

            def execute(self, query, params=None):
                self.call_count += 1
                if self.call_count == 1:
                    return MockResult([
                        MockRow(['1', '1000', 'Cash', 'asset']),
                    ])
                return MockBalanceResult()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class MockEngine:
            def connect(self):
                return MockConn()

        monkeypatch.setattr('api.index.get_engine', lambda: MockEngine())

        response = client.get('/api/reports/trial-balance')
        assert response.status_code == 200
        data = response.get_json()
        assert 'accounts' in data
        assert 'total_debits' in data
        assert 'total_credits' in data
        assert 'is_balanced' in data


class TestDoubleEntryValidation:
    def test_debit_credit_balance(self, client, monkeypatch):

        class MockRow:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, key):
                return self._data[key]

            def __iter__(self):
                return iter(self._data)

        class MockBalanceResult:
            def fetchone(self):
                return (1000, 1000)

        class MockResult:
            def __init__(self, rows):
                self._rows = rows

            def __iter__(self):
                return iter(self._rows)

        class MockConn:
            def __init__(self):
                self.call_count = 0

            def execute(self, query, params=None):
                self.call_count += 1
                if self.call_count == 1:
                    return MockResult([
                        MockRow(['1', '1000', 'Cash', 'asset']),
                    ])
                return MockBalanceResult()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class MockEngine:
            def connect(self):
                return MockConn()

        monkeypatch.setattr('api.index.get_engine', lambda: MockEngine())

        response = client.get('/api/reports/trial-balance')
        data = response.get_json()
        assert data['is_balanced'] == True


class TestIndexRoute:
    def test_index_returns_html(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')
        html = response.data.decode('utf-8')
        assert 'LedgerPro' in html
        assert 'i18n' in html
