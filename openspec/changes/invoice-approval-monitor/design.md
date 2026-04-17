## Context

New Pro-Code Python AI agent built on SAP App Foundation A2A protocol. Monitors S/4HANA Supplier Invoice OData API for pending invoices, applies business rules, generates LLM-summarized weekly reports, and exposes an HTTP endpoint consumed by an n8n workflow that emails the CFO every Monday morning.

S/4HANA is mocked in dev/test using in-memory fixture data (real connection configured via env vars in production).

## Goals / Non-Goals

**Goals:**
- Scan pending invoices and flag those >50K pending >3 days
- Generate an LLM-based narrative weekly summary
- Expose `/weekly-summary` REST endpoint
- Persist audit log entries for flags and notifications
- n8n workflow for Monday 08:00 scheduled CFO email
- Full extensibility via extension points for all major components
- OpenTelemetry instrumentation for all 5 milestones

**Non-Goals:**
- Modifying or approving invoices (read-only agent)
- Real-time push notifications (weekly batch only)
- Authentication/authorization implementation
- Deployment to SAP BTP (local execution only)

## Decisions

### 1. S/4HANA API via Mock (not MCP translation)
**Decision:** Mock S/4HANA API_SUPPLIERINVOICE_PROCESS_SRV with in-memory fixture data.
**Rationale:** `SupplierInvoiceApprovalStatus` is non-filterable in OData; filtering must be done client-side. Mock layer allows fast dev/test iteration while real connector is wired via env vars for production.
**ORD ID:** `sap.s4:apiResource:API_SUPPLIERINVOICE_PROCESS_SRV:v1`
**API Spec reference:** `api-discovery-results.md` (project root)
**Key fields used:** `SupplierInvoice`, `InvoiceGrossAmount`, `DocumentCurrency`, `PostingDate`, `SupplierInvoiceApprovalStatus`, `Supplier`

### 2. LLM for Summary Generation
**Decision:** Use LiteLLM with SAP AI Core (GPT-4o) to produce the narrative summary.
**Rationale:** Structured invoice data alone lacks readability for CFO consumption; LLM adds narrative context, highlights top risks, and formats the output.

### 3. In-memory Audit Log
**Decision:** Audit log stored in-memory (list) per agent lifecycle; no external DB.
**Rationale:** Local execution constraint. Log is returned in the summary response and printed to stdout. Can be extended to file/DB via extension point.

### 4. n8n for CFO Email Dispatch
**Decision:** n8n workflow handles Monday 08:00 cron + HTTP call + email.
**Rationale:** Lightweight automation with no BTP footprint; n8n cron + HTTP node is the simplest solution.

### 5. Extensibility via Extension Points
**Decision:** All major components (invoice scanner, threshold evaluator, summary generator, audit logger) expose extension points via `extension_capabilities.py`.
**Rationale:** Required by sap-agent-extensibility skill and PRD; allows future custom threshold rules, notification channels, or data sources.

## Risks / Trade-offs

- [Risk] S/4HANA `SupplierInvoiceApprovalStatus` non-filterable — must fetch all invoices and filter client-side → **Mitigation:** Add date-range filter by `PostingDate` to reduce data volume.
- [Risk] LLM latency on summary generation (~3-5s) → **Mitigation:** Acceptable for weekly batch; endpoint is async-compatible.
- [Risk] In-memory audit log lost on agent restart → **Mitigation:** Audit log extension point allows file/DB persistence to be added without code change.

## API References

- **Discovery results:** `api-discovery-results.md` (project root)
- **ORD ID (Cloud):** `sap.s4:apiResource:API_SUPPLIERINVOICE_PROCESS_SRV:v1`
- **EntitySet:** `A_SupplierInvoice`
- **Fields:** `SupplierInvoice`, `InvoiceGrossAmount`, `DocumentCurrency`, `PostingDate`, `SupplierInvoiceApprovalStatus`, `Supplier`, `CompanyCode`
