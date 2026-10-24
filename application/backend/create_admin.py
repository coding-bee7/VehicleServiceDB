
import os
import getpass

import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()


def main():
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password (min 12 characters): ")

    if not email or len(email) > 100 or "@" not in email:
        print("Enter a valid email address.")
        return

    if len(password) < 12 or len(password) > 128:
        print("Password must be 12–128 characters.")
        return

    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "VehicleServiceDB"),
        )
        connection.start_transaction()
        cursor = connection.cursor()

        # Do not allow this script to create another admin.
        cursor.execute("""
            SELECT UserID
            FROM UserAccount
            WHERE Role = 'Admin'
            LIMIT 1
            FOR UPDATE
        """)

        if cursor.fetchone():
            connection.rollback()
            print("An admin already exists. No account was created.")
            return

        # Create a corresponding employee profile.
        cursor.execute("""
            INSERT INTO Employee (Name, Role, Email)
            VALUES (%s, 'Admin', %s)
        """, ("System Administrator", email))

        employee_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO UserAccount
                (Email, PasswordHash, Role, EmployeeID, IsActive)
            VALUES (%s, %s, 'Admin', %s, TRUE)
        """, (
            email,
            generate_password_hash(password),
            employee_id,
        ))

        connection.commit()
        print("Admin account created successfully.")

    except mysql.connector.IntegrityError:
        if connection and connection.is_connected():
            connection.rollback()
        print("That email may already be registered. No account created.")

    except mysql.connector.Error as error:
        if connection and connection.is_connected():
            connection.rollback()
        print("Database setup failed:", error)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
