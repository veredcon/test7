## Why

Finance teams lack automated monitoring of high-value invoice approval backlogs. Invoices over 50K pending more than 3 days go undetected, creating cash-flow risk and compliance exposure. The CFO has no reliable weekly digest of the approval backlog without manual effort.

## What Changes

- New Python AI agent that monitors S/4HANA supplier invoices, flags invoices >50K pending >3 days, generates a weekly narrative summary using an LLM, and exposes a `/weekly-summary` REST endpoint.
- New n8n workflow that triggers every Monday at 08:00, calls the agent's summary endpoint, and sends a formatted email to the CFO.
- Audit log persisted by the agent for all flags raised and notifications dispatched.

## Capabilities

### New Capabilities
- `invoice-scanner`: Fetches pending supplier invoices from S/4HANA (mocked), applies threshold rules (amount >50K, days pending >3), and returns flagged invoice list.
- `summary-generator`: Uses LLM to generate a structured narrative weekly summary from flagged invoice data.
- `audit-logger`: Persists flagged invoice records and notification events to an in-memory/file audit log.
- `weekly-summary-endpoint`: Exposes a REST endpoint `/weekly-summary` that triggers the scan, generates the summary, logs the event, and returns the result.
- `n8n-cfo-notification`: n8n workflow with Monday 08:00 cron trigger → HTTP call to agent's `/weekly-summary` → email dispatch to CFO.

### Modified Capabilities
<!-- None — this is a new project -->

## Impact

- New assets: `assets/agent/` (Python A2A agent), `assets/n8n/` (n8n workflow JSON)
- New dependencies: `httpx`, `python-dateutil`, LiteLLM (AI Core via environment)
- Integration: S/4HANA `API_SUPPLIERINVOICE_PROCESS_SRV` OData v4 (read-only, mocked in dev/test)
- n8n HTTP node connects to agent's `/weekly-summary` endpoint
