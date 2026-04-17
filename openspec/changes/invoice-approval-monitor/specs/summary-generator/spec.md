## ADDED Requirements

### Requirement: Generate LLM-based weekly narrative summary
The system SHALL call an LLM (via LiteLLM/AI Core) to generate a human-readable weekly summary from the flagged invoice list.

#### Scenario: Summary contains flagged invoice details
- **WHEN** the summary generator is called with a non-empty flagged invoice list
- **THEN** the returned summary includes total pending invoices, count of flagged invoices, and top escalation candidates

#### Scenario: Summary handles empty flagged list
- **WHEN** no invoices are flagged
- **THEN** the summary states that no high-value invoices are pending and the backlog is clear
