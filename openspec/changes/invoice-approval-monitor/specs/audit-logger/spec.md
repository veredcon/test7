## ADDED Requirements

### Requirement: Persist audit log entries
The system SHALL append an entry to an in-memory audit log for each: (a) flagged invoice, (b) weekly summary generated, (c) CFO notification dispatched.

#### Scenario: Flagged invoice is logged
- **WHEN** an invoice is flagged by the scanner
- **THEN** an audit entry is created with timestamp, invoice ID, amount, and action "flagged"

#### Scenario: Notification dispatch is logged
- **WHEN** the weekly summary endpoint is called successfully
- **THEN** an audit entry is created with timestamp and action "notification_dispatched"
