# API Discovery Results — Invoice Approval Monitor Agent

## Discovered APIs

| API Name | ORD ID | Spec Format | Download Link |
|---|---|---|---|
| Supplier Invoice (S/4HANA Cloud) — API_SUPPLIERINVOICE_PROCESS_SRV | sap.s4:apiResource:API_SUPPLIERINVOICE_PROCESS_SRV:v1 | OpenAPI (JSON) | https://hcp-b740e347-cbe9-47be-a001-6c1d12e57b87.s3.amazonaws.com/staging/1776321333-SupplierInvoice_OpenAPI_API_SUPPLIERINVOICE_PROCESS_SRV.json?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAUSGYW4KBKTTOV35T%2F20260416%2Feu-central-1%2Fs3%2Faws4_request&X-Amz-Date=20260416T063533Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=5cff97e864b5f9625a731605a9eb0c3435da2852db0c09cebe74f15f754529d1 |
| Supplier Invoice (S/4HANA Cloud) — API_SUPPLIERINVOICE_PROCESS_SRV | sap.s4:apiResource:API_SUPPLIERINVOICE_PROCESS_SRV:v1 | OData EDMX (XML) | https://hcp-b740e347-cbe9-47be-a001-6c1d12e57b87.s3.amazonaws.com/staging/1776321333-SupplierInvoice_EDMX_API_SUPPLIERINVOICE_PROCESS_SRV.xml?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAUSGYW4KBKTTOV35T%2F20260416%2Feu-central-1%2Fs3%2Faws4_request&X-Amz-Date=20260416T063533Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=43728e670fe2353fdd59d6f715c98b2595a03fb8b3141db866a3bf1a75342ab6 |
| Supplier Invoice (S/4HANA On-Premise) — OP_API_SUPPLIERINVOICE_PROCESS_SRV | sap.s4:apiResource:OP_API_SUPPLIERINVOICE_PROCESS_SRV:v1 | OpenAPI (JSON) | https://hcp-b740e347-cbe9-47be-a001-6c1d12e57b87.s3.amazonaws.com/staging/1776321331-SupplierInvoice_OpenAPI_OP_API_SUPPLIERINVOICE_PROCESS_SRV.json?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAUSGYW4KBKTTOV35T%2F20260416%2Feu-central-1%2Fs3%2Faws4_request&X-Amz-Date=20260416T063532Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=872d14c3e31d3328ab0c19fe091ad706d84d9c19efae79083c46426c58c1734c |

## Key Entities

**EntitySet:** `A_SupplierInvoice`  
**Relevant fields:**
- `SupplierInvoice` — invoice ID
- `SupplierInvoiceApprovalStatus` — approval status (string, max 40)
- `SupplierInvoiceStatus` — overall status
- `InvoiceGrossAmount` — gross amount
- `DocumentCurrency` — currency
- `PostingDate` — posting/creation date
- `Supplier` — vendor
- `CompanyCode` — company code

**FunctionImports:** Release, Cancel, Post

## Key Notes
- `SupplierInvoiceApprovalStatus` is non-filterable via OData `$filter`; retrieve invoices by other criteria (PostingDate, CompanyCode) and filter client-side by status and amount.
- Approver identity is not exposed directly; for approver details, SAP BTP Workflow / My Inbox APIs are needed.
- Agent uses read-only access only (GET on A_SupplierInvoice).
