CREATE DATABASE IF NOT EXISTS VehicleServiceDB;

USE VehicleServiceDB;

SELECT DATABASE();

-- 1. Customers
CREATE TABLE IF NOT EXISTS Customer (
    CustomerID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Phone VARCHAR(15) NOT NULL UNIQUE,
    Email VARCHAR(100) UNIQUE,
    Address VARCHAR(255),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Vehicles owned by customers
CREATE TABLE IF NOT EXISTS Vehicle (
    VehicleID INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID INT NOT NULL,
    RegistrationNo VARCHAR(20) NOT NULL UNIQUE,
    Brand VARCHAR(50) NOT NULL,
    Model VARCHAR(50) NOT NULL,
    ManufactureYear YEAR,
    FuelType VARCHAR(20),
    FOREIGN KEY (CustomerID)
        REFERENCES Customer(CustomerID)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 3. Workshop employees and mechanics
CREATE TABLE IF NOT EXISTS Employee (
    EmployeeID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Role VARCHAR(30) NOT NULL,
    Phone VARCHAR(15) UNIQUE,
    Email VARCHAR(100) UNIQUE,
    Salary DECIMAL(10,2),
    CHECK (Salary IS NULL OR Salary >= 0),
    CHECK (Role IN ('Admin', 'Service Advisor', 'Mechanic'))
);

-- 4. Services offered by the workshop
CREATE TABLE IF NOT EXISTS ServiceType (
    ServiceTypeID INT AUTO_INCREMENT PRIMARY KEY,
    ServiceName VARCHAR(100) NOT NULL UNIQUE,
    Description VARCHAR(255),
    BasePrice DECIMAL(10,2) NOT NULL,
    EstimatedMinutes INT NOT NULL,
    CHECK (BasePrice >= 0),
    CHECK (EstimatedMinutes > 0)
);

-- 5. Customer appointments
CREATE TABLE IF NOT EXISTS Appointment (
    AppointmentID INT AUTO_INCREMENT PRIMARY KEY,
    VehicleID INT NOT NULL,
    AppointmentDate DATETIME NOT NULL,
    Complaint VARCHAR(500),
    Status VARCHAR(20) NOT NULL DEFAULT 'Booked',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (VehicleID)
        REFERENCES Vehicle(VehicleID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (Status IN (
        'Booked', 'Confirmed', 'Cancelled', 'Completed'
    ))
);

-- 6. Actual service work performed
CREATE TABLE IF NOT EXISTS ServiceRecord (
    ServiceID INT AUTO_INCREMENT PRIMARY KEY,
    AppointmentID INT NOT NULL UNIQUE,
    MechanicID INT,
    StartDate DATETIME,
    EndDate DATETIME,
    Odometer INT,
    Status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    FOREIGN KEY (AppointmentID)
        REFERENCES Appointment(AppointmentID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (MechanicID)
        REFERENCES Employee(EmployeeID)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (Odometer IS NULL OR Odometer >= 0),
    CHECK (Status IN (
        'Pending', 'In Progress', 'Completed'
    )),
    CHECK (
        EndDate IS NULL OR StartDate IS NULL
        OR EndDate >= StartDate
    )
);

-- 7. Tasks/services included in each service record
CREATE TABLE IF NOT EXISTS ServiceTask (
    TaskID INT AUTO_INCREMENT PRIMARY KEY,
    ServiceID INT NOT NULL,
    ServiceTypeID INT NOT NULL,
    LaborCost DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (ServiceID)
        REFERENCES ServiceRecord(ServiceID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (ServiceTypeID)
        REFERENCES ServiceType(ServiceTypeID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (LaborCost >= 0),
    UNIQUE (ServiceID, ServiceTypeID)
);

-- 8. Spare-parts inventory
CREATE TABLE IF NOT EXISTS Part (
    PartID INT AUTO_INCREMENT PRIMARY KEY,
    PartName VARCHAR(100) NOT NULL UNIQUE,
    StockQuantity INT NOT NULL DEFAULT 0,
    UnitPrice DECIMAL(10,2) NOT NULL,
    ReorderLevel INT NOT NULL DEFAULT 5,
    CHECK (StockQuantity >= 0),
    CHECK (UnitPrice >= 0),
    CHECK (ReorderLevel >= 0)
);

-- 9. Parts consumed by a service
CREATE TABLE IF NOT EXISTS PartUsage (
    ServiceID INT NOT NULL,
    PartID INT NOT NULL,
    QuantityUsed INT NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (ServiceID, PartID),
    FOREIGN KEY (ServiceID)
        REFERENCES ServiceRecord(ServiceID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (PartID)
        REFERENCES Part(PartID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (QuantityUsed > 0),
    CHECK (UnitPrice >= 0)
);

-- 10. Invoice for a service record
CREATE TABLE IF NOT EXISTS Invoice (
    InvoiceID INT AUTO_INCREMENT PRIMARY KEY,
    ServiceID INT NOT NULL UNIQUE,
    InvoiceDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    TotalAmount DECIMAL(12,2) NOT NULL DEFAULT 0,
    PaymentStatus VARCHAR(20) NOT NULL DEFAULT 'Unpaid',
    PaymentMethod VARCHAR(20),
    FOREIGN KEY (ServiceID)
        REFERENCES ServiceRecord(ServiceID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (TotalAmount >= 0),
    CHECK (PaymentStatus IN (
        'Unpaid', 'Partially Paid', 'Paid'
    )),
    CHECK (
        PaymentMethod IS NULL OR PaymentMethod IN (
            'Cash', 'UPI', 'Card', 'Bank Transfer'
        )
    )
);
USE VehicleServiceDB;

SHOW TABLES;

CREATE TABLE IF NOT EXISTS Payment (
    PaymentID INT AUTO_INCREMENT PRIMARY KEY,
    InvoiceID INT NOT NULL,
    Amount DECIMAL(12,2) NOT NULL,
    PaymentMethod VARCHAR(20) NOT NULL,
    PaymentDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    RecordedBy INT NOT NULL,

    CONSTRAINT fk_payment_invoice
        FOREIGN KEY (InvoiceID)
        REFERENCES Invoice(InvoiceID)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_payment_employee
        FOREIGN KEY (RecordedBy)
        REFERENCES Employee(EmployeeID)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_payment_amount
        CHECK (Amount > 0),

    CONSTRAINT chk_payment_method
        CHECK (PaymentMethod IN (
            'Cash', 'UPI', 'Card', 'Bank Transfer'
        ))
);

SHOW COLUMNS FROM Payment;

DESCRIBE Payment;
SELECT * FROM Payment;
