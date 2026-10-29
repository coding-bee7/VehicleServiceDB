
from getpass import getpass

from werkzeug.security import generate_password_hash
from app import get_connection


def main():
    email = input("Admin email: ").strip().lower()

    if not email:
        print("Email cannot be empty.")
        return

    password = getpass("Choose admin password: ")
    confirm = getpass("Confirm admin password: ")

    if not password:
        print("Password cannot be empty.")
        return

    if password != confirm:
        print("Passwords do not match.")
        return

    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT UserID, Role
            FROM UserAccount
            WHERE Email = %s
            """,
            (email,),
        )

        if cursor.fetchone():
            print("This email already exists. No changes made.")
            return

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO UserAccount
                (Email, PasswordHash, Role, CustomerID,
                 EmployeeID, IsActive)
            VALUES (%s, %s, 'Admin', NULL, %s, 1)
            """,
            (email, password_hash, 1),
        )

        connection.commit()
        print("Admin account created successfully.")
        print("Email:", email)

    except Exception as exc:
        connection.rollback()
        print("Admin creation failed:", str(exc))

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
