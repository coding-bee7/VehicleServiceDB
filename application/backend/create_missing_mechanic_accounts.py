
import getpass
import os

import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

TARGETS = [
    {
        "employee_id": 2,
        "name": "Mehul Parmar",
        "email": "mehul@workshop.com",
    },
    {
        "employee_id": 5,
        "name": "Vikas Patel",
        "email": "vikas@workshop.com",
    },
]


def main():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "VehicleServiceDB"),
    )

    try:
        cursor = connection.cursor(dictionary=True)
        connection.start_transaction()

        # Confirm that the intended single admin still exists.
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM UserAccount
            WHERE Role = 'Admin' AND IsActive = TRUE
        """)
        if cursor.fetchone()["total"] != 1:
            raise RuntimeError(
                "Expected exactly one active admin account. No changes made."
            )

        for target in TARGETS:
            cursor.execute("""
                SELECT EmployeeID, Name, Role, Email
                FROM Employee
                WHERE EmployeeID = %s
                FOR UPDATE
            """, (target["employee_id"],))
            employee = cursor.fetchone()

            if (
                employee is None
                or employee["Name"] != target["name"]
                or employee["Role"] != "Mechanic"
                or (employee["Email"] or "").strip().lower()
                != target["email"]
            ):
                raise RuntimeError(
                    f"Employee validation failed for {target['name']}. "
                    "No changes made."
                )

            cursor.execute("""
                SELECT UserID, Email, EmployeeID, CustomerID, Role
                FROM UserAccount
                WHERE EmployeeID = %s
                   OR LOWER(Email) = LOWER(%s)
                FOR UPDATE
            """, (target["employee_id"], target["email"]))
            conflicts = cursor.fetchall()

            if conflicts:
                raise RuntimeError(
                    f"An account or email conflict exists for "
                    f"{target['name']}. No changes made."
                )

        for target in TARGETS:
            password = getpass.getpass(
                f"Set password for {target['name']} "
                f"({target['email']}): "
            )
            confirmation = getpass.getpass("Confirm password: ")

            if password != confirmation:
                raise RuntimeError("Passwords did not match.")
            if not 12 <= len(password) <= 128:
                raise RuntimeError(
                    "Password must contain 12–128 characters."
                )

            cursor.execute("""
                INSERT INTO UserAccount
                    (Email, PasswordHash, Role, EmployeeID,
                     CustomerID, IsActive)
                VALUES (%s, %s, 'Mechanic', %s, NULL, TRUE)
            """, (
                target["email"],
                generate_password_hash(password),
                target["employee_id"],
            ))

        connection.commit()
        print("Both mechanic accounts were created successfully.")

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
