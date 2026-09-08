import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services import sheets_service


class TestSheetsService:
    def test_extract_spreadsheet_id_valid(self):
        url = "https://docs.google.com/spreadsheets/d/1rtJiUWmv8GctYoSrRpBG1os6cowFcLe8SXae6WfUSSI/edit"
        assert sheets_service.extract_spreadsheet_id(url) == "1rtJiUWmv8GctYoSrRpBG1os6cowFcLe8SXae6WfUSSI"

    def test_extract_spreadsheet_id_invalid(self):
        assert sheets_service.extract_spreadsheet_id("https://example.com") is None
        assert sheets_service.extract_spreadsheet_id("not a url") is None

    def test_is_google_sheets_url(self):
        assert sheets_service.is_google_sheets_url("https://docs.google.com/spreadsheets/d/ABC123/edit")
        assert not sheets_service.is_google_sheets_url("https://sheets.google.com/abc")
        assert not sheets_service.is_google_sheets_url("http://example.com")

    def test_normalize_header(self):
        assert sheets_service._normalize_header("Name") == "name"
        assert sheets_service._normalize_header("Student Name") == "student name"
        assert sheets_service._normalize_header("REGISTRATION NUMBER") == "registration number"
        assert sheets_service._normalize_header("Registration No.") == "registration no"
        assert sheets_service._normalize_header("E-mail") == "e mail"

    def test_detect_columns_auto(self):
        headers = ["Name", "Registration Number", "Email"]
        mapping = sheets_service.detect_columns(headers)
        assert mapping["name"] == 0
        assert mapping["registration_number"] == 1
        assert mapping["email"] == 2

    def test_detect_columns_aliases(self):
        headers = ["Full Name", "Roll No", "Student Email"]
        mapping = sheets_service.detect_columns(headers)
        assert mapping["name"] == 0
        assert mapping["registration_number"] == 1
        assert mapping["email"] == 2

    def test_detect_columns_missing(self):
        headers = ["Name", "Phone"]
        mapping = sheets_service.detect_columns(headers)
        assert mapping["name"] == 0
        assert mapping["registration_number"] is None
        assert mapping["email"] is None

    def test_validate_row_valid(self):
        existing_rolls = set()
        existing_emails = set()
        seen_rolls = set()
        seen_emails = set()
        row = ["Rahul Kumar", "23CS001", "rahul@gmail.com"]
        col_map = {"name": 0, "registration_number": 1, "email": 2}
        result = sheets_service.validate_row(
            row, col_map, 2, seen_rolls, seen_emails, existing_rolls, existing_emails
        )
        assert result["valid"] is True
        assert result["status"] == "Ready"
        assert result["name"] == "Rahul Kumar"
        assert result["registration_number"] == "23CS001"
        assert result["email"] == "rahul@gmail.com"

    def test_validate_row_missing_name(self):
        existing_rolls = set()
        existing_emails = set()
        seen_rolls = set()
        seen_emails = set()
        row = ["", "23CS001", "rahul@gmail.com"]
        col_map = {"name": 0, "registration_number": 1, "email": 2}
        result = sheets_service.validate_row(
            row, col_map, 2, seen_rolls, seen_emails, existing_rolls, existing_emails
        )
        assert result["valid"] is False
        assert "Missing name" in result["status"]

    def test_validate_row_invalid_email(self):
        existing_rolls = set()
        existing_emails = set()
        seen_rolls = set()
        seen_emails = set()
        row = ["Rahul", "23CS001", "not-an-email"]
        col_map = {"name": 0, "registration_number": 1, "email": 2}
        result = sheets_service.validate_row(
            row, col_map, 2, seen_rolls, seen_emails, existing_rolls, existing_emails
        )
        assert result["valid"] is False
        assert "Invalid email" in result["status"]

    def test_validate_row_duplicate_roll_in_db(self):
        existing_rolls = {"23CS001"}
        existing_emails = set()
        seen_rolls = set()
        seen_emails = set()
        row = ["Rahul", "23CS001", "rahul@gmail.com"]
        col_map = {"name": 0, "registration_number": 1, "email": 2}
        result = sheets_service.validate_row(
            row, col_map, 2, seen_rolls, seen_emails, existing_rolls, existing_emails
        )
        assert result["valid"] is False
        assert "Duplicate registration number" in result["status"]

    def test_validate_row_duplicate_roll_in_sheet(self):
        existing_rolls = set()
        existing_emails = set()
        seen_rolls = {"23CS001"}
        seen_emails = set()
        row = ["Priya", "23CS001", "priya@gmail.com"]
        col_map = {"name": 0, "registration_number": 1, "email": 2}
        result = sheets_service.validate_row(
            row, col_map, 3, seen_rolls, seen_emails, existing_rolls, existing_emails
        )
        assert result["valid"] is False
        assert "Duplicate registration number in sheet" in result["status"]

    def test_validate_row_duplicate_email_in_db(self):
        existing_rolls = set()
        existing_emails = {"rahul@gmail.com"}
        seen_rolls = set()
        seen_emails = set()
        row = ["Priya", "23CS002", "rahul@gmail.com"]
        col_map = {"name": 0, "registration_number": 1, "email": 2}
        result = sheets_service.validate_row(
            row, col_map, 2, seen_rolls, seen_emails, existing_rolls, existing_emails
        )
        assert result["valid"] is False
        assert "Duplicate email" in result["status"]

    def test_validate_row_preserves_leading_zeros(self):
        existing_rolls = set()
        existing_emails = set()
        seen_rolls = set()
        seen_emails = set()
        row = ["Amit", "00123", "amit@gmail.com"]
        col_map = {"name": 0, "registration_number": 1, "email": 2}
        result = sheets_service.validate_row(
            row, col_map, 2, seen_rolls, seen_emails, existing_rolls, existing_emails
        )
        assert result["valid"] is True
        assert result["registration_number"] == "00123"

    def test_validate_row_complex_roll_formats(self):
        existing_rolls = set()
        existing_emails = set()
        seen_rolls = set()
        seen_emails = set()
        for roll in ["23CS001", "CSE-2026-001", "00123", "ROLL-001"]:
            row = ["Student", roll, f"{roll.lower()}@example.com"]
            col_map = {"name": 0, "registration_number": 1, "email": 2}
            result = sheets_service.validate_row(
                row, col_map, 2, seen_rolls, seen_emails, existing_rolls, existing_emails
            )
            assert result["valid"] is True, f"Failed for roll: {roll}"
            assert result["registration_number"] == roll

    def test_parse_rows_skips_empty(self):
        existing_rolls = set()
        existing_emails = set()
        headers = ["Name", "Reg", "Email"]
        rows = [
            ["A", "1", "a@a.com"],
            ["", "", ""],
            ["B", "2", "b@b.com"],
        ]
        col_map = {"name": 0, "registration_number": 1, "email": 2}
        results = sheets_service.parse_rows(headers, rows, col_map, existing_rolls, existing_emails)
        assert len(results) == 2
        assert results[0]["name"] == "A"
        assert results[1]["name"] == "B"

    def test_parse_rows_max_limit(self):
        existing_rolls = set()
        existing_emails = set()
        headers = ["Name", "Reg", "Email"]
        rows = [[f"S{i}", str(i), f"s{i}@x.com"] for i in range(2500)]
        col_map = {"name": 0, "registration_number": 1, "email": 2}
        results = sheets_service.parse_rows(headers, rows, col_map, existing_rolls, existing_emails)
        assert len(results) == sheets_service.MAX_ROWS


class TestSheetsServiceFetch:
    @patch("app.services.sheets_service._fetch_public_csv")
    def test_fetch_public_csv_success(self, mock_fetch):
        mock_fetch.return_value = ("Title", "Sheet1", ["Name", "Reg", "Email"], [["A", "1", "a@a.com"]])
        title, sheet, headers, rows = sheets_service.fetch_sheet_data("ABC123")
        assert title == "Title"
        assert sheet == "Sheet1"
        assert headers == ["Name", "Reg", "Email"]

    @patch("app.services.sheets_service._fetch_via_gspread")
    @patch("app.services.sheets_service._fetch_public_csv")
    def test_fetch_fallback_to_public(self, mock_public, mock_gspread):
        mock_gspread.side_effect = Exception("gspread failed")
        mock_public.return_value = ("Title", "Sheet1", ["Name"], [["A"]])
        title, sheet, headers, rows = sheets_service.fetch_sheet_data("ABC123")
        assert title == "Title"

    @patch("app.services.sheets_service._fetch_public_csv")
    def test_fetch_permission_error_private_sheet(self, mock_fetch):
        mock_fetch.side_effect = PermissionError("not accessible")
        with pytest.raises(PermissionError):
            sheets_service.fetch_sheet_data("ABC123")


class TestSheetsServiceIntegration:
    @pytest.mark.asyncio
    async def test_full_flow_valid_sheet(self):
        headers = ["Name", "Registration Number", "Email"]
        rows = [
            ["Rahul Kumar", "23CS001", "rahul@gmail.com"],
            ["Priya Das", "23CS002", "priya@gmail.com"],
            ["Amit Sharma", "23CS003", "amit@gmail.com"],
        ]
        existing_rolls = set()
        existing_emails = set()
        col_map = sheets_service.detect_columns(headers)
        preview = sheets_service.parse_rows(headers, rows, col_map, existing_rolls, existing_emails)
        assert len(preview) == 3
        assert all(r["valid"] for r in preview)
        assert all(r["status"] == "Ready" for r in preview)

    @pytest.mark.asyncio
    async def test_full_flow_with_duplicates(self):
        headers = ["Name", "Registration Number", "Email"]
        rows = [
            ["Rahul", "23CS001", "rahul@gmail.com"],
            ["Priya", "23CS001", "priya@gmail.com"],
            ["Amit", "23CS003", "rahul@gmail.com"],
        ]
        existing_rolls = {"23CS001"}
        existing_emails = {"rahul@gmail.com"}
        col_map = sheets_service.detect_columns(headers)
        preview = sheets_service.parse_rows(headers, rows, col_map, existing_rolls, existing_emails)
        assert len(preview) == 3
        assert preview[0]["valid"] is False
        assert "Duplicate" in preview[0]["status"]
        assert preview[1]["valid"] is False
        assert "Duplicate" in preview[1]["status"]
        assert preview[2]["valid"] is False
        assert "Duplicate" in preview[2]["status"]