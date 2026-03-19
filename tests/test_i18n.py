import pytest


class TestI18nFrontend:
    def test_i18n_object_structure(self):
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        assert 'const i18n' in html
        assert 'vi:' in html
        assert 'en:' in html

        assert 'dashboard:' in html
        assert 'accounts:' in html
        assert 'journal:' in html
        assert 'reports:' in html

        assert 'Bảng điều khiển' in html
        assert 'Tài khoản' in html
        assert 'Nhật ký' in html
        assert 'Báo cáo' in html

        assert 'Dashboard' in html
        assert 'Accounts' in html
        assert 'Journal' in html
        assert 'Reports' in html

    def test_language_buttons_present(self):
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        assert 'id="lang-vi"' in html
        assert 'id="lang-en"' in html

    def test_translation_function_exists(self):
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        assert 'function t(key)' in html
        assert 'localStorage' in html

    def test_all_translations_complete(self):
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        vi_keys = ['dashboard', 'accounts', 'journal', 'reports', 'totalAssets',
                   'totalLiabilities', 'totalEquity', 'recentEntries', 'date',
                   'entryNumber', 'description', 'status', 'posted', 'draft',
                   'noEntries', 'accountList', 'code', 'name', 'type',
                   'journalEntries', 'reference', 'financialReports',
                   'balanceSheet', 'trialBalance', 'assets', 'liabilities',
                   'equity', 'total', 'debit', 'credit', 'totalDebits',
                   'totalCredits', 'balanced', 'notBalanced', 'error']

        for key in vi_keys:
            assert f'{key}:' in html, f"Missing translation key: {key}"


class TestI18nTranslations:
    def test_all_required_keys_present(self):
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        required_keys = [
            'dashboard', 'accounts', 'journal', 'reports',
            'totalAssets', 'totalLiabilities', 'totalEquity',
            'recentEntries', 'date', 'entryNumber', 'description',
            'status', 'posted', 'draft', 'noEntries',
            'accountList', 'code', 'name', 'type',
            'journalEntries', 'reference', 'financialReports',
            'balanceSheet', 'trialBalance', 'assets',
            'liabilities', 'equity', 'total',
            'debit', 'credit', 'totalDebits', 'totalCredits',
            'balanced', 'notBalanced', 'error'
        ]

        for key in required_keys:
            assert f'{key}:' in html, f"Missing translation key: {key}"

    def test_vietnamese_defaults(self):
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        assert 'lang="vi"' in html
        assert "localStorage.getItem('lang') || 'vi'" in html

    def test_both_languages_have_same_keys(self):
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        vi_count = html.count("vi: {")
        en_count = html.count("en: {")

        assert vi_count >= 1, "Should have Vietnamese translations"
        assert en_count >= 1, "Should have English translations"
