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


CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
    supports_credentials=False,
)


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
@role_required("Admin")
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
    if status == "Completed":
        return error_response(
            "Use the transactional service-completion endpoint to complete work", 409
        )
    if status == "In Progress":
        return error_response(
            "Mechanic start is allowed only through the approved-estimate workflow", 409
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



# ---------------- INSPECTION AND CUSTOMER ESTIMATE APPROVAL ----------------

@app.get("/api/mechanic/parts")
@role_required("Mechanic")
def mechanic_parts():
    try:
        return jsonify(fetch_all("""
            SELECT PartID, PartName, StockQuantity, UnitPrice
            FROM Part ORDER BY PartName
        """))
    except Error:
        app.logger.exception("Could not retrieve spare parts")
        return error_response("Could not retrieve spare parts", 500)


@app.post("/api/services/<int:service_id>/estimate")
@role_required("Mechanic")
def create_service_estimate(service_id):
    employee_id = get_jwt().get("employee_id")
    if employee_id is None:
        return error_response("Mechanic account is not linked to an employee profile", 403)
    data = read_json()
    if data is None:
        return error_response("Send a valid JSON object", 400)

    findings = data.get("Findings")
    recommended_tasks = data.get("RecommendedTasks")
    labor_description = data.get("LaborDescription")
    odometer = data.get("Odometer")
    try:
        labor_cost = Decimal(str(data.get("LaborCost")))
    except Exception:
        return error_response("Labour cost must be a valid number", 400)
    raw_parts = data.get("Parts", [])
    if not isinstance(findings, str) or not findings.strip():
        return error_response("Inspection findings are required", 400)
    if not isinstance(recommended_tasks, str) or not recommended_tasks.strip():
        return error_response("Recommended tasks are required", 400)
    if not isinstance(labor_description, str) or not labor_description.strip():
        return error_response("Labour description is required", 400)
    if not labor_cost.is_finite() or labor_cost < 0 or labor_cost > Decimal("99999999.99"):
        return error_response("Labour cost must be between 0 and 99999999.99", 400)
    if odometer not in (None, ""):
        if not str(odometer).isdigit() or int(odometer) < 0:
            return error_response("Odometer must be a non-negative integer", 400)
        odometer = int(odometer)
    else:
        odometer = None
    if not isinstance(raw_parts, list):
        return error_response("Parts must be a list", 400)

    requested_parts, seen = [], set()
    for item in raw_parts:
        if not isinstance(item, dict):
            return error_response("Each part must include PartID and Quantity", 400)
        part_id, quantity = item.get("PartID"), item.get("Quantity")
        if not isinstance(part_id, int) or isinstance(part_id, bool) or part_id <= 0:
            return error_response("PartID must be a positive integer", 400)
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            return error_response("Part quantity must be a positive integer", 400)
        if part_id in seen:
            return error_response("A part can only appear once in an estimate", 400)
        seen.add(part_id)
        requested_parts.append((part_id, quantity))

    connection = None
    cursor = None
    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT ServiceID, MechanicID, Status FROM ServiceRecord
            WHERE ServiceID = %s FOR UPDATE
        """, (service_id,))
        service = cursor.fetchone()
        if service is None:
            connection.rollback()
            return error_response("Service record not found", 404)
        if service["MechanicID"] != int(employee_id):
            connection.rollback()
            return error_response("You are not assigned to this service", 403)
        if service["Status"] != "Pending":
            connection.rollback()
            return error_response("Estimates can only be submitted before work starts", 409)

        cursor.execute("""
            SELECT EstimateID, Status FROM ServiceEstimate
            WHERE ServiceID = %s FOR UPDATE
        """, (service_id,))
        existing = cursor.fetchone()
        if existing and existing["Status"] == "Approved":
            connection.rollback()
            return error_response("An approved estimate cannot be changed", 409)

        parts, parts_cost = [], Decimal("0")
        for part_id, quantity in requested_parts:
            cursor.execute("""
                SELECT PartID, PartName, StockQuantity, UnitPrice
                FROM Part WHERE PartID = %s FOR UPDATE
            """, (part_id,))
            part = cursor.fetchone()
            if part is None:
                connection.rollback()
                return error_response(f"Part {part_id} was not found", 404)
            if part["StockQuantity"] < quantity:
                connection.rollback()
                return error_response(
                    f"Insufficient stock for {part['PartName']}: available {part['StockQuantity']}, requested {quantity}",
                    409
                )
            unit_price = Decimal(str(part["UnitPrice"]))
            parts_cost += unit_price * quantity
            parts.append((part_id, part["PartName"], quantity, unit_price))

        total = labor_cost + parts_cost
        cursor.execute("""
            INSERT INTO ServiceInspection
                (ServiceID, MechanicID, Findings, Odometer, RecommendedTasks)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                MechanicID = VALUES(MechanicID),
                Findings = VALUES(Findings),
                Odometer = VALUES(Odometer),
                RecommendedTasks = VALUES(RecommendedTasks),
                InspectionDate = CURRENT_TIMESTAMP
        """, (service_id, int(employee_id), findings.strip(), odometer, recommended_tasks.strip()))

        if existing:
            estimate_id = existing["EstimateID"]
            cursor.execute("""
                UPDATE ServiceEstimate
                SET Status = 'Proposed', LaborDescription = %s, LaborCost = %s,
                    PartsCost = %s, TotalAmount = %s, DecisionAt = NULL,
                    DecisionByCustomerID = NULL, CustomerNotes = NULL,
                    CreatedAt = CURRENT_TIMESTAMP
                WHERE EstimateID = %s
            """, (labor_description.strip(), labor_cost, parts_cost, total, estimate_id))
            cursor.execute("DELETE FROM ServiceEstimatePart WHERE EstimateID = %s", (estimate_id,))
        else:
            cursor.execute("""
                INSERT INTO ServiceEstimate
                    (ServiceID, Status, LaborDescription, LaborCost, PartsCost, TotalAmount)
                VALUES (%s, 'Proposed', %s, %s, %s, %s)
            """, (service_id, labor_description.strip(), labor_cost, parts_cost, total))
            estimate_id = cursor.lastrowid

        for part_id, part_name, quantity, unit_price in parts:
            cursor.execute("""
                INSERT INTO ServiceEstimatePart
                    (EstimateID, PartID, PartName, Quantity, UnitPrice)
                VALUES (%s, %s, %s, %s, %s)
            """, (estimate_id, part_id, part_name, quantity, unit_price))
        connection.commit()
        return jsonify({
            "message": "Inspection saved and estimate submitted for customer approval",
            "service_id": service_id,
            "estimate_id": estimate_id,
            "status": "Proposed",
            "total_amount": str(total)
        }), 201
    except Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Could not submit service estimate")
        return error_response("Could not submit service estimate", 500)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.get("/api/customer/estimates")
@jwt_required()
def customer_estimates():
    claims = get_jwt()
    if claims.get("role") != "Customer":
        return error_response("Customer access required", 403)
    customer_id = claims.get("customer_id")
    if customer_id is None:
        return error_response("Customer account is not linked to a customer profile", 403)
    try:
        estimates = fetch_all("""
            SELECT se.EstimateID, se.ServiceID, se.Status, se.LaborDescription,
                   se.LaborCost, se.PartsCost, se.TotalAmount, se.CreatedAt,
                   se.DecisionAt, se.CustomerNotes, si.Findings, si.Odometer,
                   si.RecommendedTasks, a.AppointmentDate, a.Complaint,
                   v.RegistrationNo, v.Brand, v.Model
            FROM ServiceEstimate se
            JOIN ServiceRecord sr ON sr.ServiceID = se.ServiceID
            JOIN Appointment a ON a.AppointmentID = sr.AppointmentID
            JOIN Vehicle v ON v.VehicleID = a.VehicleID
            JOIN ServiceInspection si ON si.ServiceID = sr.ServiceID
            WHERE v.CustomerID = %s
            ORDER BY se.CreatedAt DESC
        """, (int(customer_id),))
        for estimate in estimates:
            estimate["Parts"] = fetch_all("""
                SELECT PartID, PartName, Quantity, UnitPrice
                FROM ServiceEstimatePart WHERE EstimateID = %s ORDER BY PartName
            """, (estimate["EstimateID"],))
        return jsonify(estimates)
    except Error:
        app.logger.exception("Could not retrieve customer estimates")
        return error_response("Could not retrieve customer estimates", 500)


@app.post("/api/customer/estimates/<int:estimate_id>/decision")
@jwt_required()
def decide_service_estimate(estimate_id):
    claims = get_jwt()
    if claims.get("role") != "Customer":
        return error_response("Customer access required", 403)
    customer_id = claims.get("customer_id")
    if customer_id is None:
        return error_response("Customer account is not linked to a customer profile", 403)
    data = read_json()
    if data is None:
        return error_response("Send a valid JSON object", 400)
    decision, notes = data.get("Decision"), data.get("Notes")
    if decision not in ("Approved", "Rejected"):
        return error_response("Decision must be Approved or Rejected", 400)
    if notes is not None and (not isinstance(notes, str) or len(notes) > 500):
        return error_response("Notes must be at most 500 characters", 400)

    connection = None
    cursor = None
    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT se.EstimateID, se.Status AS EstimateStatus,
                   sr.Status AS ServiceStatus, v.CustomerID
            FROM ServiceEstimate se
            JOIN ServiceRecord sr ON sr.ServiceID = se.ServiceID
            JOIN Appointment a ON a.AppointmentID = sr.AppointmentID
            JOIN Vehicle v ON v.VehicleID = a.VehicleID
            WHERE se.EstimateID = %s FOR UPDATE
        """, (estimate_id,))
        estimate = cursor.fetchone()
        if estimate is None or estimate["CustomerID"] != int(customer_id):
            connection.rollback()
            return error_response("Estimate not found for this customer", 404)
        if estimate["ServiceStatus"] != "Pending":
            connection.rollback()
            return error_response("This service has already started; estimate decision is locked", 409)
        if estimate["EstimateStatus"] != "Proposed":
            connection.rollback()
            return error_response("Only proposed estimates can be approved or rejected", 409)

        if decision == "Approved":
            cursor.execute("""
                SELECT PartID, Quantity FROM ServiceEstimatePart
                WHERE EstimateID = %s ORDER BY PartID FOR UPDATE
            """, (estimate_id,))
            items = cursor.fetchall()
            for item in items:
                cursor.execute("""
                    SELECT PartName, StockQuantity FROM Part
                    WHERE PartID = %s FOR UPDATE
                """, (item["PartID"],))
                part = cursor.fetchone()
                if part is None or part["StockQuantity"] < item["Quantity"]:
                    connection.rollback()
                    return error_response(
                        "Stock changed after the estimate was prepared; ask the mechanic to revise it",
                        409
                    )
        cursor.execute("""
            UPDATE ServiceEstimate
            SET Status = %s, DecisionAt = CURRENT_TIMESTAMP,
                DecisionByCustomerID = %s, CustomerNotes = %s
            WHERE EstimateID = %s AND Status = 'Proposed'
        """, (decision, int(customer_id), (notes or "").strip() or None, estimate_id))
        if cursor.rowcount != 1:
            connection.rollback()
            return error_response("Estimate decision was changed; refresh and retry", 409)
        connection.commit()
        return jsonify({"message": f"Estimate {decision.lower()} successfully", "estimate_id": estimate_id, "status": decision})
    except Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Could not record estimate decision")
        return error_response("Could not record estimate decision", 500)
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


# ---------------- ADMIN DASHBOARD ----------------


@app.get("/api/admin/dashboard")
@role_required("Admin")
def admin_dashboard():
    try:
        stats = fetch_one("""
            SELECT
                (SELECT COUNT(*)
                 FROM Appointment) AS TotalAppointments,

                (SELECT COUNT(*)
                 FROM Appointment
                 WHERE Status IN ('Booked', 'Pending'))
                    AS PendingRequests,

                (SELECT COUNT(*)
                 FROM Customer) AS TotalCustomers,

                (SELECT COUNT(*)
                 FROM Vehicle) AS TotalVehicles,

                (SELECT COUNT(*)
                 FROM ServiceRecord
                 WHERE Status = 'Completed')
                    AS CompletedServices,

                (SELECT COUNT(*)
                 FROM ServiceRecord
                 WHERE Status = 'In Progress')
                    AS ServicesInProgress
        """)

        return jsonify({
            "totalAppointments": stats["TotalAppointments"],
            "pendingRequests": stats["PendingRequests"],
            "totalCustomers": stats["TotalCustomers"],
            "totalVehicles": stats["TotalVehicles"],
            "completedServices": stats["CompletedServices"],
            "servicesInProgress": stats["ServicesInProgress"],
        })

    except Error:
        app.logger.exception("Could not load admin dashboard")
        return error_response("Could not load admin dashboard", 500)


# ---------------- ADMIN APPOINTMENTS ----------------

@app.get("/api/admin/appointments")
@role_required("Admin")
def admin_appointments():
    try:
        appointments = fetch_all("""
            SELECT
                a.AppointmentID,
                a.AppointmentDate,
                a.Complaint,
                a.Status AS AppointmentStatus,
                a.VehicleID,
                c.CustomerID,
                c.Name AS CustomerName,
                c.Phone AS CustomerPhone,
                c.Email AS CustomerEmail,
                v.RegistrationNo,
                v.Brand,
                v.Model,
                sr.ServiceID,
                sr.MechanicID,
                sr.Status AS ServiceStatus,
                e.Name AS MechanicName
            FROM Appointment a
            JOIN Vehicle v
                ON v.VehicleID = a.VehicleID
            JOIN Customer c
                ON c.CustomerID = v.CustomerID
            LEFT JOIN ServiceRecord sr
                ON sr.AppointmentID = a.AppointmentID
            LEFT JOIN Employee e
                ON e.EmployeeID = sr.MechanicID
            ORDER BY a.AppointmentDate DESC
        """)

        return jsonify(appointments)

    except Error:
        app.logger.exception("Could not load admin appointments")
        return error_response("Could not load admin appointments", 500)


@app.get("/api/admin/mechanics")
@role_required("Admin")
def admin_mechanics():
    try:
        mechanics = fetch_all("""
            SELECT
                e.EmployeeID,
                e.Name,
                e.Email,
                e.Phone
            FROM Employee e
            JOIN UserAccount ua
                ON ua.EmployeeID = e.EmployeeID
            WHERE e.Role = 'Mechanic'
              AND ua.Role = 'Mechanic'
              AND ua.IsActive = TRUE
            ORDER BY e.Name
        """)

        return jsonify(mechanics), 200

    except Error:
        app.logger.exception("Could not load mechanics")
        return error_response("Could not retrieve mechanics", 500)



@app.patch("/api/admin/appointments/<int:appointment_id>")
@role_required("Admin")
def update_appointment(appointment_id):
    data = read_json()

    if data is None:
        return error_response("Send a valid JSON object", 400)

    status = data.get("Status", data.get("status"))

    allowed_statuses = {
        "Booked",
        "Pending",
        "Confirmed",
        "In Progress",
        "Completed",
        "Cancelled",
    }

    if status not in allowed_statuses:
        return error_response(
            "Invalid appointment status",
            400,
        )

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT AppointmentID, Status
                FROM Appointment
                WHERE AppointmentID = %s
                FOR UPDATE
            """, (appointment_id,))

            appointment = cursor.fetchone()

            if appointment is None:
                connection.rollback()
                return error_response("Appointment not found", 404)

            cursor.execute("""
                UPDATE Appointment
                SET Status = %s
                WHERE AppointmentID = %s
            """, (status, appointment_id))

            connection.commit()

            cursor.execute("""
                SELECT
                    AppointmentID,
                    VehicleID,
                    AppointmentDate,
                    Complaint,
                    Status AS AppointmentStatus
                FROM Appointment
                WHERE AppointmentID = %s
            """, (appointment_id,))

            updated = json_safe(cursor.fetchone())
            return jsonify(updated)

        finally:
            cursor.close()
            connection.close()

    except Error:
        app.logger.exception("Could not update appointment")
        return error_response("Could not update appointment", 500)


@app.patch("/api/admin/appointments/<int:appointment_id>/assign")
@role_required("Admin")
def assign_appointment_mechanic(appointment_id):
    data = read_json()

    if data is None:
        return error_response("A JSON request body is required", 400)

    mechanic_id = data.get("MechanicID")

    if (
        isinstance(mechanic_id, bool)
        or not isinstance(mechanic_id, int)
    ):
        return error_response("A valid MechanicID is required", 400)

    connection = None
    cursor = None

    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT AppointmentID, Status
            FROM Appointment
            WHERE AppointmentID = %s
            FOR UPDATE
        """, (appointment_id,))

        appointment = cursor.fetchone()

        if not appointment:
            connection.rollback()
            return error_response("Appointment not found", 404)

        if appointment["Status"] in ("Cancelled", "Completed"):
            connection.rollback()
            return error_response(
                "Cancelled or completed appointments cannot be assigned",
                409
            )

        cursor.execute("""
            SELECT e.EmployeeID
            FROM Employee e
            JOIN UserAccount ua
                ON ua.EmployeeID = e.EmployeeID
            WHERE e.EmployeeID = %s
              AND e.Role = 'Mechanic'
              AND ua.Role = 'Mechanic'
              AND ua.IsActive = TRUE
            FOR UPDATE
        """, (mechanic_id,))

        mechanic = cursor.fetchone()

        if not mechanic:
            connection.rollback()
            return error_response(
                "The selected mechanic is not an active mechanic account",
                400
            )

        cursor.execute("""
            SELECT ServiceID, Status
            FROM ServiceRecord
            WHERE AppointmentID = %s
            FOR UPDATE
        """, (appointment_id,))

        service = cursor.fetchone()

        if service is None:
            cursor.execute("""
                INSERT INTO ServiceRecord
                    (AppointmentID, MechanicID, Status)
                VALUES (%s, %s, 'Pending')
            """, (appointment_id, mechanic_id))

            service_id = cursor.lastrowid

        else:
            if service["Status"] != "Pending":
                connection.rollback()
                return error_response(
                    "Only pending services can be assigned or reassigned",
                    409
                )

            cursor.execute("""
                UPDATE ServiceRecord
                SET MechanicID = %s
                WHERE ServiceID = %s
            """, (mechanic_id, service["ServiceID"]))

            service_id = service["ServiceID"]

        connection.commit()

        return jsonify({
            "message": "Mechanic assigned successfully",
            "AppointmentID": appointment_id,
            "ServiceID": service_id,
            "MechanicID": mechanic_id,
            "ServiceStatus": "Pending"
        }), 200

    except Error:
        if connection:
            connection.rollback()

        app.logger.exception("Could not assign mechanic")
        return error_response("Could not assign mechanic", 500)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ---------------- CUSTOMER DASHBOARD ----------------

@app.get("/api/customer/dashboard")
@jwt_required()
def customer_dashboard():
    claims = get_jwt()

    if claims.get("role") != "Customer":
        return error_response("Customer access required", 403)

    customer_id = claims.get("customer_id")

    if customer_id is None:
        return error_response("Customer account is not linked to a customer profile", 403)

    try:
        stats = fetch_one("""
            SELECT
                (
                    SELECT COUNT(*)
                    FROM Appointment a
                    JOIN Vehicle v ON v.VehicleID = a.VehicleID
                    WHERE v.CustomerID = %s
                      AND a.AppointmentDate >= CURRENT_DATE()
                      AND a.Status NOT IN ('Completed', 'Cancelled')
                ) AS UpcomingAppointments,
                (
                    SELECT COUNT(*)
                    FROM Vehicle v
                    WHERE v.CustomerID = %s
                ) AS RegisteredVehicles,
                (
                    SELECT COUNT(*)
                    FROM ServiceRecord sr
                    JOIN Appointment a ON a.AppointmentID = sr.AppointmentID
                    JOIN Vehicle v ON v.VehicleID = a.VehicleID
                    WHERE v.CustomerID = %s
                      AND sr.Status = 'Completed'
                ) AS CompletedServices
        """, (customer_id, customer_id, customer_id))

        return jsonify({
            "upcomingAppointments": stats["UpcomingAppointments"],
            "registeredVehicles": stats["RegisteredVehicles"],
            "completedServices": stats["CompletedServices"]
        })

    except Error:
        app.logger.exception("Could not load customer dashboard")
        return error_response("Could not load customer dashboard", 500)


# ---------------- CUSTOMER NEXT APPOINTMENT ----------------

@app.get("/api/customer/next-appointment")
@jwt_required()
def customer_next_appointment():
    claims = get_jwt()

    if claims.get("role") != "Customer":
        return error_response("Customer access required", 403)

    customer_id = claims.get("customer_id")

    if customer_id is None:
        return error_response(
            "Customer account is not linked to a customer profile",
            403
        )

    try:
        appointment = fetch_one("""
            SELECT
                a.AppointmentID,
                a.AppointmentDate,
                a.Complaint,
                a.Status AS AppointmentStatus,
                v.RegistrationNo,
                v.Brand,
                v.Model
            FROM Appointment a
            JOIN Vehicle v
                ON v.VehicleID = a.VehicleID
            WHERE v.CustomerID = %s
              AND a.AppointmentDate >= CURRENT_DATE()
              AND a.Status NOT IN ('Completed', 'Cancelled')
            ORDER BY a.AppointmentDate ASC
            LIMIT 1
        """, (customer_id,))

        return jsonify(appointment) if appointment else jsonify(None)

    except Error:
        app.logger.exception("Could not load next appointment")
        return error_response("Could not load next appointment", 500)



# ---------------- CUSTOMER INVOICES ----------------

@app.get("/api/customer/invoices")
@jwt_required()
def customer_invoices():
    claims = get_jwt()

    if claims.get("role") != "Customer":
        return error_response("Customer access required", 403)

    customer_id = claims.get("customer_id")

    if customer_id is None:
        return error_response(
            "Customer account is not linked to a customer profile",
            403
        )

    try:
        invoices = fetch_all("""
            SELECT
                i.InvoiceID,
                i.ServiceID,
                i.InvoiceDate,
                i.TotalAmount,
                c.Name AS CustomerName,
                v.RegistrationNo,
                v.Brand,
                v.Model,
                COALESCE(p.AmountPaid, 0) AS AmountPaid,
                GREATEST(
                    i.TotalAmount - COALESCE(p.AmountPaid, 0),
                    0
                ) AS OutstandingBalance,
                CASE
                    WHEN COALESCE(p.AmountPaid, 0) >= i.TotalAmount
                        THEN 'Paid'
                    WHEN COALESCE(p.AmountPaid, 0) > 0
                        THEN 'Partially Paid'
                    ELSE 'Unpaid'
                END AS PaymentStatus
            FROM Invoice i
            JOIN ServiceRecord sr
                ON sr.ServiceID = i.ServiceID
            JOIN Appointment a
                ON a.AppointmentID = sr.AppointmentID
            JOIN Vehicle v
                ON v.VehicleID = a.VehicleID
            JOIN Customer c
                ON c.CustomerID = v.CustomerID
            LEFT JOIN (
                SELECT InvoiceID, SUM(Amount) AS AmountPaid
                FROM Payment
                GROUP BY InvoiceID
            ) p ON p.InvoiceID = i.InvoiceID
            WHERE v.CustomerID = %s
            ORDER BY i.InvoiceDate DESC, i.InvoiceID DESC
        """, (customer_id,))

        return jsonify(invoices)

    except Error:
        app.logger.exception("Could not retrieve customer invoices")
        return error_response("Could not retrieve customer invoices", 500)



@app.get("/api/customer/invoices/<int:invoice_id>")
@jwt_required()
def customer_invoice_details(invoice_id):
    claims = get_jwt()

    if claims.get("role") != "Customer":
        return error_response("Customer access required", 403)

    customer_id = claims.get("customer_id")

    if customer_id is None:
        return error_response(
            "Customer account is not linked to a customer profile",
            403
        )

    try:
        invoice = fetch_one("""
            SELECT
                i.InvoiceID,
                i.ServiceID,
                i.InvoiceDate,
                i.TotalAmount,
                sr.AppointmentID,
                sr.StartDate AS ServiceStartDate,
                sr.EndDate AS ServiceEndDate,
                sr.Odometer,
                sr.Status AS ServiceStatus,
                c.CustomerID,
                c.Name AS CustomerName,
                c.Email AS CustomerEmail,
                c.Phone AS CustomerPhone,
                c.Address AS CustomerAddress,
                v.VehicleID,
                v.RegistrationNo,
                v.Brand,
                v.Model,
                v.ManufactureYear,
                COALESCE(p.AmountPaid, 0) AS AmountPaid,
                GREATEST(
                    i.TotalAmount - COALESCE(p.AmountPaid, 0),
                    0
                ) AS OutstandingBalance
            FROM Invoice i
            JOIN ServiceRecord sr
                ON sr.ServiceID = i.ServiceID
            JOIN Appointment a
                ON a.AppointmentID = sr.AppointmentID
            JOIN Vehicle v
                ON v.VehicleID = a.VehicleID
            JOIN Customer c
                ON c.CustomerID = v.CustomerID
            LEFT JOIN (
                SELECT InvoiceID, SUM(Amount) AS AmountPaid
                FROM Payment
                GROUP BY InvoiceID
            ) p ON p.InvoiceID = i.InvoiceID
            WHERE i.InvoiceID = %s
              AND v.CustomerID = %s
        """, (invoice_id, customer_id))

        # The ownership condition is enforced in SQL, not just the UI.
        if not invoice:
            return error_response("Invoice not found", 404)

        payments = fetch_all("""
            SELECT
                p.PaymentID,
                p.Amount,
                p.PaymentMethod,
                p.PaymentDate
            FROM Payment p
            WHERE p.InvoiceID = %s
            ORDER BY p.PaymentDate ASC, p.PaymentID ASC
        """, (invoice_id,))

        amount_paid = round(
            sum(float(payment["Amount"]) for payment in payments), 2
        )
        total_amount = float(invoice["TotalAmount"])
        outstanding = round(max(total_amount - amount_paid, 0), 2)

        invoice["AmountPaid"] = amount_paid
        invoice["OutstandingBalance"] = outstanding
        invoice["PaymentStatus"] = (
            "Paid" if outstanding <= 0
            else "Partially Paid" if amount_paid > 0
            else "Unpaid"
        )
        invoice["Payments"] = payments

        return jsonify(invoice)

    except Error:
        app.logger.exception(
            "Could not retrieve customer invoice details"
        )
        return error_response(
            "Could not retrieve invoice details", 500
        )


# ---------------- CUSTOMER SERVICE HISTORY ----------------

@app.get("/api/customer/services")
@jwt_required()
def customer_services():
    claims = get_jwt()

    if claims.get("role") != "Customer":
        return error_response("Customer access required", 403)

    customer_id = claims.get("customer_id")

    if customer_id is None:
        return error_response(
            "Customer account is not linked to a customer profile",
            403
        )

    try:
        services = fetch_all("""
            SELECT
                a.AppointmentID,
                a.VehicleID,
                sr.ServiceID,
                v.RegistrationNo,
                v.Brand,
                v.Model,
                a.AppointmentDate,
                a.Complaint,
                a.Status AS AppointmentStatus,
                e.Name AS MechanicName,
                sr.StartDate,
                sr.EndDate,
                sr.Odometer,
                sr.Status AS ServiceStatus
            FROM Appointment a
            JOIN Vehicle v
                ON v.VehicleID = a.VehicleID
            LEFT JOIN ServiceRecord sr
                ON sr.AppointmentID = a.AppointmentID
            LEFT JOIN Employee e
                ON e.EmployeeID = sr.MechanicID
            WHERE v.CustomerID = %s
            ORDER BY a.AppointmentDate DESC
        """, (customer_id,))

        return jsonify(services)

    except Error:
        app.logger.exception("Could not retrieve customer services")
        return error_response("Could not retrieve customer services", 500)


# ---------------- CUSTOMER VEHICLES ----------------

@app.get("/api/customer/vehicles")
@jwt_required()
def customer_vehicles():
    claims = get_jwt()

    if claims.get("role") != "Customer":
        return error_response("Customer access required", 403)

    customer_id = claims.get("customer_id")

    if customer_id is None:
        return error_response(
            "Customer account is not linked to a customer profile",
            403
        )

    try:
        vehicles = fetch_all("""
            SELECT
                VehicleID,
                CustomerID,
                RegistrationNo,
                Brand,
                Model,
                ManufactureYear,
                FuelType
            FROM Vehicle
            WHERE CustomerID = %s
            ORDER BY VehicleID
        """, (customer_id,))

        return jsonify(vehicles)

    except Error:
        app.logger.exception("Could not retrieve customer vehicles")
        return error_response("Could not retrieve customer vehicles", 500)


# ---------------- CUSTOMER VEHICLE REGISTRATION ----------------

@app.post("/api/customer/vehicles")
@jwt_required()
def create_customer_vehicle():
    claims = get_jwt()

    if claims.get("role") != "Customer":
        return error_response("Customer access required", 403)

    customer_id = claims.get("customer_id")
    if customer_id is None:
        return error_response(
            "Customer account is not linked to a customer profile",
            403
        )

    data = read_json()
    if data is None:
        return error_response("Send a valid JSON object", 400)

    registration_no = data.get("RegistrationNo")
    brand = data.get("Brand")
    model = data.get("Model")
    manufacture_year = data.get("ManufactureYear")
    fuel_type = data.get("FuelType")

    # Validate required text fields.
    if not isinstance(registration_no, str) or not registration_no.strip():
        return error_response("Registration number is required", 400)

    registration_no = registration_no.strip().upper()
    if len(registration_no) > 20:
        return error_response(
            "Registration number must be at most 20 characters", 400
        )

    if not isinstance(brand, str) or not brand.strip():
        return error_response("Vehicle brand is required", 400)

    brand = brand.strip()
    if len(brand) > 50:
        return error_response("Brand must be at most 50 characters", 400)

    if not isinstance(model, str) or not model.strip():
        return error_response("Vehicle model is required", 400)

    model = model.strip()
    if len(model) > 50:
        return error_response("Model must be at most 50 characters", 400)

    # Manufacture year is optional.
    if manufacture_year in ("", None):
        manufacture_year = None
    else:
        try:
            if isinstance(manufacture_year, bool):
                raise ValueError
            manufacture_year = int(manufacture_year)
        except (TypeError, ValueError):
            return error_response("Enter a valid manufacture year", 400)

        if not 1886 <= manufacture_year <= date.today().year + 1:
            return error_response("Manufacture year is out of range", 400)

    # Fuel type is optional.
    if fuel_type in ("", None):
        fuel_type = None
    elif not isinstance(fuel_type, str) or len(fuel_type.strip()) > 20:
        return error_response("Fuel type must be at most 20 characters", 400)
    else:
        fuel_type = fuel_type.strip()

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            INSERT INTO Vehicle
                (CustomerID, RegistrationNo, Brand, Model,
                 ManufactureYear, FuelType)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            int(customer_id),
            registration_no,
            brand,
            model,
            manufacture_year,
            fuel_type
        ))

        vehicle_id = cursor.lastrowid
        connection.commit()

        cursor.execute("""
            SELECT VehicleID, CustomerID, RegistrationNo, Brand,
                   Model, ManufactureYear, FuelType
            FROM Vehicle
            WHERE VehicleID = %s AND CustomerID = %s
        """, (vehicle_id, int(customer_id)))

        vehicle = json_safe(cursor.fetchone())
        return jsonify(vehicle), 201

    except IntegrityError:
        if connection and connection.is_connected():
            connection.rollback()
        return error_response(
            "This registration number is already registered", 409
        )

    except Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Could not register customer vehicle")
        return error_response("Could not register vehicle", 500)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# ---------------- CUSTOMER APPOINTMENTS ----------------

@app.post("/api/appointments")
@jwt_required()
def create_appointment():
    claims = get_jwt()

    if claims.get("role") != "Customer":
        return error_response("Customer access required", 403)

    customer_id = claims.get("customer_id")
    if customer_id is None:
        return error_response("Customer account is not linked to a customer profile", 403)

    data = read_json()
    if data is None:
        return error_response("Send a valid JSON object", 400)

    vehicle_id = data.get("vehicle_id", data.get("VehicleID"))
    appointment_date = data.get("appointment_date", data.get("AppointmentDate"))
    complaint = data.get("complaint", data.get("Complaint"))

    if not isinstance(vehicle_id, int) or isinstance(vehicle_id, bool):
        return error_response("A valid vehicle_id is required", 400)

    if not isinstance(appointment_date, str) or not appointment_date.strip():
        return error_response("appointment_date is required", 400)

    try:
        parsed_date = datetime.fromisoformat(appointment_date.strip())
    except ValueError:
        return error_response(
            "appointment_date must be an ISO date/time, such as 2026-10-28T10:30:00",
            400
        )

    if complaint is not None and (
        not isinstance(complaint, str) or len(complaint) > 500
    ):
        return error_response("Complaint must be at most 500 characters", 400)

    try:
        vehicle = fetch_one("""
            SELECT VehicleID
            FROM Vehicle
            WHERE VehicleID = %s AND CustomerID = %s
        """, (vehicle_id, customer_id))

        if vehicle is None:
            return error_response("Vehicle not found for this customer", 404)

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                INSERT INTO Appointment
                    (VehicleID, AppointmentDate, Complaint, Status)
                VALUES (%s, %s, %s, 'Booked')
            """, (vehicle_id, parsed_date, complaint.strip() if complaint else None))

            appointment_id = cursor.lastrowid
            connection.commit()

            cursor.execute("""
                SELECT AppointmentID, VehicleID, AppointmentDate,
                       Complaint, Status, CreatedAt
                FROM Appointment
                WHERE AppointmentID = %s
            """, (appointment_id,))

            appointment = json_safe(cursor.fetchone())
            return jsonify(appointment), 201

        finally:
            cursor.close()
            connection.close()

    except Error:
        app.logger.exception("Could not create appointment")
        return error_response("Could not create appointment", 500)


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
        return error_response("Password must be at least 8 characters", 400)

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
        cursor = connection.cursor(dictionary=True)

        # Prevent duplicate login accounts.
        cursor.execute("""
            SELECT UserID
            FROM UserAccount
            WHERE Email = %s
            FOR UPDATE
        """, (email,))

        if cursor.fetchone():
            connection.rollback()
            return error_response(
                "A login account already exists for this email. Please sign in.",
                409
            )

        # Reuse an existing customer profile when the email matches.
        cursor.execute("""
            SELECT CustomerID, Name, Phone, Email, Address
            FROM Customer
            WHERE Email = %s
            FOR UPDATE
        """, (email,))

        customer = cursor.fetchone()

        if customer:
            # Do not allow someone to claim an existing profile using
            # only a matching email; require the stored phone to match too.
            if customer["Phone"] != phone:
                connection.rollback()
                return error_response(
                    "This email belongs to an existing customer, but the "
                    "phone number does not match. Contact an administrator.",
                    409
                )

            customer_id = customer["CustomerID"]

        else:
            # A different customer may already own this phone number.
            cursor.execute("""
                SELECT CustomerID
                FROM Customer
                WHERE Phone = %s
                FOR UPDATE
            """, (phone,))

            if cursor.fetchone():
                connection.rollback()
                return error_response(
                    "This phone number is already registered with another "
                    "customer profile.",
                    409
                )

            cursor.execute("""
                INSERT INTO Customer (Name, Phone, Email, Address)
                VALUES (%s, %s, %s, %s)
            """, (name, phone, email, address))

            customer_id = cursor.lastrowid

        # Create the login account linked to the existing/new profile.
        cursor.execute("""
            INSERT INTO UserAccount
                (Email, PasswordHash, Role, CustomerID, IsActive)
            VALUES (%s, %s, 'Customer', %s, TRUE)
        """, (email, password_hash, customer_id))

        user_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "message": "Customer account created successfully",
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
            "Email or phone already exists. Check the existing customer "
            "and login records.",
            409
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

        allowed_roles = {"Admin", "Mechanic", "Customer"}
        if user["Role"] not in allowed_roles:
            app.logger.warning(
                "Login rejected for unsupported role on UserID %s",
                user["UserID"]
            )
            return error_response("Invalid email or password", 401)

        if user["Role"] == "Admin":
            # Only the existing admin employee account may hold Admin access.
            if user["EmployeeID"] != 1 or user["CustomerID"] is not None:
                return error_response("Invalid email or password", 401)

        if user["Role"] == "Mechanic":
            if user["EmployeeID"] is None or user["CustomerID"] is not None:
                return error_response("Invalid email or password", 401)

        if user["Role"] == "Customer":
            if user["CustomerID"] is None or user["EmployeeID"] is not None:
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

    if role != "Mechanic":
        return error_response(
            "New staff accounts can only be created with the Mechanic role",
            400
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



# ---------------- MECHANIC WORK LIST ----------------

@app.get("/api/mechanic/services")
@role_required("Mechanic")
def mechanic_services():
    claims = get_jwt()
    employee_id = claims.get("employee_id")

    if employee_id is None:
        return error_response(
            "Mechanic account is not linked to an employee profile",
            403
        )

    try:
        services = fetch_all("""
            SELECT
                sr.ServiceID,
                sr.AppointmentID,
                sr.MechanicID,
                sr.StartDate,
                sr.EndDate,
                sr.Odometer,
                sr.ActualPartsConfirmed,
                sr.Status AS ServiceStatus,
                a.AppointmentDate,
                a.Complaint,
                a.Status AS AppointmentStatus,
                v.RegistrationNo,
                v.Brand,
                v.Model,
                c.Name AS CustomerName,
                se.EstimateID,
                se.Status AS EstimateStatus,
                se.TotalAmount AS EstimateTotal,
                si.Findings AS InspectionFindings,
                si.Odometer AS InspectionOdometer,
                si.RecommendedTasks
            FROM ServiceRecord sr
            JOIN Appointment a
                ON a.AppointmentID = sr.AppointmentID
            LEFT JOIN ServiceEstimate se ON se.ServiceID = sr.ServiceID
            LEFT JOIN ServiceInspection si ON si.ServiceID = sr.ServiceID
            JOIN Vehicle v
                ON v.VehicleID = a.VehicleID
            JOIN Customer c
                ON c.CustomerID = v.CustomerID
            WHERE sr.MechanicID = %s
            ORDER BY
                CASE WHEN sr.Status = 'In Progress'
                     THEN 0 ELSE 1 END,
                a.AppointmentDate DESC
        """, (int(employee_id),))

        for service in services:
            if service.get("EstimateID") and service.get("EstimateStatus") == "Approved":
                service["EstimateParts"] = fetch_all("""
                    SELECT PartID, PartName, Quantity, UnitPrice
                    FROM ServiceEstimatePart
                    WHERE EstimateID = %s
                    ORDER BY PartName
                """, (service["EstimateID"],))
            else:
                service["EstimateParts"] = []
            if service.get("ServiceStatus") == "In Progress":
                service["ActualParts"] = fetch_all("""
                    SELECT PartID, QuantityUsed, UnitPrice
                    FROM PartUsage
                    WHERE ServiceID = %s
                    ORDER BY PartID
                """, (service["ServiceID"],))
            else:
                service["ActualParts"] = []
        return jsonify(services)

    except Error:
        app.logger.exception(
            "Could not load mechanic services"
        )
        return error_response(
            "Could not retrieve assigned services", 500
        )


# ---------------- MECHANIC START SERVICE ----------------

@app.post("/api/services/<int:service_id>/start")
@role_required("Mechanic")
def start_service(service_id):
    claims = get_jwt()
    employee_id = claims.get("employee_id")

    if employee_id is None:
        return error_response(
            "Mechanic account is not linked to an employee profile",
            403
        )

    connection = None
    cursor = None

    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

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

        if service["MechanicID"] != int(employee_id):
            connection.rollback()
            return error_response(
                "You are not assigned to this service",
                403
            )

        cursor.execute("""
            SELECT EstimateID, Status FROM ServiceEstimate
            WHERE ServiceID = %s FOR UPDATE
        """, (service_id,))
        estimate = cursor.fetchone()
        if estimate is None or estimate["Status"] != "Approved":
            connection.rollback()
            return error_response(
                "Customer approval is required before work can start", 409
            )

        if service["Status"] != "Pending":
            connection.rollback()
            return error_response(
                "Only Pending services can be started", 409
            )

        cursor.execute("""
            SELECT PartID, Quantity, UnitPrice
            FROM ServiceEstimatePart
            WHERE EstimateID = %s
            ORDER BY PartID
            FOR UPDATE
        """, (estimate["EstimateID"],))
        approved_parts = cursor.fetchall()
        for item in approved_parts:
            cursor.execute("""
                SELECT PartName, StockQuantity FROM Part
                WHERE PartID = %s FOR UPDATE
            """, (item["PartID"],))
            part = cursor.fetchone()
            if part is None or part["StockQuantity"] < item["Quantity"]:
                connection.rollback()
                return error_response(
                    "Insufficient stock for approved part: " +
                    (part["PartName"] if part else str(item["PartID"])), 409
                )
            cursor.execute("""
                INSERT INTO PartUsage
                    (ServiceID, PartID, QuantityUsed, UnitPrice, StockDeducted)
                VALUES (%s, %s, %s, %s, FALSE)
                ON DUPLICATE KEY UPDATE
                    QuantityUsed = VALUES(QuantityUsed),
                    UnitPrice = VALUES(UnitPrice),
                    StockDeducted = FALSE
            """, (service_id, item["PartID"], item["Quantity"], item["UnitPrice"]))

        cursor.execute("""
            UPDATE ServiceRecord
            SET Status = 'In Progress',
                StartDate = COALESCE(StartDate, CURRENT_TIMESTAMP)
            WHERE ServiceID = %s
              AND Status = 'Pending'
        """, (service_id,))

        if cursor.rowcount != 1:
            connection.rollback()
            return error_response(
                "Service status changed; refresh and retry",
                409
            )

        # Appointment's current CHECK constraint excludes In Progress.
        # ServiceRecord is the source of truth until final completion.
        connection.commit()

        return jsonify({
            "message": "Service started successfully",
            "service_id": service_id,
            "status": "In Progress"
        }), 200

    except Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Could not start service")
        return error_response("Could not start service", 500)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()



@app.post("/api/services/<int:service_id>/actual-parts")
@role_required("Mechanic")
def record_actual_parts(service_id):
    claims = get_jwt()
    employee_id = claims.get("employee_id")
    if employee_id is None:
        return error_response("Mechanic account is not linked to an employee profile", 403)
    data = read_json()
    if data is None or not isinstance(data.get("Parts"), list):
        return error_response("Parts must be provided as a list", 400)

    actual = []
    seen = set()
    for item in data["Parts"]:
        if not isinstance(item, dict):
            return error_response("Each part must include PartID and Quantity", 400)
        part_id, quantity = item.get("PartID"), item.get("Quantity")
        if not isinstance(part_id, int) or isinstance(part_id, bool) or part_id <= 0:
            return error_response("PartID must be a positive integer", 400)
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
            return error_response("Actual quantity must be a non-negative integer", 400)
        if part_id in seen:
            return error_response("Each part may only appear once", 400)
        seen.add(part_id)
        actual.append((part_id, quantity))

    connection = None
    cursor = None
    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT ServiceID, MechanicID, Status
            FROM ServiceRecord WHERE ServiceID = %s FOR UPDATE
        """, (service_id,))
        service = cursor.fetchone()
        if service is None:
            connection.rollback()
            return error_response("Service record not found", 404)
        if service["MechanicID"] != int(employee_id):
            connection.rollback()
            return error_response("You are not assigned to this service", 403)
        if service["Status"] != "In Progress":
            connection.rollback()
            return error_response("Actual parts can only be recorded while work is in progress", 409)

        cursor.execute("""
            SELECT se.EstimateID
            FROM ServiceEstimate se
            WHERE se.ServiceID = %s AND se.Status = 'Approved'
            FOR UPDATE
        """, (service_id,))
        approved = cursor.fetchone()
        if approved is None:
            connection.rollback()
            return error_response("An approved estimate is required", 409)

        cursor.execute("""
            SELECT PartID, Quantity
            FROM ServiceEstimatePart
            WHERE EstimateID = %s
            ORDER BY PartID FOR UPDATE
        """, (approved["EstimateID"],))
        approved_parts = {row["PartID"]: row["Quantity"] for row in cursor.fetchall()}
        for part_id, quantity in actual:
            if part_id not in approved_parts:
                connection.rollback()
                return error_response("Actual parts must be included in the approved estimate", 409)
            if quantity > approved_parts[part_id]:
                connection.rollback()
                return error_response(
                    "Actual quantity exceeds the approved estimate; a revised customer approval is required",
                    409
                )
            if quantity == 0:
                cursor.execute("""
                    DELETE FROM PartUsage
                    WHERE ServiceID = %s AND PartID = %s AND StockDeducted = FALSE
                """, (service_id, part_id))
            else:
                cursor.execute("""
                    UPDATE PartUsage
                    SET QuantityUsed = %s, StockDeducted = FALSE
                    WHERE ServiceID = %s AND PartID = %s
                """, (quantity, service_id, part_id))
                if cursor.rowcount == 0:
                    cursor.execute("""
                        SELECT UnitPrice FROM ServiceEstimatePart
                        WHERE EstimateID = %s AND PartID = %s
                    """, (approved["EstimateID"], part_id))
                    estimate_part = cursor.fetchone()
                    cursor.execute("""
                        INSERT INTO PartUsage
                            (ServiceID, PartID, QuantityUsed, UnitPrice, StockDeducted)
                        VALUES (%s, %s, %s, %s, FALSE)
                    """, (service_id, part_id, quantity, estimate_part["UnitPrice"]))

        # If a prefilled approved part is omitted, it was not used.
        for part_id in approved_parts:
            if part_id not in seen:
                cursor.execute("""
                    DELETE FROM PartUsage
                    WHERE ServiceID = %s AND PartID = %s AND StockDeducted = FALSE
                """, (service_id, part_id))

        cursor.execute("""
            UPDATE ServiceRecord
            SET ActualPartsConfirmed = TRUE
            WHERE ServiceID = %s
        """, (service_id,))
        connection.commit()
        return jsonify({"message": "Actual parts used recorded", "service_id": service_id})
    except Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Could not record actual parts")
        return error_response("Could not record actual parts", 500)
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
            SELECT ServiceID, AppointmentID, MechanicID, Status, ActualPartsConfirmed
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
        if not service.get("ActualPartsConfirmed"):
            connection.rollback()
            return error_response(
                "Record and confirm the actual parts used before completing the service",
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
        if not labor_total or Decimal(str(labor_total)) == Decimal("0"):
            cursor.execute("""
                SELECT LaborCost FROM ServiceEstimate
                WHERE ServiceID = %s AND Status = 'Approved'
            """, (service_id,))
            estimate_labor = cursor.fetchone()
            if estimate_labor and estimate_labor["LaborCost"] is not None:
                labor_total = estimate_labor["LaborCost"]

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


# ---------------- STAFF INVOICE LIST ----------------

@app.get("/api/invoices")
@role_required("Admin")
def list_invoices_for_payment():
    try:
        invoices = fetch_all("""
            SELECT
                i.InvoiceID,
                i.ServiceID,
                i.InvoiceDate,
                i.TotalAmount,
                CASE
    WHEN COALESCE(p.AmountPaid, 0) >= i.TotalAmount THEN 'Paid'
    WHEN COALESCE(p.AmountPaid, 0) > 0 THEN 'Partially Paid'
    ELSE 'Unpaid'
END AS PaymentStatus,
                i.PaymentMethod,
                c.Name AS CustomerName,
                v.RegistrationNo,
                v.Brand,
                v.Model,
                COALESCE(p.AmountPaid, 0) AS AmountPaid,
                GREATEST(
                    i.TotalAmount - COALESCE(p.AmountPaid, 0),
                    0
                ) AS OutstandingBalance
            FROM Invoice i
            JOIN ServiceRecord sr
                ON sr.ServiceID = i.ServiceID
            JOIN Appointment a
                ON a.AppointmentID = sr.AppointmentID
            JOIN Vehicle v
                ON v.VehicleID = a.VehicleID
            JOIN Customer c
                ON c.CustomerID = v.CustomerID
            LEFT JOIN (
                SELECT InvoiceID, SUM(Amount) AS AmountPaid
                FROM Payment
                GROUP BY InvoiceID
            ) p ON p.InvoiceID = i.InvoiceID
            ORDER BY i.InvoiceDate DESC, i.InvoiceID DESC
        """)

        return jsonify(invoices)

    except Error:
        app.logger.exception("Could not list invoices")
        return error_response("Could not retrieve invoices", 500)



# ---------------- INVOICE DETAILS ----------------


@app.get("/api/invoices/<int:invoice_id>")
@role_required("Admin")
def get_invoice_details(invoice_id):
    try:
        invoice = fetch_one("""
            SELECT
                i.InvoiceID,
                i.ServiceID,
                i.InvoiceDate,
                i.TotalAmount,
                i.PaymentMethod,
                sr.AppointmentID,
                sr.StartDate AS ServiceStartDate,
                sr.EndDate AS ServiceEndDate,
                sr.Odometer,
                sr.Status AS ServiceStatus,
                c.CustomerID,
                c.Name AS CustomerName,
                c.Email AS CustomerEmail,
                c.Phone AS CustomerPhone,
                c.Address AS CustomerAddress,
                v.VehicleID,
                v.RegistrationNo,
                v.Brand,
                v.Model,
                v.ManufactureYear,
                COALESCE(p.AmountPaid, 0) AS AmountPaid,
                GREATEST(
                    i.TotalAmount - COALESCE(p.AmountPaid, 0),
                    0
                ) AS OutstandingBalance
            FROM Invoice i
            JOIN ServiceRecord sr
                ON sr.ServiceID = i.ServiceID
            JOIN Appointment a
                ON a.AppointmentID = sr.AppointmentID
            JOIN Vehicle v
                ON v.VehicleID = a.VehicleID
            JOIN Customer c
                ON c.CustomerID = v.CustomerID
            LEFT JOIN (
                SELECT InvoiceID, SUM(Amount) AS AmountPaid
                FROM Payment
                GROUP BY InvoiceID
            ) p ON p.InvoiceID = i.InvoiceID
            WHERE i.InvoiceID = %s
        """, (invoice_id,))

        if not invoice:
            return error_response("Invoice not found", 404)

        payments = fetch_all("""
            SELECT
                p.PaymentID,
                p.Amount,
                p.PaymentMethod,
                p.PaymentDate,
                e.Name AS RecordedByName
            FROM Payment p
            JOIN Employee e
                ON e.EmployeeID = p.RecordedBy
            WHERE p.InvoiceID = %s
            ORDER BY p.PaymentDate ASC, p.PaymentID ASC
        """, (invoice_id,))

        amount_paid = sum(
            (float(payment["Amount"]) for payment in payments),
            0.0
        )
        total_amount = float(invoice["TotalAmount"])
        outstanding = round(max(total_amount - amount_paid, 0), 2)

        invoice["AmountPaid"] = round(amount_paid, 2)
        invoice["OutstandingBalance"] = outstanding
        invoice["PaymentStatus"] = (
            "Paid" if outstanding <= 0
            else "Partially Paid" if amount_paid > 0
            else "Unpaid"
        )
        invoice["Payments"] = payments

        return jsonify(invoice)

    except Error:
        app.logger.exception("Could not retrieve invoice details")
        return error_response("Could not retrieve invoice details", 500)



# ---------------- PAYMENT HISTORY ----------------

@app.get("/api/payments")
@role_required("Admin")
def list_payment_history():
    try:
        payments = fetch_all("""
            SELECT
                p.PaymentID,
                p.InvoiceID,
                p.Amount,
                p.PaymentMethod,
                p.PaymentDate,
                p.RecordedBy,
                i.ServiceID,
                i.TotalAmount AS InvoiceTotal,
                c.Name AS CustomerName,
                v.RegistrationNo,
                e.Name AS RecordedByName
            FROM Payment p
            JOIN Invoice i
                ON i.InvoiceID = p.InvoiceID
            JOIN ServiceRecord sr
                ON sr.ServiceID = i.ServiceID
            JOIN Appointment a
                ON a.AppointmentID = sr.AppointmentID
            JOIN Vehicle v
                ON v.VehicleID = a.VehicleID
            JOIN Customer c
                ON c.CustomerID = v.CustomerID
            JOIN Employee e
                ON e.EmployeeID = p.RecordedBy
            ORDER BY p.PaymentDate DESC, p.PaymentID DESC
        """)

        return jsonify(payments)

    except Error:
        app.logger.exception("Could not list payment history")
        return error_response("Could not retrieve payment history", 500)


# ---------------- RECORD INVOICE PAYMENT ----------------

@app.post("/api/invoices/<int:invoice_id>/payments")
@role_required("Admin")
def record_invoice_payment(invoice_id):
    from decimal import Decimal, InvalidOperation

    claims = get_jwt()
    employee_id = claims.get("employee_id")

    if employee_id is None:
        return error_response(
            "Staff account is not linked to an employee profile",
            403
        )

    data = read_json()
    if data is None:
        return error_response("Send a valid JSON object", 400)

    raw_amount = data.get("Amount")
    method = data.get("PaymentMethod")

    # Validate amount.
    if isinstance(raw_amount, bool) or raw_amount is None:
        return error_response("A valid payment amount is required", 400)

    try:
        amount = Decimal(str(raw_amount))
    except (InvalidOperation, ValueError, TypeError):
        return error_response("Enter a valid payment amount", 400)

    if not amount.is_finite() or amount <= 0:
        return error_response("Payment amount must be greater than zero", 400)

    if amount.as_tuple().exponent < -2:
        return error_response(
            "Payment amount can have at most two decimal places", 400
        )

    if amount > Decimal("9999999999.99"):
        return error_response("Payment amount is too large", 400)

    allowed_methods = {"Cash", "UPI", "Card", "Bank Transfer"}
    if not isinstance(method, str) or method not in allowed_methods:
        return error_response(
            "PaymentMethod must be Cash, UPI, Card, or Bank Transfer",
            400
        )

    connection = None
    cursor = None

    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

        # Lock this invoice so concurrent requests cannot overpay it.
        cursor.execute("""
            SELECT InvoiceID, ServiceID, TotalAmount,
                   PaymentStatus, PaymentMethod
            FROM Invoice
            WHERE InvoiceID = %s
            FOR UPDATE
        """, (invoice_id,))

        invoice = cursor.fetchone()

        if invoice is None:
            connection.rollback()
            return error_response("Invoice not found", 404)

        total_amount = Decimal(str(invoice["TotalAmount"]))

        cursor.execute("""
            SELECT COALESCE(SUM(Amount), 0) AS AmountPaid
            FROM Payment
            WHERE InvoiceID = %s
        """, (invoice_id,))

        amount_paid = Decimal(str(cursor.fetchone()["AmountPaid"]))
        outstanding = total_amount - amount_paid

        if outstanding <= 0:
            connection.rollback()
            return error_response("This invoice is already fully paid", 409)

        if amount > outstanding:
            connection.rollback()
            return error_response(
                f"Payment exceeds the outstanding balance of {outstanding:.2f}",
                409
            )

        # Record the payment using the authenticated staff employee ID.
        cursor.execute("""
            INSERT INTO Payment
                (InvoiceID, Amount, PaymentMethod, RecordedBy)
            VALUES (%s, %s, %s, %s)
        """, (invoice_id, amount, method, int(employee_id)))

        payment_id = cursor.lastrowid

        new_amount_paid = amount_paid + amount
        new_status = (
            "Paid" if new_amount_paid >= total_amount
            else "Partially Paid"
        )

        # Keep the existing invoice fields synchronized.
        cursor.execute("""
            UPDATE Invoice
            SET PaymentStatus = %s,
                PaymentMethod = %s
            WHERE InvoiceID = %s
        """, (new_status, method, invoice_id))

        connection.commit()

        return jsonify({
            "message": "Payment recorded successfully",
            "payment": {
                "PaymentID": payment_id,
                "InvoiceID": invoice_id,
                "Amount": str(amount),
                "PaymentMethod": method,
                "RecordedBy": int(employee_id)
            },
            "invoice": {
                "InvoiceID": invoice_id,
                "TotalAmount": str(total_amount),
                "AmountPaid": str(new_amount_paid),
                "OutstandingBalance": str(total_amount - new_amount_paid),
                "PaymentStatus": new_status,
                "PaymentMethod": method
            }
        }), 201

    except Error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Could not record invoice payment")
        return error_response("Could not record payment", 500)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    # Local development only; do not expose the debug server publicly.
    app.run(host="127.0.0.1", port=5000, debug=True)

