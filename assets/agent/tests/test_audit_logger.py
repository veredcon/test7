"""Unit tests for audit_logger tool."""

import pytest


def test_log_flag_appends_entry():
    """log_flag should append an entry to the log with expected fields."""
    from tools.audit_logger import AuditLogger

    logger = AuditLogger()
    logger.log_flag(invoice_id="INV-001", amount=75000.0, action="flagged")

    log = logger.get_log()
    assert len(log) == 1
    entry = log[0]
    assert entry["invoice_id"] == "INV-001"
    assert entry["amount"] == 75000.0
    assert entry["action"] == "flagged"
    assert entry["type"] == "flag"
    assert "timestamp" in entry


def test_log_notification_appends_entry():
    """log_notification should append a notification entry."""
    from tools.audit_logger import AuditLogger

    logger = AuditLogger()
    logger.log_notification(action="notification_dispatched")

    log = logger.get_log()
    assert len(log) == 1
    entry = log[0]
    assert entry["action"] == "notification_dispatched"
    assert entry["type"] == "notification"
    assert "timestamp" in entry


def test_get_log_returns_copy():
    """get_log should return a copy, not the internal list."""
    from tools.audit_logger import AuditLogger

    logger = AuditLogger()
    logger.log_flag("INV-001", 50001.0)
    log = logger.get_log()
    log.append({"tampered": True})  # mutate returned list

    assert len(logger.get_log()) == 1  # internal log unchanged


def test_multiple_entries_accumulated():
    """Multiple log calls should accumulate all entries."""
    from tools.audit_logger import AuditLogger

    logger = AuditLogger()
    logger.log_flag("INV-001", 75000.0)
    logger.log_flag("INV-002", 120000.0)
    logger.log_notification()

    assert len(logger.get_log()) == 3


def test_clear_resets_log():
    """clear() should empty the log."""
    from tools.audit_logger import AuditLogger

    logger = AuditLogger()
    logger.log_flag("INV-001", 75000.0)
    logger.clear()

    assert len(logger.get_log()) == 0
