## 1. Project Bootstrap

- [x] 1.1 Create `assets/agent/` directory, then activate and run the `sap-agent-bootstrap` skill from within that directory to scaffold the full A2A agent project structure (solution.yaml, asset.yaml, Dockerfile, app/)
- [ ] 1.2 Verify required structure exists: `solution.yaml`, `assets/agent/asset.yaml`, `assets/agent/Dockerfile`, `assets/agent/app/`
- [ ] 1.3 Ensure `asset.yaml` uses `buildPath: .` and `/.well-known/agent.json` for all health probes
- [ ] 1.4 Copy boilerplate test files into `assets/agent/`: `cp -r .agent/skills/prd-to-spec/assets/agent_tests/. assets/agent/`; then rename `.template` files: `for file in assets/agent/**/*.template; do [ -f "$file" ] && mv "$file" "${file%.template}"; done`
- [ ] 1.5 Install test dependencies: `pip install -r assets/agent/requirements-test.txt` (run from project root)

## 2. Instrumentation Setup

- [ ] 2.1 In `assets/agent/app/main.py`, call `auto_instrument()` at the very top before any AI framework imports
- [ ] 2.2 Import OpenTelemetry tracing utilities for custom spans in all tool/handler files

## 3. Invoice Scanner Tool

- [ ] 3.1 Create `assets/agent/app/tools/invoice_scanner.py` with a `scan_invoices` tool that fetches pending invoices
- [ ] 3.2 Implement in-memory mock data: at least 5 invoices with varying amounts (some >50K, some <50K) and PostingDate values (some >3 days ago, some <3 days ago). Use `sys.modules` check to switch between mock and real S/4HANA call.
- [ ] 3.3 Implement threshold filtering: flag invoices where `InvoiceGrossAmount > 50000` AND `(today - PostingDate).days > 3`
- [ ] 3.4 Add M1 instrumentation: emit `logger.info("M1.achieved: invoice scan completed, {n} pending invoices retrieved")` on success; `logger.warning("M1.missed: invoice scan failed or returned no data")` on failure/empty
- [ ] 3.5 Add M2 instrumentation: emit `logger.info("M2.achieved: flagging complete, {n} invoices flagged above threshold")` after filtering; `logger.warning("M2.missed: flagging step did not complete")` on error
- [ ] 3.6 Wrap scan logic in an OpenTelemetry span named `invoice_scan`

## 4. Summary Generator Tool

- [ ] 4.1 Create `assets/agent/app/tools/summary_generator.py` with a `generate_summary` tool
- [ ] 4.2 Construct a prompt from the flagged invoice list and call LiteLLM (AI Core) to generate a narrative weekly summary
- [ ] 4.3 Handle empty flagged list: produce a "no high-value invoices pending" summary without calling the LLM if the list is empty
- [ ] 4.4 Add M3 instrumentation: emit `logger.info("M3.achieved: weekly summary generated successfully")` on success; `logger.warning("M3.missed: summary generation failed")` on error
- [ ] 4.5 Wrap summary logic in an OpenTelemetry span named `summary_generation`

## 5. Audit Logger Tool

- [ ] 5.1 Create `assets/agent/app/tools/audit_logger.py` with an `AuditLogger` class using an in-memory list
- [ ] 5.2 Implement `log_flag(invoice_id, amount, action)` and `log_notification(action)` methods; each entry includes ISO timestamp
- [ ] 5.3 Implement `get_log()` method returning the full log as a list of dicts
- [ ] 5.4 Add M5 instrumentation: emit `logger.info("M5.achieved: audit log updated with {n} flags and notification record")` after writing; `logger.warning("M5.missed: audit log write failed")` on error

## 6. Weekly Summary Endpoint

- [ ] 6.1 Add `GET /weekly-summary` route to the agent's HTTP server (FastAPI or equivalent per sap-agent-bootstrap pattern)
- [ ] 6.2 Handler: call `scan_invoices` → `generate_summary` → `audit_logger.log_notification` → return JSON `{flagged_invoices, summary, audit_log}`
- [ ] 6.3 On data source failure: return HTTP 500 with error message, log `M1.missed`
- [ ] 6.4 Add M4 instrumentation: emit `logger.info("M4.achieved: CFO notification sent via n8n workflow")` (emitted when endpoint returns 200); `logger.warning("M4.missed: CFO notification failed - {reason}")` on error
- [ ] 6.5 Wrap full endpoint handler in an OpenTelemetry span named `weekly_summary_endpoint`
- [ ] 6.6 Register `weekly-summary` skill in agent card at `/.well-known/agent.json`

## 7. Extensibility (sap-agent-extensibility skill — MANDATORY)

- [ ] 7.1 Activate and complete the full `sap-agent-extensibility` skill workflow (do NOT skip — this must result in actual code)
- [ ] 7.2 Identify extension points: `InvoiceScannerExtension`, `ThresholdEvaluatorExtension`, `SummaryGeneratorExtension`, `AuditLoggerExtension`
- [ ] 7.3 Create `assets/agent/app/extension_capabilities.py` defining Protocol interfaces and a `register_extension` mechanism for each extension point
- [ ] 7.4 Wrap each extension point invocation with a telemetry span
- [ ] 7.5 Verify: `grep -r "extension_capabilities\|ExtensionPoint\|register_extension" assets/agent/app/` must return results
- [ ] 7.6 Verify: `ls assets/agent/app/extension_capabilities.py` must succeed

## 8. n8n Workflow

- [ ] 8.1 Create `assets/n8n/cfo-weekly-summary-workflow.json` — n8n workflow JSON with: Cron node (Monday 08:00), HTTP Request node (GET `{{AGENT_URL}}/weekly-summary`), Email/SMTP node (send to `{{CFO_EMAIL}}`)
- [ ] 8.2 Configure error handling in n8n: if HTTP node returns non-2xx, stop workflow and log error (no partial email)
- [ ] 8.3 Document required n8n environment variables in a comment block at the top of the workflow JSON: `AGENT_URL`, `CFO_EMAIL`, SMTP credentials

## 9. Tests

- [ ] 9.1 Write unit test `assets/agent/tests/test_invoice_scanner.py` — test `scan_invoices` returns correct flagged list with mock data; run `pytest assets/agent/tests/test_invoice_scanner.py` immediately after writing
- [ ] 9.2 Write unit test `assets/agent/tests/test_summary_generator.py` — test summary is generated for non-empty and empty flagged lists; mock S/4HANA, use real LLM (AI Core env vars are present); run immediately
- [ ] 9.3 Write unit test `assets/agent/tests/test_audit_logger.py` — test `log_flag` and `log_notification` append entries; test `get_log` returns correct structure; run immediately
- [ ] 9.4 Write integration test `assets/agent/tests/test_integration.py` — end-to-end: call `/weekly-summary` endpoint, assert JSON structure with `flagged_invoices`, `summary`, `audit_log`; mock S/4HANA; use real LLM via AI Core
- [ ] 9.5 Run `pytest` from `assets/agent/` (no extra flags — `pytest.ini` controls everything); check `test_report.json` is created
- [ ] 9.6 If coverage < 70%, add targeted tests until threshold is met, then re-run `pytest`

## 10. Validation

- [ ] 10.1 Run `grep -r "M[0-9]\.achieved" assets/agent/app/` — must return results for all 5 milestones
- [ ] 10.2 Run `grep -r "extension_capabilities\|ExtensionPoint\|register_extension" assets/agent/app/` — must return results
- [ ] 10.3 Verify `assets/agent/app/extension_capabilities.py` exists
- [ ] 10.4 Verify `assets/agent/Dockerfile` exists (co-located with `asset.yaml`)
- [ ] 10.5 Run `openspec validate invoice-approval-monitor --strict --no-interactive`
- [ ] 10.6 Run final `pytest` from `assets/agent/` — confirm `test_report.json` contains latest results
