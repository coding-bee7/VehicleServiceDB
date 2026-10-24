# Backend Test Cases

Project: Vehicle Service and Maintenance Management System

| ID | Test | Expected result | Actual result |
|---|---|---|---|
| API-01 | Check `/api/health` | HTTP 200 and database status | Passed — verified |
| AUTH-01 | Register a valid customer | HTTP 201 and customer account created | Passed — verified |
| AUTH-02 | Log in with valid credentials | HTTP 200 and JWT returned | Passed — verified |
| AUTH-03 | Call `/api/auth/me` without a token | HTTP 401 | Passed — verified |
| AUTH-04 | Attempt to create staff without admin authorization | HTTP 401 or 403 | Pending verification |
| SRV-01 | Complete service 4 | HTTP 200 and service marked completed | Passed — verified |
| SRV-02 | Repeat completion request | No second stock deduction or duplicate invoice | Passed — verified |
| INV-01 | Verify service 4 invoice | Total amount is 5000.00 and payment remains Unpaid | Passed — verified |
| INV-02 | Complete service with insufficient inventory | HTTP 409 and all transaction changes rolled back | Pending verification |
| SEC-01 | Attempt to access another customer's data | Access denied | Pending verification |

## Testing Notes
- Tests marked pending must be executed before final submission.
- Record the date, test environment, and any observed error messages.
- Never include real passwords, JWT tokens, or private customer information in screenshots.
