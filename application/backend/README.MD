# Vehicle Service and Maintenance Management System — Backend

## 1. Project Overview

The Vehicle Service and Maintenance Management System is a DBMS project designed to manage vehicle service appointments, service records, employees, spare parts, inventory usage, invoices, and payments.

This repository branch contains the backend application, implemented using **Python, Flask, and MySQL**. It exposes REST API endpoints for communication with the frontend and database.

## 2. Technology Stack

| Component | Technology |
|---|---|
| Backend language | Python |
| Web framework | Flask |
| API architecture | REST API |
| Database | MySQL |
| Database connector | `mysql-connector-python` |
| Frontend integration | React with Tailwind CSS |
| Cross-origin requests | Flask-CORS |
| Authentication | JWT |
| Password hashing | Werkzeug security utilities |
| Configuration | Environment variables using `.env` |
| Backend development | Visual Studio Code |
| Database management | MySQL Workbench |

Tailwind CSS is used for frontend styling; it is not part of the Flask backend.

## 3. Backend Architecture

The application follows a three-layer architecture:

```text
React + Tailwind CSS Frontend
              |
              | HTTP requests / JSON responses
              v
       Flask REST API
              |
              | MySQL Connector
              v
        MySQL Database
         VehicleServiceDB
```

The frontend communicates with the Flask API. The API validates incoming requests, applies application logic, interacts with MySQL, and returns JSON responses.

## 4. Project Structure

The backend files are organized under `application/backend/`.

```text
VehicleServiceDB/
├── application/
│   └── backend/
│       ├── app.py
│       ├── create_admin.py
│       ├── requirements.txt
│       ├── .env                 # Local only; do not commit
│       └── README.md
├── database/
│   ├── schema.sql
│   ├── sample_data.sql
│   └── queries.sql
├── documentation/
└── testing/
```

The database and documentation filenames above describe the intended repository organization. Include only files that have actually been created and committed to the branch.

## 5. Database

**Database name:** `VehicleServiceDB`

The backend uses MySQL to store and retrieve application data.

The database includes tables for the project's main entities, such as:

- Customers
- Vehicles
- Appointments
- Employees
- Service records
- Service tasks
- Parts
- Part usage
- Invoices
- User accounts

The exact columns, keys, constraints, and relationships are defined in the database SQL scripts.

### UserAccount

The `UserAccount` table supports application login and links accounts to customer or employee records.

Its fields include:

- `UserID` — primary key
- `Email` — unique email address
- `PasswordHash` — hashed password
- `Role` — account role
- `CustomerID` — optional customer reference
- `EmployeeID` — optional employee reference
- `IsActive` — account activation status
- `CreatedAt` — account creation timestamp

The table's constraints associate customer accounts with customers and staff accounts with employees.

## 6. Authentication and Authorization

### Registration

`POST /api/auth/register`

Registers a customer account. The registration endpoint assigns the Customer role rather than allowing public registration as an administrator or staff member.

Passwords are hashed using Werkzeug security utilities before storage. Plain-text passwords are not intended to be stored in the database.

### Login

`POST /api/auth/login`

Validates the submitted email and password. Successful authentication returns a JWT access token.

The token is configured to expire after two hours and includes role and relevant customer or employee identity claims.

### Current Account

`GET /api/auth/me`

Returns information associated with the authenticated account. This endpoint requires a valid JWT.

### Role-Based Access

The backend uses a `role_required` decorator to restrict selected endpoints to permitted roles.

The implemented protected operations include:

- **Admin:** create staff accounts.
- **Admin or Mechanic:** complete eligible service records.

Mechanic service completion also checks the assigned mechanic against the authenticated employee. Other endpoints should be reviewed individually before assuming they enforce ownership or role restrictions.

## 7. Staff Account Management

`POST /api/admin/staff`

This protected endpoint allows an administrator to create staff accounts.

Supported staff roles are:

- Mechanic
- Service Advisor

Staff creation associates an employee record with a user account. The operation uses a database transaction to avoid leaving an employee record without its corresponding account if account creation fails.

### Initial Administrator

`create_admin.py` is a one-time local setup script for creating the initial administrator account when one does not already exist.

Run it only after configuring the database and reviewing its prompts or configuration. Use a strong, unique password and keep credentials out of version control.

## 8. Service Completion and Inventory Management

`POST /api/services/<service_id>/complete`

This protected endpoint completes an eligible service record and updates related database records within a transaction.

The implemented workflow includes:

1. Lock and retrieve the service record.
2. Check the caller's role and, for a mechanic, the assigned employee.
3. Check that the service is eligible for completion.
4. Lock pending part-usage records and the corresponding part records.
5. Verify that sufficient inventory is available.
6. Deduct used quantities from part stock.
7. Mark the applicable part-usage records as stock-deducted.
8. Calculate labour and parts costs.
9. Create or update the associated invoice.
10. Mark the service record and appointment as completed.
11. Commit the transaction.

If an inventory validation fails, the operation is designed to roll back its database changes.

### Duplicate Completion Protection

The completion endpoint checks whether the service is already completed. Repeating the request for an already completed service returns the existing invoice without deducting stock a second time.

The `PartUsage.StockDeducted` field records whether a usage entry has already been applied to inventory.

## 9. Invoice Handling

Each service record is associated with an invoice through the database relationship.

The completion workflow calculates the invoice total using labour and parts costs. When updating an existing invoice, the implementation updates the total amount while preserving the existing payment status, payment method, and invoice date.

The supported payment-status values defined for the invoice table are:

- Unpaid
- Partially Paid
- Paid

The supported payment methods are:

- Cash
- UPI
- Card
- Bank Transfer

These values describe the database's accepted invoice fields; they do not imply that a payment gateway or online payment processing system is integrated.

## 10. Environment Configuration

Create a local `.env` file in the backend directory.

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=VehicleServiceDB
JWT_SECRET_KEY=replace_with_a_strong_random_secret
```

Replace the example values with your local MySQL credentials. Use a strong, private JWT secret.

**Never commit `.env`, database passwords, JWT secrets, real customer data, or other credentials to GitHub.**

## 11. Installation and Running

Prerequisites:

- Python installed
- MySQL Server installed and running
- `VehicleServiceDB` created using the project's database scripts
- Required Python packages installed

### Step 1: Open the backend directory

```bash
cd application/backend
```

### Step 2: Create a virtual environment (recommended)

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

### Step 4: Configure the environment

Create the `.env` file using the configuration in Section 10.

### Step 5: Prepare the database

Create the `VehicleServiceDB` database and execute the schema SQL script. Load sample data only if it is available and appropriate for your environment.

Ensure the database includes the `UserAccount` table and the `PartUsage.StockDeducted` column required by the implemented authentication and service-completion logic.

### Step 6: Create the initial administrator

Run the local administrator setup script if an administrator account has not already been created:

```bash
python create_admin.py
```

### Step 7: Start the Flask application

```bash
python app.py
```

Use the host and port configured by the application. The frontend must be configured to send requests to the running backend address.

## 12. Dependencies

The backend dependency list is maintained in `requirements.txt`. The application uses the following packages or libraries:

- Flask
- mysql-connector-python
- Flask-CORS
- Flask-JWT-Extended
- python-dotenv
- Werkzeug

Install the versions recorded in `requirements.txt` to reproduce the project's environment.

## 13. Testing and Verification

The following behavior has been tested during backend development:

| Test | Observed result |
|---|---|
| Authenticated request to `/api/auth/me` | Successful response with a valid token |
| Request to `/api/auth/me` without a token | HTTP 401 response |
| Service completion for service ID 4 | Successful completion |
| Invoice creation/update during the tested completion | Invoice total of ₹5,000.00 |
| Invoice payment status after tested completion | Remained Unpaid |
| Related appointment after tested completion | Marked Completed |
| Part usage after tested completion | `StockDeducted` marked true |
| Repeated completion of the same service | Returned the existing invoice without additional stock deduction |

The service-completion test demonstrates that the same completed service was not processed twice.

Insufficient-stock rollback, complete endpoint coverage, and ownership restrictions on every relevant endpoint require separate verification before being reported as fully tested.

## 14. API Reference

The principal endpoints documented in this README are:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/auth/register` | Register a customer account |
| `POST` | `/api/auth/login` | Authenticate and obtain a JWT |
| `GET` | `/api/auth/me` | Retrieve the authenticated account |
| `POST` | `/api/admin/staff` | Create a staff account; Admin only |
| `POST` | `/api/services/<service_id>/complete` | Complete an eligible service; Admin or assigned Mechanic |

Protected endpoints require the authorization header:

```http
Authorization: Bearer <access_token>
```

Refer to `app.py` for the complete implementation and the exact request fields, response formats, and additional routes.

## 15. Security Notes

- Passwords are stored as hashes, not plain text.
- JWT authentication protects selected endpoints.
- Role-based checks restrict selected administrative and service operations.
- Database transactions protect multi-step operations such as staff creation and service completion.
- Environment variables hold database credentials and the JWT secret.
- Secrets and real customer information must not be committed to the repository.
- Production deployment should use HTTPS, secure secret management, restricted database permissions, and appropriate input validation.

## 16. Project Scope

This backend supports the database and application logic for vehicle servicing, inventory usage, invoice calculation, and account authentication.

The frontend is maintained separately and uses React with Tailwind CSS. The frontend and backend must agree on API routes, JSON fields, authentication headers, and error handling.

## 17. Maintainer Notes

Before final submission:

- Confirm `requirements.txt` matches the packages imported by `app.py`.
- Confirm the SQL schema recreates the database required by the backend.
- Keep real credentials and `.env` out of GitHub.
- Include only test results that were actually observed.
- Verify the documented endpoint list against the final `app.py`.
