from functools import wraps
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (create_access_token, JWTManager, jwt_required,get_jwt, get_jwt_identity)
import os
import re
from datetime import date, datetime
from decimal import Decimal

import mysql.connector
from mysql.connector import IntegrityError, Error
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS


load_dotenv()

# Create the Flask application FIRST
app = Flask(__name__)

# Configure JWT
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("JWT_SECRET_KEY is missing from .env")

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)


jwt = JWTManager(app)

CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    }
})

# Permit common local frontend development ports.
# Add your teammate's actual origin if it differs.



def get_connection():
    """Open a new MySQL connection using .env settings."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "VehicleServiceDB"),
        connection_timeout=5,
    )


def json_safe(value):
    """Convert MySQL date and decimal values into JSON-safe values."""
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def error_response(message, status_code):
    return jsonify({"error": message}), status_code


def role_required(*allowed_roles):
    """Allow only authenticated users with specified roles."""
    def decorator(view_function):
        @wraps(view_function)
        @jwt_required()
        def wrapped(*args, **kwargs):
            claims = get_jwt()

            if claims.get("role") not in allowed_roles:
                return jsonify({
                    "error": "You do not have permission to perform this action"
                }), 403

            return view_function(*args, **kwargs)

        return wrapped
    return decorator


def read_json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def valid_email(email):
    return (
        email is None
        or email == ""
        or (
            len(email) <= 100
            and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
        ) is not None
    )


def fetch_all(sql, params=()):
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        return json_safe(cursor.fetchall())
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def fetch_one(sql, params=()):
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        result = cursor.fetchone()
        return json_safe(result)
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


@app.get("/")
def home():
    return jsonify({
        "message": "Vehicle Service Management API",
        "api_health": "/api/health"
    })


# Check that Flask can reach MySQL.
@app.get("/api/health")
def health():
    try:
        result = fetch_one("SELECT DATABASE() AS database_name")
        return jsonify({
            "status": "ok",
            "database": result["database_name"]
        })
    except Error:
        app.logger.exception("Database health check failed")
        return error_response("Database connection failed", 503)


# ---------------- CUSTOMERS ----------------

@app.get("/api/customers")
def list_customers():
    try:
        customers = fetch_all("""
            SELECT CustomerID, Name, Phone, Email, Address, CreatedAt
            FROM Customer
            ORDER BY CustomerID
        """)
        return jsonify(customers)
    except Error:
        app.logger.exception("Could not list customers")
        return error_response("Could not retrieve customers", 500)


@app.get("/api/customers/<int:customer_id>")
def get_customer(customer_id):
    try:
        customer = fetch_one("""
            SELECT CustomerID, Name, Phone, Email, Address, CreatedAt
            FROM Customer
            WHERE CustomerID = %s
        """, (customer_id,))

        if customer is None:
            return error_response("Customer not found", 404)

        return jsonify(customer)
    except Error:
        app.logger.exception("Could not retrieve customer")
        return error_response("Could not retrieve customer", 500)


@app.post("/api/customers")
def create_customer():
    data = read_json()
    if data is None:
        return error_response("Send a valid JSON object", 400)

    name = data.get("Name")
    phone = data.get("Phone")
    email = data.get("Email") or None
    address = data.get("Address") or None

    if not isinstance(name, str) or not name.strip():
        return error_response("Name is required", 400)
    if len(name.strip()) > 100:
        return error_response("Name must be at most 100 characters", 400)
    if not isinstance(phone, str) or not phone.strip():
        return error_response("Phone is required", 400)
    if len(phone.strip()) > 15:
        return error_response("Phone must be at most 15 characters", 400)
    if email is not None and not isinstance(email, str):
        return error_response("Email must be a string", 400)
    if not valid_email(email):
        return error_response("Enter a valid email address", 400)
    if address is not None and (
        not isinstance(address, str) or len(address) > 255
    ):
        return error_response("Address must be at most 255 characters", 400)

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO Customer (Name, Phone, Email, Address)
            VALUES (%s, %s, %s, %s)
        """, (name.strip(), phone.strip(), email, address))
        customer_id = cursor.lastrowid
        connection.commit()

        customer = fetch_one("""
            SELECT CustomerID, Name, Phone, Email, Address, CreatedAt
            FROM Customer
            WHERE CustomerID = %s
        """, (customer_id,))

        return jsonify(customer), 201

    except IntegrityError:
        if connection:
            connection.rollback()
        return error_response(
            "Phone number or email already exists", 409
        )
    except Error:
        if connection:
            connection.rollback()
        app.logger.exception("Could not create customer")
        return error_response("Could not create customer", 500)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.put("/api/customers/<int:customer_id>")
def update_customer(customer_id):
    data = read_json()
    if data is None:
        return error_response("Send a valid JSON object", 400)

    name = data.get("Name")
    phone = data.get("Phone")
    email = data.get("Email") or None
    address = data.get("Address") or None

    if not isinstance(name, str) or not name.strip():
        return error_response("Name is required", 400)
    if len(name.strip()) > 100:
        return error_response("Name must be at most 100 characters", 400)
    if not isinstance(phone, str) or not phone.strip():
        return error_response("Phone is required", 400)
    if len(phone.strip()) > 15:
        return error_response("Phone must be at most 15 characters", 400)
    if email is not None and not isinstance(email, str):
        return error_response("Email must be a string", 400)
    if not valid_email(email):
        return error_response("Enter a valid email address", 400)
    if address is not None and (
        not isinstance(address, str) or len(address) > 255
    ):
        return error_response("Address must be at most 255 characters", 400)

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE Customer
            SET Name = %s, Phone = %s, Email = %s, Address = %s
            WHERE CustomerID = %s
        """, (
            name.strip(), phone.strip(), email, address, customer_id
        ))

        if cursor.rowcount == 0:
            # Distinguish a missing ID from an unchanged record.
            cursor.execute(
                "SELECT CustomerID FROM Customer WHERE CustomerID = %s",
                (customer_id,)
            )
            if cursor.fetchone() is None:
                connection.rollback()
                return error_response("Customer not found", 404)

        connection.commit()

        customer = fetch_one("""
            SELECT CustomerID, Name, Phone, Email, Address, CreatedAt
            FROM Customer
            WHERE CustomerID = %s
        """, (customer_id,))
        return jsonify(customer)

    except IntegrityError:
        if connection:
            connection.rollback()
        return error_response(
            "Phone number or email already exists", 409
        )
    except Error:
        if connection:
            connection.rollback()
        app.logger.exception("Could not update customer")
        return error_response("Could not update customer", 500)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.delete("/api/customers/<int:customer_id>")
def delete_customer(customer_id):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM Customer WHERE CustomerID = %s",
            (customer_id,)
        )

        if cursor.rowcount == 0:
            connection.rollback()
            return error_response("Customer not found", 404)

        connection.commit()
        return jsonify({"message": "Customer deleted successfully"})

    except IntegrityError:
        if connection:
            connection.rollback()
        return error_response(
            "Cannot delete customer: related vehicle or service records exist",
            409
        )
    except Error:
        if connection:
            connection.rollback()
        app.logger.exception("Could not delete customer")
        return error_response("Could not delete customer", 500)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# ---------------- VEHICLES ----------------

@app.get("/api/vehicles")
def list_vehicles():
    try:
        vehicles = fetch_all("""
            SELECT
                v.VehicleID,
                v.CustomerID,
                c.Name AS CustomerName,
                v.RegistrationNo,
                v.Brand,
                v.Model,
                v.ManufactureYear,
                v.FuelType
            FROM Vehicle v
            JOIN Customer c ON c.CustomerID = v.CustomerID
            ORDER BY v.VehicleID
        """)
        return jsonify(vehicles)
    except Error:
        app.logger.exception("Could not list vehicles")
        return error_response("Could not retrieve vehicles", 500)


# ---------------- SERVICE RECORDS ----------------

@app.get("/api/services")
def list_services():
    try:
        services = fetch_all("""
            SELECT
                sr.ServiceID,
                sr.AppointmentID,
                c.Name AS CustomerName,
                v.RegistrationNo,
                v.Brand,
                v.Model,
                a.AppointmentDate,
                a.Complaint,
                e.Name AS MechanicName,
                sr.StartDate,
                sr.EndDate,
                sr.Odometer,
                sr.Status
            FROM ServiceRecord sr
            JOIN Appointment a
                ON a.AppointmentID = sr.AppointmentID
            JOIN Vehicle v
                ON v.VehicleID = a.VehicleID
            JOIN Customer c
                ON c.CustomerID = v.CustomerID
            LEFT JOIN Employee e
                ON e.EmployeeID = sr.MechanicID
            ORDER BY sr.ServiceID
        """)
        return jsonify(services)
    except Error:
        app.logger.exception("Could not list services")
        return error_response("Could not retrieve services", 500)


@app.patch("/api/services/<int:service_id>/status")
def update_service_status(service_id):
    data = read_json()
    if data is None:
        return error_response("Send a valid JSON object", 400)

    status = data.get("Status")
    allowed_statuses = {"Pending", "In Progress", "Completed"}

    if not isinstance(status, str) or status not in allowed_statuses:
        return error_response(
            "Status must be Pending, In Progress, or Completed", 400
        )

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT ServiceID, AppointmentID, Status
            FROM ServiceRecord
            WHERE ServiceID = %s
        """, (service_id,))
        service = cursor.fetchone()

        if service is None:
            connection.rollback()
            return error_response("Service record not found", 404)

        if status == "Completed":
            cursor.execute("""
                UPDATE ServiceRecord
                SET Status = %s,
                    EndDate = COALESCE(EndDate, CURRENT_TIMESTAMP)
                WHERE ServiceID = %s
            """, (status, service_id))

            cursor.execute("""
                UPDATE Appointment
                SET Status = 'Completed'
                WHERE AppointmentID = %s
            """, (service["AppointmentID"],))
        else:
            cursor.execute("""
                UPDATE ServiceRecord
                SET Status = %s
                WHERE ServiceID = %s
            """, (status, service_id))

        connection.commit()

        cursor.execute("""
            SELECT ServiceID, AppointmentID, Status, StartDate, EndDate
            FROM ServiceRecord
            WHERE ServiceID = %s
        """, (service_id,))
        updated = json_safe(cursor.fetchone())
        return jsonify(updated)

    except Error:
        if connection:
            connection.rollback()
        app.logger.exception("Could not update service status")
        return error_response("Could not update service status", 500)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# ---------------- REVENUE REPORT ----------------

@app.get("/api/reports/revenue")
@role_required("Admin")
def revenue_report():
    year_text = request.args.get("year")
    params = ()

    sql = """
        SELECT
            YEAR(InvoiceDate) AS Year,
            MONTH(InvoiceDate) AS Month,
            COUNT(*) AS PaidInvoiceCount,
            SUM(TotalAmount) AS TotalRevenue
        FROM Invoice
        WHERE PaymentStatus = 'Paid'
    """

    if year_text is not None:
        if not year_text.isdigit() or not 2000 <= int(year_text) <= 2100:
            return error_response("Year must be between 2000 and 2100", 400)
        sql += " AND YEAR(InvoiceDate) = %s"
        params = (int(year_text),)

    sql += """
        GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        ORDER BY Year, Month
    """

    try:
        rows = fetch_all(sql, params)
        total = round(sum(row["TotalRevenue"] or 0 for row in rows), 2)
        return jsonify({
            "year_filter": int(year_text) if year_text else None,
            "total_paid_revenue": total,
            "monthly_breakdown": rows
        })
    except Error:
        app.logger.exception("Could not generate revenue report")
        return error_response("Could not generate revenue report", 500)


@app.errorhandler(404)
def not_found(_error):
    return error_response("Endpoint not found", 404)


@app.errorhandler(405)
def method_not_allowed(_error):
    return error_response("HTTP method not allowed", 405)


# ---------------- AUTHENTICATION ----------------

@app.post("/api/auth/register")
def register_customer():
    data = read_json()

    if data is None:
        return error_response("Send a valid JSON object", 400)

    name = data.get("Name")
    phone = data.get("Phone")
    email = data.get("Email")
    password = data.get("Password")
    address = data.get("Address") or None

    if not isinstance(name, str) or not name.strip():
        return error_response("Name is required", 400)

    name = name.strip()
    if len(name) > 100:
        return error_response("Name must be at most 100 characters", 400)

    if not isinstance(phone, str) or not phone.strip():
        return error_response("Phone is required", 400)

    phone = phone.strip()
    if len(phone) > 15:
        return error_response("Phone must be at most 15 characters", 400)

    if not isinstance(email, str):
        return error_response("Email is required", 400)

    email = email.strip().lower()
    if not valid_email(email) or not email:
        return error_response("Enter a valid email address", 400)

    if not isinstance(password, str) or len(password) < 8:
        return error_response(
            "Password must be at least 8 characters", 400
        )

    if len(password) > 128:
        return error_response("Password is too long", 400)

    if address is not None and (
        not isinstance(address, str) or len(address) > 255
    ):
        return error_response("Address must be at most 255 characters", 400)

    password_hash = generate_password_hash(password)

    connection = None
    cursor = None

    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor()

        # Create the customer profile.
        cursor.execute("""
            INSERT INTO Customer (Name, Phone, Email, Address)
            VALUES (%s, %s, %s, %s)
        """, (name, phone, email, address))

        customer_id = cursor.lastrowid

        # Create the corresponding login account.
        cursor.execute("""
            INSERT INTO UserAccount
                (Email, PasswordHash, Role, CustomerID)
            VALUES (%s, %s, 'Customer', %s)
        """, (email, password_hash, customer_id))

        user_id = cursor.lastrowid

        # Both inserts succeed together or are rolled back together.
        connection.commit()

        return jsonify({
            "message": "Customer registered successfully",
            "user": {
                "UserID": user_id,
                "CustomerID": customer_id,
                "Name": name,
                "Email": email,
                "Role": "Customer"
            }
        }), 201

    except IntegrityError:
        if connection and connection.is_connected():
            connection.rollback()

        return error_response(
            "Email or phone already exists", 409
        )

    except Error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Customer registration failed")
        return error_response("Registration failed", 500)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.post("/api/auth/login")
def login():
    data = read_json()

    if data is None:
        return error_response("Send a valid JSON object", 400)

    email = data.get("Email")
    password = data.get("Password")

    if not isinstance(email, str) or not isinstance(password, str):
        return error_response("Email and password are required", 400)

    email = email.strip().lower()

    if not email or len(email) > 100 or len(password) > 128:
        return error_response("Invalid email or password", 401)

    try:
        user = fetch_one("""
            SELECT
                UserID,
                Email,
                PasswordHash,
                Role,
                CustomerID,
                EmployeeID,
                IsActive
            FROM UserAccount
            WHERE Email = %s
        """, (email,))

        # Return the same message for unknown emails and wrong passwords.
        if (
            user is None
            or not user["IsActive"]
            or not check_password_hash(
                user["PasswordHash"], password
            )
        ):
            return error_response("Invalid email or password", 401)

        claims = {"role": user["Role"]}

        if user["CustomerID"] is not None:
            claims["customer_id"] = user["CustomerID"]

        if user["EmployeeID"] is not None:
            claims["employee_id"] = user["EmployeeID"]

        token = create_access_token(
            identity=str(user["UserID"]),
            additional_claims=claims
        )

        return jsonify({
            "message": "Login successful",
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 7200,
            "user": {
                "UserID": user["UserID"],
                "Email": user["Email"],
                "Role": user["Role"],
                "CustomerID": user["CustomerID"],
                "EmployeeID": user["EmployeeID"]
            }
        }), 200

    except Error:
        app.logger.exception("Login failed due to a database error")
        return error_response("Login service unavailable", 503)

@app.get("/api/auth/me")
@jwt_required()
def current_user():
    claims = get_jwt()

    return jsonify({
        "user_id": get_jwt_identity(),
        "role": claims.get("role"),
        "customer_id": claims.get("customer_id"),
        "employee_id": claims.get("employee_id"),
    })


@app.post("/api/admin/staff")
@role_required("Admin")
def create_staff():
    data = read_json()

    if data is None:
        return error_response("Send a valid JSON object", 400)

    name = data.get("Name")
    email = data.get("Email")
    phone = data.get("Phone")
    role = data.get("Role")
    password = data.get("Password")

    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
        return error_response("A valid name is required", 400)

    if not isinstance(email, str):
        return error_response("Email is required", 400)

    email = email.strip().lower()
    if not valid_email(email) or not email:
        return error_response("Enter a valid email address", 400)

    if phone is not None and (
        not isinstance(phone, str) or len(phone.strip()) > 15
    ):
        return error_response("Invalid phone number", 400)

    if role not in {"Mechanic", "Service Advisor"}:
        return error_response(
            "Role must be Mechanic or Service Advisor", 400
        )

    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        return error_response(
            "Password must be 12–128 characters", 400
        )

    connection = None
    cursor = None

    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO Employee (Name, Role, Phone, Email)
            VALUES (%s, %s, %s, %s)
        """, (name.strip(), role, phone.strip() if phone else None, email))

        employee_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO UserAccount
                (Email, PasswordHash, Role, EmployeeID, IsActive)
            VALUES (%s, %s, %s, %s, TRUE)
        """, (
            email,
            generate_password_hash(password),
            role,
            employee_id,
        ))

        user_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "message": "Staff account created successfully",
            "user": {
                "UserID": user_id,
                "EmployeeID": employee_id,
                "Name": name.strip(),
                "Email": email,
                "Role": role,
            },
        }), 201

    except IntegrityError:
        if connection and connection.is_connected():
            connection.rollback()
        return error_response(
            "Email or phone already exists", 409
        )

    except Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Staff creation failed")
        return error_response("Could not create staff account", 500)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()



# ---------------- TRANSACTIONAL SERVICE COMPLETION ----------------

@app.post("/api/services/<int:service_id>/complete")
@role_required("Admin", "Mechanic")
def complete_service(service_id):
    claims = get_jwt()
    role = claims.get("role")
    employee_id = claims.get("employee_id")

    connection = None
    cursor = None

    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

        # Lock the service so two completion requests cannot process it
        # simultaneously.
        cursor.execute("""
            SELECT ServiceID, AppointmentID, MechanicID, Status
            FROM ServiceRecord
            WHERE ServiceID = %s
            FOR UPDATE
        """, (service_id,))

        service = cursor.fetchone()

        if service is None:
            connection.rollback()
            return error_response("Service record not found", 404)

        # Mechanics may complete only their own assigned jobs.
        if role == "Mechanic":
            if employee_id is None or service["MechanicID"] != int(employee_id):
                connection.rollback()
                return error_response(
                    "You are not assigned to this service", 403
                )

        # Repeated requests must not deduct inventory a second time.
        if service["Status"] == "Completed":
            cursor.execute("""
                SELECT InvoiceID, ServiceID, TotalAmount,
                       InvoiceDate, PaymentStatus, PaymentMethod
                FROM Invoice
                WHERE ServiceID = %s
            """, (service_id,))
            invoice = cursor.fetchone()

            connection.rollback()

            if invoice is None:
                return error_response(
                    "Service is completed but its invoice is missing; "
                    "admin review is required",
                    409
                )

            return jsonify({
                "message": "Service already completed; no changes made",
                "service_id": service_id,
                "status": "Completed",
                "invoice": json_safe(invoice)
            }), 200

        if service["Status"] != "In Progress":
            connection.rollback()
            return error_response(
                "Only services with status In Progress can be completed",
                409
            )

        # Lock the not-yet-deducted usage records.
        cursor.execute("""
            SELECT PartID, QuantityUsed
            FROM PartUsage
            WHERE ServiceID = %s
              AND StockDeducted = FALSE
            ORDER BY PartID
            FOR UPDATE
        """, (service_id,))

        pending_usage = cursor.fetchall()

        # Deduct each part only if sufficient stock is available.
        for usage in pending_usage:
            part_id = usage["PartID"]
            quantity = usage["QuantityUsed"]

            cursor.execute("""
                SELECT PartID, PartName, StockQuantity
                FROM Part
                WHERE PartID = %s
                FOR UPDATE
            """, (part_id,))

            part = cursor.fetchone()

            if part is None:
                connection.rollback()
                return error_response(
                    f"Part {part_id} was not found", 409
                )

            if part["StockQuantity"] < quantity:
                connection.rollback()
                return error_response(
                    f"Insufficient stock for {part['PartName']}",
                    409
                )

            cursor.execute("""
                UPDATE Part
                SET StockQuantity = StockQuantity - %s
                WHERE PartID = %s
                  AND StockQuantity >= %s
            """, (quantity, part_id, quantity))

            if cursor.rowcount != 1:
                connection.rollback()
                return error_response(
                    f"Could not deduct stock for {part['PartName']}",
                    409
                )

            cursor.execute("""
                UPDATE PartUsage
                SET StockDeducted = TRUE
                WHERE ServiceID = %s
                  AND PartID = %s
                  AND StockDeducted = FALSE
            """, (service_id, part_id))

            if cursor.rowcount != 1:
                connection.rollback()
                return error_response(
                    "Part usage changed during completion; retry",
                    409
                )

        # Calculate labour and parts independently to avoid join
        # multiplication when a service has multiple tasks and parts.
        cursor.execute("""
            SELECT COALESCE(SUM(LaborCost), 0) AS LaborTotal
            FROM ServiceTask
            WHERE ServiceID = %s
        """, (service_id,))
        labor_total = cursor.fetchone()["LaborTotal"]

        cursor.execute("""
            SELECT COALESCE(SUM(QuantityUsed * UnitPrice), 0)
                   AS PartsTotal
            FROM PartUsage
            WHERE ServiceID = %s
        """, (service_id,))
        parts_total = cursor.fetchone()["PartsTotal"]

        total_amount = labor_total + parts_total

        # Create the invoice if absent. If it exists, update only the
        # calculated total; preserve payment status, method and date.
        cursor.execute("""
            INSERT INTO Invoice (ServiceID, TotalAmount)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                TotalAmount = %s
        """, (service_id, total_amount, total_amount))

        # Complete the service and its appointment in this transaction.
        cursor.execute("""
            UPDATE ServiceRecord
            SET Status = 'Completed',
                EndDate = COALESCE(EndDate, CURRENT_TIMESTAMP)
            WHERE ServiceID = %s
        """, (service_id,))

        cursor.execute("""
            UPDATE Appointment
            SET Status = 'Completed'
            WHERE AppointmentID = %s
        """, (service["AppointmentID"],))

        cursor.execute("""
            SELECT InvoiceID, ServiceID, InvoiceDate,
                   TotalAmount, PaymentStatus, PaymentMethod
            FROM Invoice
            WHERE ServiceID = %s
        """, (service_id,))
        invoice = json_safe(cursor.fetchone())

        connection.commit()

        return jsonify({
            "message": "Service completed successfully",
            "service_id": service_id,
            "status": "Completed",
            "labor_total": float(labor_total),
            "parts_total": float(parts_total),
            "invoice": invoice
        }), 200

    except Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Service completion failed")
        return error_response(
            "Service completion failed; all changes were rolled back",
            500
        )

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    # Local development only; do not expose the debug server publicly.
    app.run(host="127.0.0.1", port=5000, debug=True)

