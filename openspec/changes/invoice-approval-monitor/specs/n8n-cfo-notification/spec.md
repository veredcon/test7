## ADDED Requirements

### Requirement: n8n workflow triggers weekly CFO email
The n8n workflow SHALL be configured with a Cron trigger for every Monday at 08:00, an HTTP Request node calling the agent's `/weekly-summary` endpoint, and an Email (SMTP) node sending the summary to the CFO.

#### Scenario: Monday morning trigger fires
- **WHEN** Monday 08:00 is reached
- **THEN** the cron node triggers the workflow, the HTTP node calls /weekly-summary, and the email node dispatches the summary to the CFO email address

#### Scenario: Agent endpoint failure
- **WHEN** the HTTP node receives a non-2xx response
- **THEN** the workflow logs the error and does NOT send a partial email
