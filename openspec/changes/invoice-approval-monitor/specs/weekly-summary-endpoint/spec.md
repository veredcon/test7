## ADDED Requirements

### Requirement: Expose /weekly-summary REST endpoint
The agent SHALL expose a `GET /weekly-summary` endpoint that: (1) scans invoices, (2) flags high-value pending ones, (3) generates the LLM summary, (4) logs the audit entry, and returns a JSON response.

#### Scenario: Successful summary response
- **WHEN** GET /weekly-summary is called
- **THEN** the response contains: flagged_invoices (list), summary (string), audit_log (list), status 200

#### Scenario: Data source unavailable
- **WHEN** the invoice data source fails
- **THEN** the endpoint returns a 500 error with a descriptive message and logs the failure

### Requirement: Agent card exposes weekly-summary skill
The agent card at `/.well-known/agent.json` SHALL list the `weekly-summary` capability.

#### Scenario: Agent card is accessible
- **WHEN** GET /.well-known/agent.json is called
- **THEN** the response contains the agent's name, description, and skills list including weekly-summary
