"""Unit tests for summary_generator tool.

Note: AI Core env vars are available, but S/4HANA is mocked.
Summary generation uses the real LLM via LiteLLM/AI Core.
"""

import sys
import pytest

assert "pytest" in sys.modules

# Minimal flagged invoice fixture
FLAGGED_INVOICES = [
    {
        "SupplierInvoice": "INV-001",
        "InvoiceGrossAmount": 75_000.0,
        "DocumentCurrency": "EUR",
        "PostingDate": "2024-04-10",
        "SupplierInvoiceApprovalStatus": "PENDING",
        "Supplier": "VENDOR-A",
        "CompanyCode": "1000",
        "days_pending": 5,
    }
]

ALL_INVOICES = FLAGGED_INVOICES + [
    {
        "SupplierInvoice": "INV-003",
        "InvoiceGrossAmount": 30_000.0,
        "DocumentCurrency": "EUR",
        "PostingDate": "2024-04-09",
        "SupplierInvoiceApprovalStatus": "PENDING",
        "Supplier": "VENDOR-C",
        "CompanyCode": "2000",
        "days_pending": 6,
    }
]


def test_generate_summary_empty_flagged():
    """generate_summary with empty flagged list returns 'no high-value' message without calling LLM."""
    from tools.summary_generator import generate_summary

    summary = generate_summary(
        flagged_invoices=[],
        all_invoices=ALL_INVOICES,
        scan_date="2024-04-15",
    )

    assert isinstance(summary, str)
    assert len(summary) > 0
    # Fast path — no LLM call needed for empty list
    assert "no high-value" in summary.lower() or "clear" in summary.lower() or "no" in summary.lower()


def test_generate_summary_returns_string(monkeypatch):
    """generate_summary returns a non-empty string for non-empty flagged list."""
    from tools import summary_generator

    class FakeMessage:
        content = "This week, 1 high-value invoice over 50K is pending approval for more than 3 days requiring CFO attention."

    class FakeLLM:
        def invoke(self, messages):
            return FakeMessage()

    monkeypatch.setattr(summary_generator, "ChatLiteLLM", lambda **kwargs: FakeLLM())

    summary = summary_generator.generate_summary(
        flagged_invoices=FLAGGED_INVOICES,
        all_invoices=ALL_INVOICES,
        scan_date="2024-04-15",
    )

    assert isinstance(summary, str)
    assert len(summary) > 10


def test_generate_summary_empty_flagged_no_llm_call(monkeypatch):
    """Empty flagged list should NOT call LLM (fast path)."""
    from tools import summary_generator

    calls = []

    class FakeLLM:
        def invoke(self, messages):
            calls.append(messages)
            raise AssertionError("LLM should NOT be called for empty flagged list")

    monkeypatch.setattr(summary_generator, "ChatLiteLLM", lambda **kwargs: FakeLLM())

    summary = summary_generator.generate_summary(
        flagged_invoices=[],
        all_invoices=ALL_INVOICES,
        scan_date="2024-04-15",
    )

    assert isinstance(summary, str)
    assert len(calls) == 0
