# Product Requirements Document (PRD)

**Title:** Invoice Approval Monitor Agent  
**Date:** 2026-04-16  
**Owner:** Finance Operations / CFO Office  
**Solution Category:** AI Agent, n8n Workflow

---

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Finance teams lose visibility when large invoices stall in approval queues. This agent continuously monitors invoice approvals, flags any invoice over 50K pending more than 3 days, and delivers a structured weekly summary to the CFO every Monday morning — automatically.

**Business Need:**  
There is no automated mechanism today to detect high-value invoices aging in approval workflows or to provide the CFO with a consolidated weekly view of the approval backlog. This creates cash-flow risk, compliance exposure, and decision-making delays.

**Expected Value:**  
- Eliminate blind spots in invoice approval monitoring for invoices exceeding 50K.  
- Reduce manual reporting effort for finance operations teams.  
- Provide the CFO with a reliable, zero-effort weekly digest each Monday.

**Product Objectives (Prioritized):**
1. Detect and flag all invoices >50K pending approval for more than 3 days.
2. Generate a structured, narrative weekly summary of the approval backlog.
3. Deliver the summary to the CFO automatically every Monday morning via email.
4. Maintain an audit log of all flags raised and notifications sent.

---

## Requirements

### Must-Have Requirements

**R1: Invoice Monitoring & Threshold Flagging**
- **Problem to Solve**: High-value invoices stall in approval queues without any alert, creating financial and compliance risk.
- **User Story**: As a finance operations agent, I need to scan all pending invoices and flag those exceeding 50K that have been waiting for more than 3 days, so that nothing slips through unnoticed.
- **Acceptance Criteria**:
  - Given a list of pending invoices, when the agent runs, then all invoices with amount > 50,000 AND pending days > 3 are flagged.
  - Flagged invoices include: invoice ID, amount, vendor, responsible approver, and days pending.
- **Priority Rank**: 1

**R2: Weekly Summary Generation**
- **Problem to Solve**: The CFO has no consolidated view of the invoice approval backlog without manual effort.
- **User Story**: As the CFO, I need a weekly summary report of all flagged and pending invoices so that I can make informed decisions about approval escalations.
- **Acceptance Criteria**:
  - Given the current invoice data, when a weekly summary is requested, then the agent produces a structured report covering: total pending invoices, flagged high-value invoices, approver breakdown, and top escalation candidates.
  - The summary is in a human-readable narrative format.
- **Priority Rank**: 2

**R3: Scheduled CFO Notification via n8n**
- **Problem to Solve**: The CFO needs to receive the weekly summary without any manual trigger.
- **User Story**: As the CFO, I need to receive the weekly invoice summary every Monday morning in my inbox so I can review it before the week begins.
- **Acceptance Criteria**:
  - Given the n8n workflow is active, when Monday 08:00 is reached, then the workflow calls the agent's summary endpoint and sends a formatted email to the CFO.
  - The email contains the full weekly summary with flagged invoice details.
- **Priority Rank**: 3

**R4: Audit Log**
- **Problem to Solve**: Flags raised and notifications sent must be traceable for compliance purposes.
- **User Story**: As a compliance officer, I need a log of all flagged invoices and sent notifications so that the monitoring activity is auditable.
- **Acceptance Criteria**:
  - Each flagged invoice and each CFO notification is persisted in a log with timestamp, invoice ID, and action taken.
- **Priority Rank**: 4

---

## Solution Architecture

**Architecture Overview:**  
A Python AI agent handles the monitoring, flagging, and summary generation logic. An n8n workflow provides the scheduled Monday trigger and email delivery. Invoice data is retrieved from an external source (SAP S/4HANA AP APIs or a mock data layer for dev/test).

**Key Components:**
- **Invoice Monitor Agent (Python)**: Core agent — scans invoices, applies threshold rules, generates the weekly narrative summary via LLM, and exposes a `/weekly-summary` endpoint.
- **n8n Workflow**: Cron-triggered every Monday at 08:00 → calls agent's summary endpoint → sends email to CFO.
- **Invoice Data Source**: S/4HANA Accounts Payable APIs (or configurable mock for development).
- **Audit Log Store**: File-based or lightweight DB log persisted by the agent.

**Integration Points:**
- S/4HANA AP API: read-only, pulls pending invoice list with amount, status, aging, and approver.
- Email service (SMTP / SAP alert service): write, sends the weekly summary email.

---

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The agent must be built with extension points to allow future additions: e.g., additional threshold rules, new notification channels, or custom escalation logic.
- Extension points include: threshold configuration (amount, days), summary template, recipient list, and data source connector.
- The `sap-agent-extensibility` skill will be applied during implementation.

**Business Step Instrumentation:**
- All key business steps must emit structured log statements for observability.
- Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`

---

### Automation & Agent Behaviour

**Automation Level:** Hybrid (rule-based flagging + LLM-assisted summary generation)

**Actions the system performs without human approval:**
- Scanning pending invoices and applying threshold rules.
- Generating the weekly summary narrative.
- Triggering the CFO email via n8n.

**Actions that require human review or approval:**
- Modifying invoice data or approval status (explicitly out of scope — read-only agent).

**Model:** GPT-4o via SAP Generative AI Hub (for summary narrative generation).

**Knowledge & data sources accessed:**
- SAP S/4HANA Accounts Payable pending invoice list (read-only).

**Tools or connectors invoked:**
- S/4HANA AP API connector: read-only invoice data retrieval.
- n8n HTTP node: calls agent's `/weekly-summary` endpoint.
- Email node (n8n): sends formatted summary to CFO.

**Guardrails & fail-safes:**
- Agent never modifies invoice records or approval statuses — strictly read-only.
- If the data source is unavailable, the agent logs the failure and skips the notification with an error alert.
- If fewer than 1 invoice is returned, the agent sends a "no flagged items" summary rather than skipping the notification.

---

## Milestones

### M1: Invoice Scan Completed
- **Description**: Agent has retrieved all pending invoices from the data source.
- **Achieved when**: Invoice list is fetched successfully and has been processed for threshold evaluation.
- **Log on achievement**: `M1.achieved: invoice scan completed, {n} pending invoices retrieved`
- **Log on miss**: `M1.missed: invoice scan failed or returned no data`

### M2: Flags Raised
- **Description**: High-risk invoices (>50K, >3 days pending) have been identified and annotated.
- **Achieved when**: At least one invoice is evaluated against thresholds; flagged list is produced (may be empty).
- **Log on achievement**: `M2.achieved: flagging complete, {n} invoices flagged above threshold`
- **Log on miss**: `M2.missed: flagging step did not complete`

### M3: Weekly Summary Generated
- **Description**: The agent has produced a structured narrative weekly summary.
- **Achieved when**: Summary document is generated and ready for dispatch.
- **Log on achievement**: `M3.achieved: weekly summary generated successfully`
- **Log on miss**: `M3.missed: summary generation failed`

### M4: CFO Notification Triggered
- **Description**: n8n workflow has dispatched the weekly summary email to the CFO.
- **Achieved when**: n8n cron fires, summary endpoint is called, and email is sent without error.
- **Log on achievement**: `M4.achieved: CFO notification sent via n8n workflow`
- **Log on miss**: `M4.missed: CFO notification failed - {reason}`

### M5: Escalation Recorded
- **Description**: All flagged invoices and the notification event are persisted to the audit log.
- **Achieved when**: Audit log entry is written for each flag and for the notification dispatch.
- **Log on achievement**: `M5.achieved: audit log updated with {n} flags and notification record`
- **Log on miss**: `M5.missed: audit log write failed`
