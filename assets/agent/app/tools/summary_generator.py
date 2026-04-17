"""
Summary Generator Tool
Generates a narrative weekly summary from flagged invoice data using LiteLLM (SAP AI Core).
"""

import logging
from typing import Any

from langchain_litellm import ChatLiteLLM
from langchain_core.messages import HumanMessage
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def _build_prompt(flagged_invoices: list[dict[str, Any]], all_invoices: list[dict[str, Any]], scan_date: str) -> str:
    """Build the LLM prompt from invoice data."""
    total = len(all_invoices)
    flagged_count = len(flagged_invoices)

    lines = [
        f"Weekly Invoice Approval Summary — {scan_date}",
        f"Total pending invoices: {total}",
        f"High-value flagged invoices (>50K, >3 days pending): {flagged_count}",
        "",
        "Flagged invoices requiring CFO attention:",
    ]
    for inv in flagged_invoices:
        lines.append(
            f"  - Invoice {inv['SupplierInvoice']}: {inv['InvoiceGrossAmount']} {inv['DocumentCurrency']} "
            f"from {inv['Supplier']} — {inv['days_pending']} days pending"
        )

    return "\n".join(lines)


def generate_summary(
    flagged_invoices: list[dict[str, Any]],
    all_invoices: list[dict[str, Any]],
    scan_date: str,
) -> str:
    """
    Generate a human-readable weekly invoice summary using an LLM.

    Args:
        flagged_invoices: List of invoices exceeding threshold.
        all_invoices: Full list of pending invoices.
        scan_date: ISO date string for the scan.

    Returns:
        Narrative summary string.
    """
    with tracer.start_as_current_span("summary_generation") as span:
        try:
            span.set_attribute("summary.flagged_count", len(flagged_invoices))
            span.set_attribute("summary.total_invoices", len(all_invoices))

            # Fast path: no flagged invoices
            if not flagged_invoices:
                summary = (
                    f"Weekly Invoice Approval Summary ({scan_date}): "
                    "No high-value invoices (>50K, >3 days pending) are currently awaiting approval. "
                    f"Total pending invoices: {len(all_invoices)}. The approval backlog is within acceptable parameters."
                )
                logger.info("M3.achieved: weekly summary generated successfully")
                span.set_attribute("summary.llm_called", False)
                return summary

            # Build prompt and call LLM
            data_summary = _build_prompt(flagged_invoices, all_invoices, scan_date)
            prompt = (
                "You are a financial assistant preparing a weekly invoice approval summary for the CFO. "
                "Based on the following data, write a concise, professional summary (3-5 sentences) "
                "highlighting the most urgent items, total backlog size, and any recommended actions.\n\n"
                f"{data_summary}"
            )

            llm = ChatLiteLLM(model="sap/anthropic--claude-4.5-sonnet")
            response = llm.invoke([HumanMessage(content=prompt)])
            summary = response.content

            logger.info("M3.achieved: weekly summary generated successfully")
            span.set_attribute("summary.llm_called", True)
            return summary

        except Exception as e:
            logger.warning(f"M3.missed: summary generation failed: {e}")
            span.record_exception(e)
            raise
