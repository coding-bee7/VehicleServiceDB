# Vehicle Service Management System (AutoDB)

A database-backed vehicle workshop management application built for the **VehicleServiceDB** DBMS project. It combines a React/Vite web interface, a Flask REST API, and a MySQL relational database.

The application models the core workshop lifecycle: customer and vehicle records, appointment booking, service assignment, mechanic inspection, customer estimate approval, work completion, spare-parts inventory, invoicing, and payment tracking.

> **Project status:** The source code and UI/API structure are in the repository, and the configured CI workflow checks frontend lint/build and backend Python syntax. Those checks do **not** prove that a local MySQL database is configured correctly or that every complete workflow has passed end-to-end testing. See [Validation and known limitations](#validation-and-known-limitations).

## Contents

- [Features](#features)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Application workflow](#application-workflow)
- [Database design and SQL files](#database-design-and-sql-files)
- [Local setup](#local-setup)
- [Run the application](#run-the-application)
- [API overview](#api-overview)
- [Validation and known limitations](#validation-and-known-limitations)
- [Git workflow](#git-workflow)
- [Security and configuration notes](#security-and-configuration-notes)

## Features

### Customer
- Register and sign in.
- Maintain vehicle information.
- Book service appointments and provide a complaint/description.
- View a dashboard, upcoming appointment, and service history.
- Review mechanic inspection findings and proposed estimates.
- Approve or reject a proposed estimate. A rejection can include a reason, which is available to the mechanic for follow-up.
- View invoice summaries and invoice details.

### Mechanic
- View assigned services and available spare parts.
- Record inspection findings, odometer reading, recommended work, labour charges, and estimated parts.
- Submit an estimate for the customer's decision.
- Start a service only after the estimate has been approved.
- Record the actual parts consumed and work performed.
- Complete the service so the backend can calculate the final charge, update inventory, and create/update the invoice.

### Administrator and workshop staff
- View the administrative dashboard and revenue report.
- Review appointments and assign mechanics.
- Manage spare-parts inventory: add parts, update part details and prices, set reorder levels, and receive stock.
- Monitor low-stock items.
- Access invoice and payment-related API operations. Payment-related database setup has a known gap noted below.

### Workflow safeguards in the backend
- JWT-based authentication, password hashing, and role checks on protected routes.
- Customer estimate states: Proposed, Approved, and Rejected.
- A service cannot be started without an approved estimate.
- Mechanics record actual parts before completing the service; actual quantities are checked against the approved estimate.
- Stock deduction is tracked with a `StockDeducted` flag to prevent the same usage row from being deducted repeatedly.
- Service completion uses a database transaction for inventory/invoice updates.

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, JavaScript, CSS |
| 3D vehicle scene | Three.js, React Three Fiber, Drei |
| Backend | Python, Flask, Flask-CORS |
| Authentication | Flask-JWT-Extended, Werkzeug password hashing |
| Database driver | mysql-connector-python |
| Configuration | python-dotenv and local environment files |
| Database | MySQL |
| CI validation | GitHub Actions, Node.js 22, Python 3.12 |

## Repository structure

```text
VehicleServiceDB/
├── .github/
│   └── workflows/
│       └── mvp-validation.yml        # Frontend lint/build + backend syntax check
├── application/
│   ├── README.md                     # Application area note
│   ├── backend/
│   │   ├── app.py                    # Flask API, authentication, business rules
│   │   ├── create_admin.py           # Interactive admin-account creation helper
│   │   ├── create_missing_mechanic_accounts.py
│   │   │                               # Data-specific mechanic-account helper
│   │   └── requirements.txt           # Python dependencies
│   └── frontend/
│       ├── package.json              # npm scripts and frontend dependencies
│       ├── package-lock.json          # Locked frontend dependency tree
│       ├── vite.config.js             # Vite configuration
│       ├── index.html                 # Frontend HTML entry point
│       ├── public/
│       │   ├── favicon.svg
│       │   ├── icons.svg
│       │   ├── images/autodb-car.png  # Vehicle imagery
│       │   └── models/porsche.glb     # 3D model used by the UI
│       └── src/
│           ├── main.jsx               # React entry point
│           ├── App.jsx                # Main pages and role-specific views
│           ├── App.css                # Page and component styling
│           ├── index.css              # Global styles
│           ├── CarScene.jsx            # 3D vehicle scene
│           ├── assets/                 # Frontend assets
│           └── services/api.js         # Centralized HTTP/API adapter
├── database/
│   ├── README.md
│   ├── schema.sql                     # Core relational schema
│   ├── user_account.sql               # Authentication account table
│   ├── sample_data.sql                # Example workshop records
│   ├── inspection_estimate_migration.sql
│   │                                   # Inspection/estimate tables + workflow columns
│   ├── queries.sql                    # Inventory and invoice checks; includes state-changing SQL
│   ├── morequeries.sql                # Mixed investigation/manual SQL snippets
│   └── service_completion_verification.sql
│                                       # Targeted service/invoice/stock verification queries
├── documentation/
│   └── README.md                      # Documentation area placeholder
├── presentation/
│   └── README.md                      # Presentation area placeholder
├── testing/
│   └── README.md                      # Testing area placeholder
└── README.md                          # This guide
```

The `documentation/`, `presentation/`, and `testing/` folders currently contain README placeholders rather than a complete report, slide deck, or automated test suite. Keep project reports, diagrams, slides, and test evidence in those locations as they are produced.

## Application workflow

1. **Set up the database** with the core schema and authentication table.
2. **Register or sign in** to obtain an access token; protected API calls send it in the `Authorization: Bearer <token>` header.
3. **Create a customer vehicle and appointment.** Workshop staff can review appointments and assign mechanics.
4. **Inspect the vehicle.** The mechanic records findings, odometer reading, recommended tasks, labour, and estimated parts.
5. **Obtain customer approval.** The customer approves or rejects the estimate. A rejection reason can be reviewed by the mechanic before revising and resubmitting the estimate.
6. **Perform the service.** An approved estimate is required to start work. The mechanic records actual parts used and work performed.
7. **Complete and invoice.** The backend finalizes the service, applies eligible stock deductions, and creates or updates the invoice.
8. **Review billing and stock.** Customers can inspect invoices; authorized workshop users can use the billing endpoints and manage inventory.

## Database design and SQL files

The database name used by the backend is `VehicleServiceDB`. The core schema defines these main entities:

- `Customer`, `Vehicle`, and `Employee`
- `ServiceType`, `Appointment`, `ServiceRecord`, and `ServiceTask`
- `Part` and `PartUsage`
- `Invoice`

Additional scripts extend the core structure:

| File | Purpose | Usage notes |
| --- | --- | --- |
| `database/schema.sql` | Creates the database and the core tables. | Run first on a new local development database. |
| `database/user_account.sql` | Creates `UserAccount`, which stores role, password hash, and links to customer/employee records. | Run after `schema.sql`. |
| `database/inspection_estimate_migration.sql` | Creates `ServiceInspection`, `ServiceEstimate`, and `ServiceEstimatePart`; conditionally adds `PartUsage.StockDeducted`, `ServiceRecord.ActualPartsConfirmed`, and `ServiceRecord.WorkPerformed`. | Run after the core schema. Back up an existing database first. It is designed to be rerunnable for the listed tables/columns, but still inspect the target database before applying it. |
| `database/sample_data.sql` | Inserts example customers, vehicles, employees, appointments, services, parts, and invoices. | Optional; intended for a clean test database. It contains fixed IDs and should not be re-run on an already populated database. |
| `database/service_completion_verification.sql` | Queries service, invoice, part usage, and stock state for example IDs. | Read and update the example IDs for the record being investigated. |
| `database/queries.sql` | Inventory/invoice audit queries and stock-related SQL. | **Do not run the whole file as setup.** It contains a non-idempotent `ALTER TABLE` and a transaction that can deduct stock. |
| `database/morequeries.sql` | Accumulated inspection, troubleshooting, sample insert, and schema-adjustment SQL. | **Not a clean install script.** Review and select individual statements; it includes data-changing statements and `ALTER TABLE` operations. |

### Important schema note

The backend defines payment-history and invoice-payment routes that query a `Payment` table. The committed `schema.sql`, `user_account.sql`, and inspection/estimate migration do not create that table, and the mixed manual query file is not a reliable migration for it. **Before using payment recording/history endpoints on a fresh database, add and apply a reviewed migration that creates the required `Payment` table and its foreign keys.** The core `Invoice` table exists, but that alone does not create a payment ledger.

## Local setup

### Prerequisites

- Git
- MySQL server and a client such as MySQL Workbench
- Python 3.12 recommended (the CI syntax check uses Python 3.12)
- Node.js 22 and npm (the CI workflow uses Node.js 22)

### 1. Get the project

```bash
git clone https://github.com/coding-bee7/VehicleServiceDB.git
cd VehicleServiceDB
git checkout main
```

### 2. Create the database

For a new local development database, execute the SQL files in this order using MySQL Workbench or the MySQL command-line client:

1. `database/schema.sql`
2. `database/user_account.sql`
3. `database/inspection_estimate_migration.sql`
4. Optionally, `database/sample_data.sql` for example records

For example, from a POSIX shell with the MySQL client installed:

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/user_account.sql
mysql -u root -p < database/inspection_estimate_migration.sql
# Optional, only on a clean test database:
mysql -u root -p < database/sample_data.sql
```

Use your own local database credentials. Back up a database before applying a migration to an existing instance. Do not run `queries.sql` or `morequeries.sql` wholesale.

### 3. Configure the Flask backend

Create `application/backend/.env` locally. Do not commit this file.

```dotenv
JWT_SECRET_KEY=replace_with_a_long_random_secret
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_local_mysql_password
DB_NAME=VehicleServiceDB
```

Generate a strong secret rather than reusing the example value. The code requires `JWT_SECRET_KEY` at startup; the database settings above match the names read by `app.py`. The backend defaults to host `localhost`, port `3306`, user `root`, and database `VehicleServiceDB` when the optional database values are not set. Set a password matching your own MySQL configuration.

Install dependencies and launch the API:

```bash
cd application/backend
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

The backend uses Flask, Flask-CORS, Flask-JWT-Extended, mysql-connector-python, and python-dotenv. Keep the terminal running while using the frontend. If the API reports a missing table/column, verify that the correct SQL setup and migration steps have been applied.

### 4. Configure and launch the frontend

Create `application/frontend/.env` locally with the API's base URL:

```dotenv
VITE_API_BASE_URL=http://localhost:5000/api
```

The Vite configuration currently does not define a development proxy. Setting the full local API URL lets the browser call Flask directly; the backend CORS configuration permits common local frontend origins, including `localhost:5173` and `127.0.0.1:5173`.

Install and run the frontend in a separate terminal:

```bash
cd application/frontend
npm install
npm run dev
```

Open the URL printed by Vite (usually `http://localhost:5173`). Restart Vite after changing the frontend `.env` file. On Windows PowerShell, use `npm.cmd install` and `npm.cmd run dev` if PowerShell blocks the npm command shim.

## API overview

The API is implemented in `application/backend/app.py`; the frontend's HTTP adapter is in `application/frontend/src/services/api.js`.

| Area | Representative endpoints |
| --- | --- |
| Health | `GET /api/health` |
| Authentication | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` |
| Customer | `GET /api/customer/dashboard`, `GET /api/customer/next-appointment`, `GET/POST /api/customer/vehicles`, `GET /api/customer/services`, `GET /api/customer/estimates`, `POST /api/customer/estimates/{estimate_id}/decision`, `GET /api/customer/invoices` |
| Appointments and services | `POST /api/appointments`, `GET /api/services`, `PATCH /api/services/{service_id}/status` |
| Mechanic | `GET /api/mechanic/services`, `GET /api/mechanic/parts`, `POST /api/services/{service_id}/estimate`, `POST /api/services/{service_id}/start`, `POST /api/services/{service_id}/actual-parts`, `POST /api/services/{service_id}/complete` |
| Administration | `GET /api/admin/dashboard`, `GET/POST /api/admin/parts`, `PATCH /api/admin/parts/{part_id}`, `POST /api/admin/parts/{part_id}/stock`, appointment and mechanic-management endpoints |
| Reporting and billing | `GET /api/reports/revenue`, `GET /api/invoices`, `GET /api/invoices/{invoice_id}`, `GET /api/payments`, `POST /api/invoices/{invoice_id}/payments` |

The exact access requirements and request/response fields are defined in the backend implementation. Use an authenticated token for protected routes; do not rely on frontend navigation alone as a security boundary.

## Validation and known limitations

- `.github/workflows/mvp-validation.yml` defines frontend dependency installation, ESLint, Vite production build, and Python syntax compilation of `application/backend/app.py`.
- Those CI steps do not start MySQL, apply database scripts, or run browser/API end-to-end tests.
- `testing/` currently contains only a placeholder README; no dedicated automated database integration test suite is present in the tracked tree.
- The `Payment` table is referenced by backend payment endpoints but is not created by the committed schema/migrations; see [Database design and SQL files](#database-design-and-sql-files).
- The helper `create_missing_mechanic_accounts.py` contains fixed employee IDs/names and validation assumptions. Inspect its target records and adjust it for your own database before running it.
- Use a fresh local database for sample data. SQL in the mixed query files can change records, table definitions, or stock quantities.

Run the frontend checks locally before submitting changes:

```bash
cd application/frontend
npm ci
npm run lint
npm run build
```

Run the backend syntax check from the repository root:

```bash
python -m py_compile application/backend/app.py
```

These commands validate frontend lint/build and backend syntax only; they do not replace manual verification with a configured MySQL database.

## Git workflow

- `main`: main project branch.
- `integration`: shared branch for bringing together frontend, backend, and database work.
- Feature branches: use a short-lived branch for a focused change, then open a pull request into `integration`.
- Review the resulting integration state before proposing it for `main`.
- Keep credentials, local `.env` files, virtual environments, `node_modules/`, and other local-only files out of commits.
- Write commit messages that describe the change and include setup/migration notes when database files change.

## Security and configuration notes

- Never commit a real database password, JWT secret, access token, or other credentials.
- Use a unique strong `JWT_SECRET_KEY` for each local/deployed environment.
- Passwords are stored as hashes; do not insert plaintext passwords into `UserAccount.PasswordHash`.
- Keep authorization checks in Flask. Frontend route selection is for user experience, not enforcement.
- The current CORS allowlist is configured in `application/backend/app.py`; add the deployed frontend origin deliberately when deploying, rather than opening CORS to every origin.
- Before deploying publicly, review production server configuration, HTTPS, secrets management, database privileges, input validation, logging, and the outstanding schema/test gaps above.
