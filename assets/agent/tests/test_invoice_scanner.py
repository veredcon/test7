"""Unit tests for invoice_scanner tool."""

import sys
import pytest

# Ensure pytest mode is active so mock data is used
assert "pytest" in sys.modules


def test_scan_invoices_returns_flagged_list():
    """scan_invoices should flag invoices >50K and >3 days pending."""
    from tools.invoice_scanner import scan_invoices

    result = scan_invoices()

    assert "flagged_invoices" in result
    assert "all_invoices" in result
    assert "scan_date" in result

    flagged = result["flagged_invoices"]
    # At least 1 flagged invoice expected from mock data (INV-001, INV-002, INV-006)
    assert len(flagged) > 0

    # Each flagged invoice must exceed thresholds
    for inv in flagged:
        assert inv["InvoiceGrossAmount"] > 50_000
        assert inv["days_pending"] > 3
        assert inv["SupplierInvoiceApprovalStatus"] == "PENDING"


def test_scan_invoices_not_flagged_low_amount():
    """Invoices under 50K threshold should not be flagged."""
    from tools.invoice_scanner import scan_invoices

    result = scan_invoices()
    flagged_ids = {inv["SupplierInvoice"] for inv in result["flagged_invoices"]}

    # INV-003 has amount 30K — must not be flagged
    assert "INV-003" not in flagged_ids


def test_scan_invoices_not_flagged_recent():
    """Invoices >50K but only 1 day pending should not be flagged."""
    from tools.invoice_scanner import scan_invoices

    result = scan_invoices()
    flagged_ids = {inv["SupplierInvoice"] for inv in result["flagged_invoices"]}

    # INV-004 has amount 85K but was posted 1 day ago — must not be flagged
    assert "INV-004" not in flagged_ids


def test_scan_invoices_approved_not_flagged():
    """Approved invoices should not appear in flagged list regardless of amount/age."""
    from tools.invoice_scanner import scan_invoices

    result = scan_invoices()
    flagged_ids = {inv["SupplierInvoice"] for inv in result["flagged_invoices"]}

    # INV-005 is APPROVED — must not be flagged
    assert "INV-005" not in flagged_ids


def test_scan_invoices_flagged_contain_required_fields():
    """Flagged invoices must include all required fields."""
    from tools.invoice_scanner import scan_invoices

    result = scan_invoices()
    required_fields = {
        "SupplierInvoice",
        "InvoiceGrossAmount",
        "DocumentCurrency",
        "PostingDate",
        "SupplierInvoiceApprovalStatus",
        "Supplier",
        "days_pending",
    }
    for inv in result["flagged_invoices"]:
        assert required_fields.issubset(inv.keys()), f"Missing fields in {inv}"
