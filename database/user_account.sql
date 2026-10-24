
USE VehicleServiceDB;

CREATE TABLE IF NOT EXISTS UserAccount (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Email VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    Role VARCHAR(30) NOT NULL DEFAULT 'Customer',
    CustomerID INT UNIQUE,
    EmployeeID INT UNIQUE,
    IsActive BOOLEAN NOT NULL DEFAULT TRUE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_customer
        FOREIGN KEY (CustomerID)
        REFERENCES Customer(CustomerID)
        ON DELETE RESTRICT,

    CONSTRAINT fk_user_employee
        FOREIGN KEY (EmployeeID)
        REFERENCES Employee(EmployeeID)
        ON DELETE RESTRICT,

    CONSTRAINT chk_user_role
        CHECK (Role IN (
            'Admin', 'Mechanic', 'Service Advisor', 'Customer'
        )),

    CONSTRAINT chk_user_profile
        CHECK (
            (Role = 'Customer'
             AND CustomerID IS NOT NULL
             AND EmployeeID IS NULL)
            OR
            (Role IN ('Admin', 'Mechanic', 'Service Advisor')
             AND EmployeeID IS NOT NULL
             AND CustomerID IS NULL)
        )
);
DESCRIBE UserAccount;
SELECT UserID, Email, PasswordHash, Role, CustomerID
FROM UserAccount
WHERE Email = 'authtest@example.com';
