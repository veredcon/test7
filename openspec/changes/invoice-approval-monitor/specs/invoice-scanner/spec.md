## ADDED Requirements

### Requirement: Fetch pending invoices from S/4HANA
The system SHALL retrieve supplier invoices from S/4HANA `A_SupplierInvoice` endpoint (mocked in dev/test). The tool SHALL use in-memory mock data when `pytest` is in `sys.modules`.

#### Scenario: Returns all pending invoices
- **WHEN** the invoice scanner tool is called
- **THEN** it returns a list of invoices with fields: SupplierInvoice, InvoiceGrossAmount, DocumentCurrency, PostingDate, SupplierInvoiceApprovalStatus, Supplier

### Requirement: Flag high-value pending invoices
The system SHALL flag any invoice where `InvoiceGrossAmount > 50000` AND `days_pending > 3` (calculated from `PostingDate` to current date).

#### Scenario: Invoice above threshold is flagged
- **WHEN** an invoice has amount 75000 and was posted 5 days ago with status pending
- **THEN** it appears in the flagged invoices list with days_pending and amount annotated

#### Scenario: Invoice below threshold is not flagged
- **WHEN** an invoice has amount 30000 pending for 5 days
- **THEN** it does NOT appear in the flagged invoices list

#### Scenario: Invoice above amount but within 3 days is not flagged
- **WHEN** an invoice has amount 100000 and was posted 2 days ago
- **THEN** it does NOT appear in the flagged invoices list
