# Vehicle Service and Maintenance Management System
## Backend Technical Documentation

### 1. Overview
The backend provides REST API functionality for the Vehicle Service and Maintenance Management System. It uses Python, Flask, and MySQL to manage customer accounts, vehicles, service records, staff accounts, inventory usage, invoices, and revenue reports.

### 2. Technology Stack
- Python
- Flask REST API
- MySQL and MySQL Workbench
- mysql-connector-python
- python-dotenv for environment configuration
- Flask-JWT-Extended for JWT authentication
- Werkzeug password hashing
- Flask-CORS for frontend communication

### 3. Database Connectivity
Database connection settings are loaded from environment variables in a local `.env` file. Database operations use parameterized SQL queries to reduce SQL injection risk.

The `.env` file and local virtual environment must not be committed to the repository.

### 4. Authentication
Customer registration creates a customer profile and a linked user account. Passwords are stored as hashes rather than plaintext.

Successful login returns a signed JWT access token. Protected endpoints should validate the token and apply role-based authorization.

Supported roles include:
- Admin
- Mechanic
- Service Advisor
- Customer

Public registration must not allow users to assign themselves privileged roles.

### 5. Service Completion and Inventory
The service-completion API processes a service within a database transaction. It checks the service status, applies pending part usage, updates inventory, calculates labour and parts charges, updates the invoice, and marks the service and appointment completed.

The `PartUsage.StockDeducted` flag records whether the inventory deduction has already been applied. Repeated completion requests are tested to ensure they do not deduct stock twice.

### 6. Invoice Calculation
The invoice total is calculated using:

Invoice Total = Total Labour Cost + Total Parts Cost

Labour is aggregated from `ServiceTask.LaborCost`. Parts cost is calculated from `PartUsage.QuantityUsed × PartUsage.UnitPrice`.

Existing invoice payment information should be preserved when updating the calculated total.

### 7. API Error Handling
The API uses HTTP status codes to indicate success and failure, including:
- 200: successful request
- 201: resource created
- 400: invalid input
- 401: missing or invalid authentication
- 403: insufficient permissions
- 404: resource not found
- 409: conflict, such as insufficient inventory
- 500 or 503: server or database failure

### 8. Testing
The backend has been tested for customer registration and login, JWT verification, service completion, invoice values, and repeated completion requests. Further testing should verify insufficient-stock rollback and ownership restrictions.

### 9. Running the Backend
1. Install dependencies from `requirements.txt`.
2. Configure database credentials and a JWT signing key in a local `.env` file.
3. Ensure MySQL is running and the database schema has been installed.
4. Run `python app.py`.
5. Test the health endpoint at `/api/health`.

### 10. Security Notes
This is a college project implementation. Before production use, complete and verify authorization and ownership checks on every sensitive endpoint, configure production-grade secrets, and use a production WSGI server.
