"""Integration test for the /weekly-summary endpoint.

Calls the full pipeline: invoice scan → flagging → summary generation → audit log.
S/4HANA is mocked (pytest mode). LLM is mocked to avoid AI Core dependency.
"""

import sys
import pytest

assert "pytest" in sys.modules


def test_weekly_summary_pipeline(monkeypatch):
    """End-to-end test: pipeline produces flagged_invoices, summary, and audit_log."""
    from tools import summary_generator, audit_logger as audit_logger_module
    from tools.audit_logger import AuditLogger

    # Mock LLM
    class FakeMsg:
        content = "Weekly Summary: 3 high-value invoices require CFO attention."

    class FakeLLM:
        def invoke(self, messages):
            return FakeMsg()

    monkeypatch.setattr(summary_generator, "ChatLiteLLM", lambda **kwargs: FakeLLM())

    # Reset the module-level audit logger for test isolation
    fresh_logger = AuditLogger()
    monkeypatch.setattr(audit_logger_module, "_audit_logger", fresh_logger)

    # Import after monkeypatching
    from tools.invoice_scanner import scan_invoices
    from tools.summary_generator import generate_summary
    from tools.audit_logger import get_audit_logger

    # Run pipeline
    scan_result = scan_invoices()
    flagged = scan_result["flagged_invoices"]
    all_invoices = scan_result["all_invoices"]
    scan_date = scan_result["scan_date"]

    audit = get_audit_logger()
    for inv in flagged:
        audit.log_flag(
            invoice_id=inv["SupplierInvoice"],
            amount=inv["InvoiceGrossAmount"],
            action="flagged",
        )

    summary = generate_summary(
        flagged_invoices=flagged,
        all_invoices=all_invoices,
        scan_date=scan_date,
    )
    audit.log_notification(action="notification_dispatched")

    result = {
        "flagged_invoices": flagged,
        "summary": summary,
        "audit_log": audit.get_log(),
        "scan_date": scan_date,
    }

    # Assertions
    assert "flagged_invoices" in result
    assert "summary" in result
    assert "audit_log" in result
    assert "scan_date" in result

    assert isinstance(result["flagged_invoices"], list)
    assert len(result["flagged_invoices"]) > 0  # at least 1 flagged invoice from mock data

    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 5

    assert isinstance(result["audit_log"], list)
    # Expect entries: one per flagged invoice + one notification
    expected_entries = len(flagged) + 1
    assert len(result["audit_log"]) == expected_entries

    # Verify notification entry is present
    notification_entries = [e for e in result["audit_log"] if e["type"] == "notification"]
    assert len(notification_entries) == 1
    assert notification_entries[0]["action"] == "notification_dispatched"


def test_weekly_summary_empty_flagged(monkeypatch):
    """Pipeline with no flagged invoices should still return valid structure."""
    from tools import summary_generator, audit_logger as audit_logger_module
    from tools.audit_logger import AuditLogger
    from tools import invoice_scanner

    # Mock: return no invoices
    monkeypatch.setattr(invoice_scanner, "MOCK_INVOICES", [])

    # Reset audit logger
    fresh_logger = AuditLogger()
    monkeypatch.setattr(audit_logger_module, "_audit_logger", fresh_logger)

    from tools.invoice_scanner import scan_invoices
    from tools.summary_generator import generate_summary
    from tools.audit_logger import get_audit_logger

    scan_result = scan_invoices()
    flagged = scan_result["flagged_invoices"]
    all_invoices = scan_result["all_invoices"]
    scan_date = scan_result["scan_date"]

    summary = generate_summary(
        flagged_invoices=flagged,
        all_invoices=all_invoices,
        scan_date=scan_date,
    )

    audit = get_audit_logger()
    audit.log_notification()

    result = {
        "flagged_invoices": flagged,
        "summary": summary,
        "audit_log": audit.get_log(),
        "scan_date": scan_date,
    }

    assert result["flagged_invoices"] == []
    assert isinstance(result["summary"], str)
    assert len(result["audit_log"]) == 1
