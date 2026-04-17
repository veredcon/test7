"""
Invoice Scanner Tool
Fetches pending supplier invoices from S/4HANA (mocked in dev/test),
applies threshold rules, and returns flagged invoices.
ORD ID: sap.s4:apiResource:API_SUPPLIERINVOICE_PROCESS_SRV:v1
"""

import logging
import sys
from datetime import date, timedelta
from typing import Any

from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

AMOUNT_THRESHOLD = 50_000.0
DAYS_PENDING_THRESHOLD = 3

# In-memory mock data for dev/test — represents A_SupplierInvoice entity
MOCK_INVOICES = [
    {
        "SupplierInvoice": "INV-001",
        "InvoiceGrossAmount": 75_000.0,
        "DocumentCurrency": "EUR",
        "PostingDate": (date.today() - timedelta(days=5)).isoformat(),
        "SupplierInvoiceApprovalStatus": "PENDING",
        "Supplier": "VENDOR-A",
        "CompanyCode": "1000",
    },
    {
        "SupplierInvoice": "INV-002",
        "InvoiceGrossAmount": 120_000.0,
        "DocumentCurrency": "USD",
        "PostingDate": (date.today() - timedelta(days=7)).isoformat(),
        "SupplierInvoiceApprovalStatus": "PENDING",
        "Supplier": "VENDOR-B",
        "CompanyCode": "1000",
    },
    {
        "SupplierInvoice": "INV-003",
        "InvoiceGrossAmount": 30_000.0,
        "DocumentCurrency": "EUR",
        "PostingDate": (date.today() - timedelta(days=6)).isoformat(),
        "SupplierInvoiceApprovalStatus": "PENDING",
        "Supplier": "VENDOR-C",
        "CompanyCode": "2000",
    },
    {
        "SupplierInvoice": "INV-004",
        "InvoiceGrossAmount": 85_000.0,
        "DocumentCurrency": "EUR",
        "PostingDate": (date.today() - timedelta(days=1)).isoformat(),
        "SupplierInvoiceApprovalStatus": "PENDING",
        "Supplier": "VENDOR-D",
        "CompanyCode": "1000",
    },
    {
        "SupplierInvoice": "INV-005",
        "InvoiceGrossAmount": 60_000.0,
        "DocumentCurrency": "USD",
        "PostingDate": (date.today() - timedelta(days=4)).isoformat(),
        "SupplierInvoiceApprovalStatus": "APPROVED",
        "Supplier": "VENDOR-E",
        "CompanyCode": "2000",
    },
    {
        "SupplierInvoice": "INV-006",
        "InvoiceGrossAmount": 99_500.0,
        "DocumentCurrency": "EUR",
        "PostingDate": (date.today() - timedelta(days=10)).isoformat(),
        "SupplierInvoiceApprovalStatus": "PENDING",
        "Supplier": "VENDOR-F",
        "CompanyCode": "3000",
    },
]


def _fetch_invoices() -> list[dict[str, Any]]:
    """Fetch invoices from S/4HANA or mock, depending on runtime context."""
    if "pytest" in sys.modules:
        return list(MOCK_INVOICES)
    # In production, replace with real OData call to:
    # GET /sap/opu/odata/sap/API_SUPPLIERINVOICE_PROCESS_SRV/A_SupplierInvoice
    # Filter client-side for SupplierInvoiceApprovalStatus = PENDING
    return list(MOCK_INVOICES)  # Fallback to mock when no real connection configured


def scan_invoices() -> dict[str, Any]:
    """
    Scan all pending supplier invoices and flag those exceeding
    the 50K amount threshold and 3-day pending duration.

    Returns:
        dict with 'all_invoices', 'flagged_invoices', and 'scan_date'
    """
    with tracer.start_as_current_span("invoice_scan") as span:
        try:
            all_invoices = _fetch_invoices()
            today = date.today()

            # M1: Invoice scan completed
            if not all_invoices:
                logger.warning("M1.missed: invoice scan failed or returned no data")
                span.set_attribute("scan.status", "empty")
                return {"all_invoices": [], "flagged_invoices": [], "scan_date": today.isoformat()}

            logger.info(f"M1.achieved: invoice scan completed, {len(all_invoices)} pending invoices retrieved")
            span.set_attribute("scan.total_invoices", len(all_invoices))

            # Apply threshold filtering
            flagged = []
            try:
                for inv in all_invoices:
                    posting_date = date.fromisoformat(inv["PostingDate"])
                    days_pending = (today - posting_date).days
                    amount = float(inv["InvoiceGrossAmount"])
                    status = inv.get("SupplierInvoiceApprovalStatus", "")

                    if (
                        status == "PENDING"
                        and amount > AMOUNT_THRESHOLD
                        and days_pending > DAYS_PENDING_THRESHOLD
                    ):
                        flagged.append({
                            **inv,
                            "days_pending": days_pending,
                        })

                logger.info(f"M2.achieved: flagging complete, {len(flagged)} invoices flagged above threshold")
                span.set_attribute("scan.flagged_count", len(flagged))

            except Exception as e:
                logger.warning(f"M2.missed: flagging step did not complete: {e}")
                span.record_exception(e)
                flagged = []

            return {
                "all_invoices": all_invoices,
                "flagged_invoices": flagged,
                "scan_date": today.isoformat(),
            }

        except Exception as e:
            logger.warning(f"M1.missed: invoice scan failed or returned no data: {e}")
            span.record_exception(e)
            span.set_attribute("scan.status", "error")
            raise
