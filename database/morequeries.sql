show databases;

use vehicleservicedb;
show tables;

SHOW DATABASES LIKE '%vehicle%';

USE VehicleServiceDB;
SHOW TABLES LIKE 'UserAccount';

SELECT DATABASE();
SHOW TABLES LIKE 'Customer';
SHOW TABLES LIKE 'Employee';
SHOW TABLES LIKE 'UserAccount';

SELECT UserID, Email, Role, CustomerID, EmployeeID
FROM UserAccount;

SELECT VehicleID, CustomerID, RegistrationNo, Brand, Model
FROM Vehicle;

SELECT AppointmentID, VehicleID, AppointmentDate, Complaint, Status
FROM Appointment;

SELECT ServiceID, AppointmentID, Status
FROM ServiceRecord;

SELECT
    UserID,
    Email,
    Role,
    CustomerID,
    EmployeeID,
    IsActive
FROM UserAccount
ORDER BY UserID;

SELECT CustomerID, Name
FROM Customer
ORDER BY CustomerID;

USE VehicleServiceDB;

INSERT INTO Vehicle
    (CustomerID, RegistrationNo, Brand, Model, ManufactureYear, FuelType)
VALUES
    (6, 'GJ05TEST06', 'Maruti Suzuki', 'Swift', 2024, 'Petrol');
    
SELECT VehicleID, CustomerID, RegistrationNo, Brand, Model
FROM Vehicle
WHERE CustomerID = 6;

DESCRIBE Appointment;

USE VehicleServiceDB;

SELECT
    a.AppointmentID,
    a.VehicleID,
    v.RegistrationNo,
    a.AppointmentDate,
    a.Complaint,
    a.Status
FROM Appointment a
JOIN Vehicle v ON v.VehicleID = a.VehicleID
WHERE v.RegistrationNo = 'GJ05TEST06'
ORDER BY a.AppointmentID DESC;

select * from UserAccount;

SELECT *
FROM UserAccount
WHERE Role = 'Admin';

DESCRIBE UserAccount;

SELECT UserID, Email, Role, CustomerID, EmployeeID, IsActive
FROM UserAccount;

SHOW CREATE TABLE UserAccount;

SELECT
    CONSTRAINT_NAME,
    CHECK_CLAUSE
FROM information_schema.CHECK_CONSTRAINTS
WHERE CONSTRAINT_NAME = 'chk_user_profile';

SELECT * FROM Employee;

SELECT UserID, Email, Role, CustomerID, EmployeeID, IsActive
FROM UserAccount
WHERE Email = 'arjun@workshop.com';

SHOW CREATE TABLE Appointment;
SHOW CREATE TABLE PartUsage;
SHOW CREATE TABLE UserAccount;

SELECT Status, COUNT(*) AS Total
FROM Appointment
GROUP BY Status;

SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'PartUsage'
  AND COLUMN_NAME = 'StockDeducted';
  
  ALTER TABLE PartUsage
ADD COLUMN StockDeducted BOOLEAN NOT NULL DEFAULT FALSE;


SHOW COLUMNS FROM PartUsage LIKE 'StockDeducted';

ALTER TABLE Appointment
DROP CHECK appointment_chk_1;

ALTER TABLE Appointment
ADD CONSTRAINT appointment_chk_1
CHECK (
    Status IN (
        'Booked',
        'Pending',
        'Confirmed',
        'In Progress',
        'Completed',
        'Cancelled'
    )
);

SELECT
    sr.ServiceID,
    sr.Status AS ServiceStatus,
    a.AppointmentID,
    a.Status AS AppointmentStatus
FROM ServiceRecord sr
LEFT JOIN Appointment a
    ON a.AppointmentID = sr.AppointmentID
ORDER BY sr.ServiceID;


USE VehicleServiceDB;

-- Parts assigned to Service 4
SELECT
    pu.ServiceID,
    pu.PartID,
    p.PartName,
    pu.QuantityUsed,
    pu.UnitPrice,
    p.StockQuantity,
    pu.StockDeducted
FROM PartUsage pu
JOIN Part p ON p.PartID = pu.PartID
WHERE pu.ServiceID = 4;

-- Existing invoice for Service 4
SELECT *
FROM Invoice
WHERE ServiceID = 4;

-- Service details
SELECT *
FROM ServiceRecord
WHERE ServiceID = 4;


USE VehicleServiceDB;

-- Verify service and appointment status
SELECT
    sr.ServiceID,
    sr.Status AS ServiceStatus,
    sr.EndDate,
    a.Status AS AppointmentStatus
FROM ServiceRecord sr
JOIN Appointment a
    ON a.AppointmentID = sr.AppointmentID
WHERE sr.ServiceID = 4;

-- Verify stock deduction
SELECT
    p.PartID,
    p.PartName,
    p.StockQuantity,
    pu.QuantityUsed,
    pu.StockDeducted
FROM PartUsage pu
JOIN Part p ON p.PartID = pu.PartID
WHERE pu.ServiceID = 4;

-- Verify invoice
SELECT
    InvoiceID,
    ServiceID,
    TotalAmount,
    PaymentStatus,
    PaymentMethod
FROM Invoice
WHERE ServiceID = 4;

INSERT INTO Vehicle
(CustomerID, RegistrationNo, Brand, Model)
VALUES
(999999, 'TEST000001', 'TestBrand', 'TestModel');

SELECT
    e.EmployeeID,
    e.Name,
    e.Role,
    e.Email AS EmployeeEmail,
    ua.UserID,
    ua.Email AS LoginEmail,
    ua.IsActive
FROM Employee e
LEFT JOIN UserAccount ua
    ON ua.EmployeeID = e.EmployeeID
WHERE e.Role = 'Mechanic'
ORDER BY e.EmployeeID;

SELECT EmployeeID, Name, Role, Email
FROM Employee
WHERE EmployeeID = 3;

SELECT UserID, Email, Role, EmployeeID
FROM UserAccount
WHERE EmployeeID = 3;

SELECT UserID, Email
FROM UserAccount
WHERE Email = 'ravi.mechanic@workshop.com';

INSERT INTO UserAccount
    (Email, PasswordHash, Role, EmployeeID, IsActive)
VALUES
    (
        'ravi.mechanic@workshop.com',
        'scrypt:32768:8:1$5nDmz3e8ltUFEgqX$fef6e6149eaa1b2c6dccb7492fdffb1ad0ce0653b674b7c7d558d40dc91fddcdeb8cb3bbdca2a7854bd5e10d19729380d8534cbffacf1aef7d4a6316bfe69433',
        'Mechanic',
        3,
        TRUE
    );
    
    SELECT
    ua.UserID,
    ua.Email,
    ua.Role,
    ua.EmployeeID,
    e.Name,
    ua.IsActive
FROM UserAccount ua
JOIN Employee e ON e.EmployeeID = ua.EmployeeID
WHERE ua.EmployeeID = 3;

SELECT
    sr.ServiceID,
    sr.AppointmentID,
    sr.MechanicID,
    e.Name AS MechanicName,
    sr.Status AS ServiceStatus,
    a.Status AS AppointmentStatus
FROM ServiceRecord sr
LEFT JOIN Employee e ON sr.MechanicID = e.EmployeeID
LEFT JOIN Appointment a ON sr.AppointmentID = a.AppointmentID
ORDER BY sr.ServiceID;

SELECT
    ServiceID,
    AppointmentID,
    MechanicID,
    StartDate,
    EndDate,
    Status,
    Odometer
FROM ServiceRecord
WHERE ServiceID = 5;

SELECT *
FROM PartUsage
WHERE ServiceID = 5;

SELECT EmployeeID, Name, Role, Email
FROM Employee
WHERE EmployeeID = 4;

SELECT UserID, Email, Role, EmployeeID, IsActive
FROM UserAccount
WHERE EmployeeID = 4;

USE VehicleServiceDB;

INSERT INTO UserAccount
    (Email, PasswordHash, Role, EmployeeID, IsActive)
VALUES
    (
        'sanjay@workshop.com',
        'scrypt:32768:8:1$GLVlo3WJ6foEJipm$94438d13c48cf86ba3802df42ac4649a21e769b003f2be484dea2058b8ef43a4e4f4b2f9509bbb9b6598f66fd85e2e58b55397bacc1789035491e9e49560714e',
        'Mechanic',
        4,
        TRUE
    );
    
SELECT UserID, Email, Role, EmployeeID, IsActive
FROM UserAccount
WHERE EmployeeID = 4;

SELECT
    sr.ServiceID,
    sr.Status AS ServiceStatus,
    sr.StartDate,
    sr.EndDate,
    a.Status AS AppointmentStatus
FROM ServiceRecord sr
JOIN Appointment a
    ON a.AppointmentID = sr.AppointmentID
WHERE sr.ServiceID = 5;

SELECT
    InvoiceID,
    ServiceID,
    TotalAmount,
    PaymentStatus,
    PaymentMethod
FROM Invoice
WHERE ServiceID = 5;

SELECT *
FROM PartUsage
WHERE ServiceID = 5;

SELECT
    sr.ServiceID,
    sr.Status AS ServiceStatus,
    a.Status AS AppointmentStatus,
    sr.StartDate,
    sr.EndDate,
    i.InvoiceID,
    i.TotalAmount,
    i.PaymentStatus
FROM ServiceRecord sr
JOIN Appointment a
    ON a.AppointmentID = sr.AppointmentID
LEFT JOIN Invoice i
    ON i.ServiceID = sr.ServiceID
WHERE sr.ServiceID = 5;

SELECT
    c.CustomerID,
    c.Name,
    c.Email,
    a.AppointmentID,
    sr.ServiceID,
    sr.Status AS ServiceStatus
FROM ServiceRecord sr
JOIN Appointment a
    ON a.AppointmentID = sr.AppointmentID
JOIN Vehicle v
    ON v.VehicleID = a.VehicleID
JOIN Customer c
    ON c.CustomerID = v.CustomerID
WHERE sr.ServiceID = 5;

SELECT UserID, Email, Role, CustomerID, IsActive
FROM UserAccount
WHERE CustomerID = 5;

SELECT
    InvoiceID,
    ServiceID,
    TotalAmount,
    PaymentStatus,
    PaymentMethod
FROM Invoice
ORDER BY InvoiceID;

SELECT
    EmployeeID,
    Name,
    Role
FROM Employee
ORDER BY EmployeeID;

SELECT
    i.InvoiceID,
    i.TotalAmount,
    i.PaymentStatus,
    COALESCE(SUM(p.Amount), 0) AS AmountPaid,
    i.TotalAmount - COALESCE(SUM(p.Amount), 0) AS OutstandingBalance
FROM Invoice i
LEFT JOIN Payment p ON p.InvoiceID = i.InvoiceID
GROUP BY
    i.InvoiceID,
    i.TotalAmount,
    i.PaymentStatus
ORDER BY i.InvoiceID;

DESCRIBE ServiceRecord;
DESCRIBE Customer;

SELECT *
FROM Customer
WHERE Email = 'karan@example.com';

show tables;
describe Customer;
DESCRIBE useraccount;

SELECT *
FROM useraccount
WHERE Email = 'karan@example.com';

SELECT
    UserID,
    Email,
    Role,
    CustomerID,
    EmployeeID,
    IsActive
FROM useraccount
WHERE Email = 'karan@example.com';

SELECT
    UserID,
    Email,
    Role,
    CustomerID,
    IsActive
FROM useraccount
WHERE CustomerID = 5;

SELECT
    UserID,
    Email,
    Role,
    CustomerID,
    EmployeeID,
    IsActive
FROM useraccount
WHERE Email = 'karan@example.com';

USE VehicleServiceDB;

SELECT
    EmployeeID,
    Name,
    Role,
    Email,
    Phone
FROM Employee
ORDER BY Role, EmployeeID;

SELECT
    e.EmployeeID,
    e.Name,
    e.Role,
    e.Email,
    e.Phone
FROM Employee e
LEFT JOIN UserAccount u
    ON u.EmployeeID = e.EmployeeID
WHERE u.UserID IS NULL
ORDER BY e.Role, e.EmployeeID;

SELECT
    u.UserID,
    u.Email AS LoginEmail,
    u.Role AS LoginRole,
    u.EmployeeID,
    e.Name AS EmployeeName,
    e.Role AS EmployeeRole,
    u.IsActive
FROM UserAccount u
LEFT JOIN Employee e
    ON e.EmployeeID = u.EmployeeID
WHERE u.EmployeeID IS NOT NULL
ORDER BY u.EmployeeID;

SHOW CREATE TABLE Employee;
SHOW CREATE TABLE UserAccount;

SELECT
    UserID,
    Email,
    Role,
    CustomerID,
    EmployeeID,
    IsActive
FROM UserAccount
ORDER BY UserID;

SELECT
    e.EmployeeID,
    e.Name,
    e.Role AS EmployeeRole,
    e.Email,
    u.UserID,
    u.Role AS AccountRole,
    u.EmployeeID AS LinkedEmployeeID
FROM Employee e
LEFT JOIN UserAccount u
    ON u.EmployeeID = e.EmployeeID
WHERE e.EmployeeID IN (1, 2, 3, 4, 5)
ORDER BY e.EmployeeID;

USE VehicleServiceDB;

-- Convert Mehul from Service Advisor to Mechanic.
UPDATE Employee
SET Role = 'Mechanic'
WHERE EmployeeID = 2
  AND Role = 'Service Advisor';

-- Restrict employee roles to Admin and Mechanic.
ALTER TABLE Employee
    DROP CHECK employee_chk_2;

ALTER TABLE Employee
    ADD CONSTRAINT chk_employee_role
    CHECK (Role IN ('Admin', 'Mechanic'));

-- Remove Service Advisor from account-role validation.
ALTER TABLE UserAccount
    DROP CHECK chk_user_profile;

ALTER TABLE UserAccount
    DROP CHECK chk_user_role;

ALTER TABLE UserAccount
    ADD CONSTRAINT chk_user_profile
    CHECK (
        (
            Role = 'Customer'
            AND CustomerID IS NOT NULL
            AND EmployeeID IS NULL
        )
        OR
        (
            Role IN ('Admin', 'Mechanic')
            AND EmployeeID IS NOT NULL
            AND CustomerID IS NULL
        )
    );

ALTER TABLE UserAccount
    ADD CONSTRAINT chk_user_role
    CHECK (Role IN ('Admin', 'Mechanic', 'Customer'));

SELECT UserID, Email, EmployeeID, CustomerID, Role
FROM UserAccount
WHERE LOWER(Email) IN (
    'vikas@workshop.com',
    'mehul@workshop.com'
);

SELECT EmployeeID, Name, Role, Email
FROM Employee
ORDER BY EmployeeID;

SELECT UserID, Email, Role, EmployeeID, CustomerID, IsActive
FROM UserAccount
ORDER BY UserID;

SELECT
    u.UserID,
    u.Email,
    u.Role,
    u.EmployeeID,
    e.Name,
    u.IsActive
FROM UserAccount u
JOIN Employee e ON e.EmployeeID = u.EmployeeID
WHERE u.EmployeeID IN (2, 5)
ORDER BY u.EmployeeID;

SELECT
    e.EmployeeID,
    e.Name,
    e.Role AS EmployeeRole,
    u.Email,
    u.Role AS AccountRole,
    u.IsActive
FROM Employee e
JOIN UserAccount u ON u.EmployeeID = e.EmployeeID
WHERE u.Email = 'rohit@example.com';