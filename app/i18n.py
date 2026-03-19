from enum import Enum


class Language(str, Enum):
    EN = "en"
    VI = "vi"


TRANSLATIONS = {
    "en": {
        # Navigation
        "app_name": "Thuan's LedgerPro",
        "dashboard": "Dashboard",
        "accounts": "Chart of Accounts",
        "journal": "Journal Entries",
        "reports": "Financial Reports",
        
        # Dashboard
        "total_assets": "Total Assets",
        "total_liabilities": "Total Liabilities",
        "total_equity": "Total Equity",
        "net_income": "Net Income",
        "recent_entries": "Recent Journal Entries",
        "account_summary": "Account Summary",
        "view_all": "View All Entries",
        "loading": "Loading...",
        "no_entries": "No entries yet",
        
        # Accounts
        "add_account": "Add Account",
        "edit_account": "Edit Account",
        "account_code": "Account Code",
        "account_name": "Account Name",
        "account_type": "Account Type",
        "balance": "Balance",
        "status": "Status",
        "actions": "Actions",
        "active": "Active",
        "inactive": "Inactive",
        "parent_account": "Parent Account",
        "none": "None",
        "all_types": "All Types",
        "search_accounts": "Search accounts...",
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "deactivate": "Deactivate",
        
        # Account Types
        "asset": "Asset",
        "liability": "Liability",
        "equity": "Equity",
        "revenue": "Revenue",
        "expense": "Expense",
        
        # Journal Entries
        "new_entry": "New Entry",
        "entry_number": "Entry #",
        "date": "Date",
        "description": "Description",
        "reference": "Reference",
        "debit": "Debit",
        "credit": "Credit",
        "amount": "Amount",
        "posted": "Posted",
        "draft": "Draft",
        "all": "All",
        "start_date": "Start Date",
        "end_date": "End Date",
        "line_items": "Line Items",
        "memo": "Memo",
        "total_debits": "Total Debits",
        "total_credits": "Total Credits",
        "difference": "Difference",
        "save_draft": "Save as Draft",
        "save_and_post": "Save and Post",
        "post": "Post",
        "unpost": "Unpost",
        "add_line": "Add Line",
        "select_account": "Select account...",
        "optional_memo": "Optional memo",
        "at_least_2_lines": "At least 2 line items required",
        "must_be_balanced": "Entry must be balanced",
        
        # Reports
        "trial_balance": "Trial Balance",
        "balance_sheet": "Balance Sheet",
        "income_statement": "Income Statement",
        "general_ledger": "General Ledger",
        "account_ledger": "Account Ledger",
        "as_of_date": "As of Date",
        "for_period": "For the period",
        "to": "to",
        "generate_report": "Generate Report",
        "balanced": "Balanced",
        "unbalanced": "Unbalanced",
        "totals": "Totals",
        "opening_balance": "Opening Balance",
        "closing_balance": "Closing Balance",
        "gross_profit": "Gross Profit",
        
        # Balance Sheet
        "assets": "Assets",
        "liabilities": "Liabilities",
        "total_liabilities_equity": "Total Liabilities + Equity",
        "net_income_current": "Net Income (Current Period)",
        
        # Messages
        "confirm_delete": "Are you sure you want to deactivate this account?",
        "confirm_action": "Confirm Action",
        "account_saved": "Account saved successfully",
        "account_deleted": "Account deactivated",
        "entry_saved": "Entry saved as draft",
        "entry_posted": "Entry saved and posted",
        "entry_deleted": "Entry deleted",
        "error": "Error",
        "success": "Success",
        "warning": "Warning",
        "entries_count": "{count} accounts",
        
        # Footer
        "print": "Print",
        "close": "Close",
    },
    "vi": {
        # Navigation
        "app_name": "Thuan's LedgerPro",
        "dashboard": "Bảng điều khiển",
        "accounts": "Danh sách Tài khoản",
        "journal": "Sổ Nhật ký",
        "reports": "Báo cáo Tài chính",
        
        # Dashboard
        "total_assets": "Tổng Tài sản",
        "total_liabilities": "Tổng Nợ phải trả",
        "total_equity": "Tổng Vốn chủ sở hữu",
        "net_income": "Lợi nhuận ròng",
        "recent_entries": "Các Phiếu gần đây",
        "account_summary": "Tóm tắt Tài khoản",
        "view_all": "Xem tất cả",
        "loading": "Đang tải...",
        "no_entries": "Chưa có phiếu nào",
        
        # Accounts
        "add_account": "Thêm Tài khoản",
        "edit_account": "Sửa Tài khoản",
        "account_code": "Mã Tài khoản",
        "account_name": "Tên Tài khoản",
        "account_type": "Loại Tài khoản",
        "balance": "Số dư",
        "status": "Trạng thái",
        "actions": "Thao tác",
        "active": "Hoạt động",
        "inactive": "Không hoạt động",
        "parent_account": "Tài khoản cha",
        "none": "Không có",
        "all_types": "Tất cả loại",
        "search_accounts": "Tìm kiếm tài khoản...",
        "save": "Lưu",
        "cancel": "Hủy",
        "delete": "Xóa",
        "deactivate": "Hủy kích hoạt",
        
        # Account Types
        "asset": "Tài sản",
        "liability": "Nợ phải trả",
        "equity": "Vốn chủ sở hữu",
        "revenue": "Doanh thu",
        "expense": "Chi phí",
        
        # Journal Entries
        "new_entry": "Phiếu mới",
        "entry_number": "Số Phiếu",
        "date": "Ngày",
        "description": "Mô tả",
        "reference": "Tham chiếu",
        "debit": "Nợ",
        "credit": "Có",
        "amount": "Số tiền",
        "posted": "Đã ghi",
        "draft": "Nháp",
        "all": "Tất cả",
        "start_date": "Ngày bắt đầu",
        "end_date": "Ngày kết thúc",
        "line_items": "Dòng Phiếu",
        "memo": "Ghi chú",
        "total_debits": "Tổng Nợ",
        "total_credits": "Tổng Có",
        "difference": "Chênh lệch",
        "save_draft": "Lưu nháp",
        "save_and_post": "Lưu và Ghi",
        "post": "Ghi",
        "unpost": "Bỏ ghi",
        "add_line": "Thêm dòng",
        "select_account": "Chọn tài khoản...",
        "optional_memo": "Ghi chú tùy chọn",
        "at_least_2_lines": "Cần ít nhất 2 dòng phiếu",
        "must_be_balanced": "Phiếu phải cân bằng",
        
        # Reports
        "trial_balance": "Bảng Cân đối Tài khoản",
        "balance_sheet": "Bảng Cân đối Kế toán",
        "income_statement": "Báo cáo Thu nhập",
        "general_ledger": "Sổ Cái",
        "account_ledger": "Sổ Tài khoản",
        "as_of_date": "Tính đến ngày",
        "for_period": "Cho giai đoạn",
        "to": "đến",
        "generate_report": "Tạo Báo cáo",
        "balanced": "Cân bằng",
        "unbalanced": "Không cân bằng",
        "totals": "Tổng cộng",
        "opening_balance": "Số dư đầu kỳ",
        "closing_balance": "Số dư cuối kỳ",
        "gross_profit": "Lợi nhuận gộp",
        
        # Balance Sheet
        "assets": "Tài sản",
        "liabilities": "Nợ phải trả",
        "total_liabilities_equity": "Tổng Nợ + Vốn",
        "net_income_current": "Lợi nhuận (Kỳ hiện tại)",
        
        # Messages
        "confirm_delete": "Bạn có chắc muốn hủy kích hoạt tài khoản này?",
        "confirm_action": "Xác nhận Thao tác",
        "account_saved": "Tài khoản đã lưu thành công",
        "account_deleted": "Tài khoản đã hủy kích hoạt",
        "entry_saved": "Phiếu đã lưu nháp",
        "entry_posted": "Phiếu đã lưu và ghi",
        "entry_deleted": "Phiếu đã xóa",
        "error": "Lỗi",
        "success": "Thành công",
        "warning": "Cảnh báo",
        "entries_count": "{count} tài khoản",
        
        # Footer
        "print": "In",
        "close": "Đóng",
    }
}


def get_translations(lang: str) -> dict:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])


def t(key: str, lang: str = "en", **kwargs) -> str:
    translations = get_translations(lang)
    text = translations.get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
