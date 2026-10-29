USE VehicleServiceDB;

SHOW CREATE TABLE ServiceRecord;
SHOW CREATE TABLE ServiceTask;
SHOW CREATE TABLE PartUsage;
SHOW CREATE TABLE Part;
SHOW CREATE TABLE Invoice;
SHOW CREATE TABLE Appointment;
SHOW CREATE TABLE Employee;

SELECT ServiceID, Status, StartDate, EndDate
FROM ServiceRecord
WHERE ServiceID = 4;

SELECT AppointmentID, Status
FROM Appointment
WHERE AppointmentID = (
    SELECT AppointmentID
    FROM ServiceRecord
    WHERE ServiceID = 4
);

SELECT InvoiceID, ServiceID, TotalAmount,
       PaymentStatus, PaymentMethod, InvoiceDate
FROM Invoice
WHERE ServiceID = 4;

SELECT PartID, QuantityUsed, StockDeducted
FROM PartUsage
WHERE ServiceID = 4;

SELECT PartID, PartName, StockQuantity
FROM Part
WHERE PartID = 5;

SELECT ServiceID, PartID, QuantityUsed, StockDeducted
FROM PartUsage
WHERE ServiceID = 4;