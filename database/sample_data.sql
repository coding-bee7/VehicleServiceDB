
USE VehicleServiceDB;

START TRANSACTION;

-- 1. Customers
INSERT INTO Customer
(CustomerID, Name, Phone, Email, Address)
VALUES
(1, 'Rahul Patel', '9876501001',
 'rahul@example.com', 'Adajan, Surat'),
(2, 'Priya Shah', '9876501002',
 'priya@example.com', 'Vesu, Surat'),
(3, 'Amit Desai', '9876501003',
 'amit@example.com', 'City Light, Surat'),
(4, 'Neha Mehta', '9876501004',
 'neha@example.com', 'Piplod, Surat'),
(5, 'Karan Joshi', '9876501005',
 'karan@example.com', 'Varachha, Surat');

-- 2. Vehicles
INSERT INTO Vehicle
(VehicleID, CustomerID, RegistrationNo, Brand,
 Model, ManufactureYear, FuelType)
VALUES
(1, 1, 'GJ05AB1234', 'Maruti Suzuki',
 'Swift', 2022, 'Petrol'),
(2, 2, 'GJ05CD5678', 'Hyundai',
 'Creta', 2023, 'Diesel'),
(3, 3, 'GJ05EF9012', 'Honda',
 'City', 2021, 'Petrol'),
(4, 4, 'GJ05GH3456', 'Tata',
 'Nexon', 2024, 'EV'),
(5, 5, 'GJ05JK7890', 'TVS',
 'Jupiter', 2022, 'Petrol'),
(6, 1, 'GJ05LM2468', 'Maruti Suzuki',
 'Baleno', 2020, 'Petrol');

-- 3. Employees
INSERT INTO Employee
(EmployeeID, Name, Role, Phone, Email, Salary)
VALUES
(1, 'Arjun Singh', 'Admin', '9123400001',
 'arjun@workshop.com', 45000),
(2, 'Mehul Parmar', 'Service Advisor',
 '9123400002', 'mehul@workshop.com', 30000),
(3, 'Ravi Kumar', 'Mechanic', '9123400003',
 'ravi@workshop.com', 25000),
(4, 'Sanjay Yadav', 'Mechanic', '9123400004',
 'sanjay@workshop.com', 27000),
(5, 'Vikas Patel', 'Mechanic', '9123400005',
 'vikas@workshop.com', 26000);

-- 4. Service types
INSERT INTO ServiceType
(ServiceTypeID, ServiceName, Description,
 BasePrice, EstimatedMinutes)
VALUES
(1, 'General Service', 'Routine vehicle inspection',
 1500, 120),
(2, 'Oil Change', 'Engine oil and filter service',
 800, 45),
(3, 'Brake Service', 'Brake inspection and repair',
 2000, 90),
(4, 'AC Service', 'Air conditioning inspection',
 1200, 60),
(5, 'Battery Check', 'Battery testing and inspection',
 500, 30),
(6, 'Wheel Alignment', 'Wheel alignment and balancing',
 1000, 45);

-- 5. Appointments
INSERT INTO Appointment
(AppointmentID, VehicleID, AppointmentDate,
 Complaint, Status)
VALUES
(1, 1, '2026-10-20 10:00:00',
 'Routine maintenance', 'Completed'),
(2, 2, '2026-10-21 11:00:00',
 'Engine oil replacement', 'Completed'),
(3, 3, '2026-10-22 09:30:00',
 'Brake noise', 'Completed'),
(4, 4, '2026-10-24 14:00:00',
 'Battery and general inspection', 'Confirmed'),
(5, 5, '2026-10-25 10:30:00',
 'General service', 'Booked'),
(6, 6, '2026-10-26 12:00:00',
 'AC not cooling properly', 'Booked');

-- 6. Service records
INSERT INTO ServiceRecord
(ServiceID, AppointmentID, MechanicID,
 StartDate, EndDate, Odometer, Status)
VALUES
(1, 1, 3, '2026-10-20 10:10:00',
 '2026-10-20 12:00:00', 25000, 'Completed'),
(2, 2, 4, '2026-10-21 11:10:00',
 '2026-10-21 12:00:00', 18000, 'Completed'),
(3, 3, 3, '2026-10-22 09:40:00',
 '2026-10-22 11:30:00', 32000, 'Completed'),
(4, 4, 5, '2026-10-24 14:10:00',
 NULL, 12000, 'In Progress'),
(5, 5, 4, NULL, NULL, 15000, 'Pending');

-- 7. Tasks performed during services
INSERT INTO ServiceTask
(TaskID, ServiceID, ServiceTypeID, LaborCost)
VALUES
(1, 1, 1, 1500),
(2, 1, 2, 800),
(3, 2, 2, 800),
(4, 3, 3, 2000),
(5, 4, 5, 500),
(6, 5, 1, 1500);

-- 8. Spare parts
INSERT INTO Part
(PartID, PartName, StockQuantity, UnitPrice, ReorderLevel)
VALUES
(1, 'Engine Oil 1L', 50, 450, 10),
(2, 'Oil Filter', 20, 300, 5),
(3, 'Brake Pad Set', 4, 1800, 5),
(4, 'Air Filter', 15, 500, 5),
(5, 'Battery 12V', 8, 4500, 3),
(6, 'Coolant 1L', 3, 250, 5);

-- 9. Parts used by service records
-- These entries record part usage for each service.
-- Inventory is deducted transactionally by the
-- backend service-completion endpoint.
-- StockDeducted tracks whether deduction has occurred.
INSERT INTO PartUsage
(ServiceID, PartID, QuantityUsed, UnitPrice)
VALUES
(1, 1, 3, 450),
(1, 2, 1, 300),
(2, 1, 3, 450),
(2, 2, 1, 300),
(3, 3, 1, 1800),
(4, 5, 1, 4500);

-- 10. Invoices for service records
INSERT INTO Invoice
(InvoiceID, ServiceID, InvoiceDate, TotalAmount,
 PaymentStatus, PaymentMethod)
VALUES
(1, 1, '2026-10-20 12:05:00',
 3950, 'Paid', 'UPI'),
(2, 2, '2026-10-21 12:05:00',
 2450, 'Paid', 'Cash'),
(3, 3, '2026-10-22 11:35:00',
 3800, 'Paid', 'Card'),
(4, 4, '2026-10-24 14:15:00',
 5000, 'Unpaid', NULL);

COMMIT;

-- test starts
-- Confirm inserted data
SELECT 'Customer' AS TableName, COUNT(*) AS Total
FROM Customer
UNION ALL
SELECT 'Vehicle', COUNT(*) FROM Vehicle
UNION ALL
SELECT 'Employee', COUNT(*) FROM Employee
UNION ALL
SELECT 'ServiceType', COUNT(*) FROM ServiceType
UNION ALL
SELECT 'Appointment', COUNT(*) FROM Appointment
UNION ALL
SELECT 'ServiceRecord', COUNT(*) FROM ServiceRecord
UNION ALL
SELECT 'ServiceTask', COUNT(*) FROM ServiceTask
UNION ALL
SELECT 'Part', COUNT(*) FROM Part
UNION ALL
SELECT 'PartUsage', COUNT(*) FROM PartUsage
UNION ALL
SELECT 'Invoice', COUNT(*) FROM Invoice;

SELECT
    c.CustomerID,
    c.Name AS CustomerName,
    v.RegistrationNo,
    v.Brand,
    v.Model
FROM Customer c
JOIN Vehicle v
    ON c.CustomerID = v.CustomerID
ORDER BY c.CustomerID;

SELECT
    c.Name AS CustomerName,
    v.RegistrationNo,
    a.AppointmentDate,
    sr.ServiceID,
    e.Name AS MechanicName,
    sr.Status AS ServiceStatus
FROM Customer c
JOIN Vehicle v
    ON c.CustomerID = v.CustomerID
JOIN Appointment a
    ON v.VehicleID = a.VehicleID
JOIN ServiceRecord sr
    ON a.AppointmentID = sr.AppointmentID
LEFT JOIN Employee e
    ON sr.MechanicID = e.EmployeeID
ORDER BY a.AppointmentDate;


SELECT
    sr.ServiceID,
    COALESCE(l.LaborTotal, 0) AS LaborTotal,
    COALESCE(p.PartsTotal, 0) AS PartsTotal,
    COALESCE(l.LaborTotal, 0)
        + COALESCE(p.PartsTotal, 0) AS CalculatedTotal
FROM ServiceRecord sr
LEFT JOIN (
    SELECT
        ServiceID,
        SUM(LaborCost) AS LaborTotal
    FROM ServiceTask
    GROUP BY ServiceID
) l ON l.ServiceID = sr.ServiceID
LEFT JOIN (
    SELECT
        ServiceID,
        SUM(QuantityUsed * UnitPrice) AS PartsTotal
    FROM PartUsage
    GROUP BY ServiceID
) p ON p.ServiceID = sr.ServiceID
ORDER BY sr.ServiceID;


-- This should fail because customer 999999 does not exist.


SELECT
    PaymentStatus,
    COUNT(*) AS InvoiceCount,
    SUM(TotalAmount) AS InvoiceTotal
FROM Invoice
GROUP BY PaymentStatus;