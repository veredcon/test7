"""
Audit Logger Tool
Persists flagged invoice records and notification events to an in-memory audit log.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class AuditLogger:
    """
    In-memory audit log for flagged invoices and notification events.
    Can be extended via AuditLoggerExtension to persist to file or DB.
    """

    def __init__(self) -> None:
        self._log: list[dict[str, Any]] = []

    def log_flag(self, invoice_id: str, amount: float, action: str = "flagged") -> None:
        """Log a flagged invoice entry."""
        with tracer.start_as_current_span("audit_log_flag"):
            try:
                entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "type": "flag",
                    "invoice_id": invoice_id,
                    "amount": amount,
                    "action": action,
                }
                self._log.append(entry)
            except Exception as e:
                logger.warning(f"M5.missed: audit log write failed: {e}")
                raise

    def log_notification(self, action: str = "notification_dispatched") -> None:
        """Log a notification dispatch event."""
        with tracer.start_as_current_span("audit_log_notification"):
            try:
                entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "type": "notification",
                    "action": action,
                }
                self._log.append(entry)
                logger.info(f"M5.achieved: audit log updated with {len(self._log)} entries and notification record")
            except Exception as e:
                logger.warning(f"M5.missed: audit log write failed: {e}")
                raise

    def get_log(self) -> list[dict[str, Any]]:
        """Return the full audit log as a list of dicts."""
        return list(self._log)

    def clear(self) -> None:
        """Clear the audit log (useful for testing)."""
        self._log.clear()


# Module-level singleton used by the weekly summary endpoint
_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Return the shared audit logger instance."""
    return _audit_logger
