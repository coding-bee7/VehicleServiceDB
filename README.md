# Vehicle Service and Maintenance Management System
## Backend Branch Documentation

## 1. Overview

The Vehicle Service and Maintenance Management System is a DBMS project designed to manage vehicle servicing operations, customer accounts, appointments, employees, spare parts, inventory usage, service records, and invoices.

This branch contains the backend implementation responsible for processing API requests, enforcing selected authorization rules, applying service-related business logic, and interacting with the MySQL database.

**Backend branch:** `backend`

**Database:** `VehicleServiceDB`

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| Flask | REST API framework |
| MySQL | Relational database |
| `mysql-connector-python` | Python-to-MySQL connectivity |
| Flask-CORS | Cross-origin API requests |
| Flask-JWT-Extended | JWT-based authentication |
| Werkzeug | Password hashing and verification |
| `python-dotenv` | Loading environment variables |
| Visual Studio Code | Backend development |
| MySQL Workbench | Database management and SQL testing |
| React and Tailwind CSS | Frontend integration |

React and Tailwind CSS belong to the frontend. They communicate with the Flask backend through HTTP requests and JSON responses.

## 3. Architecture

```text
┌──────────────────────────────┐
│     React + Tailwind CSS     │
│           Frontend           │
└──────────────┬───────────────┘
               │
               │ HTTP / JSON
               ▼
┌──────────────────────────────┐
│          Flask API           │
│                              │
│ Authentication               │
│ Authorization                │
│ Service management           │
│ Inventory and invoice logic  │
└──────────────┬───────────────┘
               │
               │ MySQL Connector
               ▼
┌──────────────────────────────┐
│           MySQL              │
│       VehicleServiceDB       │
└──────────────────────────────┘
```

### Request flow

1. The frontend sends an HTTP request to a Flask API endpoint.
2. The backend validates the request and applies the relevant authentication and authorization checks.
3. The backend reads or updates records in MySQL.
4. The API returns a JSON response and an appropriate HTTP status code.

## 4. Repository Structure

The branch is organized around the application, database scripts, documentation, testing, and presentation materials.

```text
VehicleServiceDB/
├── application/
│   └── backend/
│       ├── app.py
│       ├── create_admin.py
│       ├── requirements.txt
│       └── README.md
├── database/
│   ├── schema.sql
│   ├── sample_data.sql
│   └── queries.sql
├── documentation/
├── testing/
└── presentation/
```

The tree describes the intended organization. Individual files should be included only if they have actually been created and committed. This root README documents the backend branch as a whole; `application/backend/README.md` can contain backend-specific setup details.

## 5. Database

The backend connects to the MySQL database named `VehicleServiceDB`.

The database supports the project's core entities and operations, including:

- Customers and vehicles
- Appointments
- Employees and staff roles
- Service records and service tasks
- Spare parts and part usage
- Invoices and payment status
- User accounts and account roles

The SQL schema defines the table structures, primary keys, foreign keys, uniqueness requirements, and data constraints.

### UserAccount

The `UserAccount` table supports authentication and connects an account to a customer or employee record.

| Column | Purpose |
|---|---|
| `UserID` | Primary key |
| `Email` | Unique login email |
| `PasswordHash` | Hashed password |
| `Role` | Account role |
| `CustomerID` | Optional customer reference |
| `EmployeeID` | Optional employee reference |
| `IsActive` | Account activation status |
| `CreatedAt` | Account creation timestamp |

The database constraints associate customer accounts with customer records and staff accounts with employee records.

### PartUsage and inventory

The `PartUsage` table records the parts used during a service. Its `StockDeducted` field tracks whether a usage record has already been applied to inventory.

This flag is important for preventing duplicate inventory deductions when a service-completion request is repeated.

## 6. Authentication and Authorization

Authentication uses JWT access tokens. Passwords are hashed using Werkzeug security utilities.

### Customer registration

`POST /api/auth/register`

Registers a customer account. The public registration route assigns the Customer role rather than allowing a user to register publicly as an administrator or staff member.

### Login

`POST /api/auth/login`

Validates the submitted email and password. On successful authentication, the endpoint returns a JWT access token.

The token is configured to expire after two hours and includes role and relevant customer or employee identity claims.

### Current authenticated account

`GET /api/auth/me`

Returns information about the authenticated account. A valid JWT is required.

### Role-based access control

The backend uses a `role_required` decorator to protect selected operations.

| Operation | Permitted role |
|---|---|
| Create staff accounts | Admin |
| Complete an eligible service | Admin or assigned Mechanic |

For mechanic service completion, the backend also checks that the service is assigned to the authenticated employee.

These restrictions apply to the implemented protected endpoints; they should not be interpreted as proof that every route has been audited for authorization and record ownership.

## 7. Staff Account Management

`POST /api/admin/staff`

This endpoint allows an authorized administrator to create staff accounts.

Supported staff roles are:

- Mechanic
- Service Advisor

The operation creates an employee record and a linked user account. A database transaction is used to keep the operation consistent if one of the steps fails.

### Initial administrator setup

`create_admin.py` is a one-time local setup script for creating the initial administrator account when one does not already exist.

Configure the database first and use a strong, unique administrator password. Never commit credentials or the `.env` file to GitHub.

## 8. Service Completion

`POST /api/services/<service_id>/complete`

This protected endpoint completes an eligible service record and updates related database records in a transaction.

The implemented workflow:

1. Retrieves and locks the service record.
2. Checks the caller's role and, for a mechanic, the service assignment.
3. Checks whether the service is eligible for completion.
4. Locks pending part-usage records and corresponding inventory records.
5. Verifies that sufficient stock is available.
6. Deducts the quantities used from inventory.
7. Marks the relevant usage records as stock-deducted.
8. Calculates labour and parts costs.
9. Creates or updates the associated invoice.
10. Marks the service record and appointment as completed.
11. Commits the transaction.

The operation is designed to roll back database changes if inventory validation fails.

### Duplicate request protection

If a service is already completed, repeating the completion request returns the existing invoice without deducting inventory a second time.

This behavior was verified during testing for service ID 4.

## 9. Invoice Calculation

The service-completion workflow calculates the invoice total using labour and parts costs.

When an invoice already exists, the implementation updates its total amount while preserving the existing payment status, payment method, and invoice date.

The database accepts these payment statuses:

- Unpaid
- Partially Paid
- Paid

Supported payment methods include:

- Cash
- UPI
- Card
- Bank Transfer

These fields support invoice record management. They do not indicate that an external payment gateway or online payment-processing integration is implemented.

## 10. API Reference

The principal backend endpoints documented here are:

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register a customer | Public registration |
| `POST` | `/api/auth/login` | Authenticate and obtain a JWT | Public |
| `GET` | `/api/auth/me` | Retrieve the authenticated account | Valid JWT |
| `POST` | `/api/admin/staff` | Create a staff account | Admin |
| `POST` | `/api/services/<service_id>/complete` | Complete an eligible service | Admin or assigned Mechanic |

Protected requests use the following authorization header:

```http
Authorization: Bearer <access_token>
```

The complete implementation in `application/backend/app.py` is the source of truth for additional routes, request fields, response formats, and error handling.

## 11. Installation and Setup

### Prerequisites

- Python
- MySQL Server
- MySQL Workbench (recommended for database setup and testing)
- Required backend packages
- The project database schema

### Step 1: Open the backend directory

```bash
cd application/backend
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure environment variables

Create a local `.env` file inside `application/backend/`:

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=VehicleServiceDB
JWT_SECRET_KEY=replace_with_a_strong_random_secret
```

Replace the example values with the credentials for your local environment.

### Step 5: Prepare the database

Create and populate `VehicleServiceDB` using the project's SQL scripts.

Ensure the schema contains the `UserAccount` table and the `PartUsage.StockDeducted` column required by the authentication and service-completion implementation.

Load sample data only when the appropriate SQL file is available. Use synthetic test data rather than real customer information.

### Step 6: Create the initial administrator

If an administrator account does not already exist, run:

```bash
python create_admin.py
```

Follow the script's configuration and input requirements.

### Step 7: Run the backend

```bash
python app.py
```

Use the host and port configured in the application. Configure the frontend to send API requests to that backend address.

## 12. Dependencies

The backend uses these third-party Python packages or libraries:

- Flask
- `mysql-connector-python`
- Flask-CORS
- Flask-JWT-Extended
- `python-dotenv`
- Werkzeug

The actual package versions should be maintained in `application/backend/requirements.txt`. Install dependencies from that file rather than relying on the list in this README alone.

## 13. Testing and Verification

The following results were observed during backend development:

| Test | Observed result |
|---|---|
| Authenticated request to `/api/auth/me` | Successful response with a valid token |
| Request to `/api/auth/me` without a token | HTTP 401 |
| Completion of service ID 4 | Successful |
| Invoice total for the tested service | ₹5,000.00 |
| Invoice payment status after completion | Remained Unpaid |
| Related appointment after completion | Marked Completed |
| Part usage after completion | `StockDeducted` marked true |
| Repeated completion of the same service | Existing invoice returned; no additional stock deduction |

The duplicate-completion test demonstrated that the same completed service was not processed twice.

The following areas still require separate verification before being described as fully tested:

- Insufficient-stock rollback
- Complete test coverage for all API routes
- Ownership and authorization checks across all relevant endpoints
- Integration with the final frontend

Only actual test results should be reported in the final submission.

## 14. Error Handling and Data Consistency

The backend uses JSON responses for API communication and applies database transactions to important multi-step operations, including staff account creation and service completion.

The service-completion workflow uses database locking and inventory validation to reduce the risk of conflicting stock updates. Repeated completion is handled to avoid duplicate stock deductions.

Refer to the final `app.py` implementation for the exact HTTP status codes and error response formats supported by each endpoint.

## 15. Security Considerations

- Store password hashes rather than plain-text passwords.
- Keep database credentials and the JWT secret in environment variables.
- Never commit `.env`, passwords, tokens, or sensitive customer information.
- Use role checks for protected operations.
- Use least-privilege MySQL credentials.
- Use HTTPS and appropriate secret management in a production deployment.
- Verify authorization and ownership checks on every sensitive endpoint before production use.

This project implements selected authentication and authorization functionality for academic use. A complete production security audit has not been established by the tests documented here.

## 16. Frontend Integration

The frontend is developed separately using React and Tailwind CSS.

The frontend should:

1. Send requests to the Flask API.
2. Send and receive JSON data.
3. Store and transmit the JWT according to the application's authentication design.
4. Include the bearer token for protected endpoints.
5. Display API validation and error responses appropriately.

The frontend and backend teams must align on endpoint URLs, request fields, response fields, role names, and authentication behavior.

## 17. Submission Checklist

Before submitting the branch, verify the following:

- [ ] `app.py` is committed.
- [ ] `create_admin.py` is committed.
- [ ] `requirements.txt` matches the imports used by the application.
- [ ] The SQL scripts needed to recreate the database are committed.
- [ ] The schema includes `UserAccount` and `PartUsage.StockDeducted`.
- [ ] Setup instructions match the actual application configuration.
- [ ] Test results reflect tests that were actually performed.
- [ ] `.env`, passwords, tokens, and other secrets are excluded from GitHub.
- [ ] Documentation, testing, and presentation folders contain the files actually prepared by the team.

## 18. Summary

The backend provides the application layer connecting the vehicle-service frontend to the MySQL database. Its implemented functionality includes customer authentication, JWT-protected account access, selected role-restricted staff and service operations, transactional service completion, inventory deduction, and invoice calculation.

The `backend` branch serves as the integration point for the backend code, database requirements, API documentation, and supporting test evidence for the Vehicle Service and Maintenance Management System.
