-- AutoDB inspection + estimate approval workflow (run once against VehicleServiceDB).
USE VehicleServiceDB;

CREATE TABLE IF NOT EXISTS ServiceInspection (
  InspectionID INT AUTO_INCREMENT PRIMARY KEY,
  ServiceID INT NOT NULL UNIQUE,
  MechanicID INT NOT NULL,
  Findings TEXT NOT NULL,
  Odometer INT NULL,
  RecommendedTasks TEXT NOT NULL,
  InspectionDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_inspection_service FOREIGN KEY (ServiceID)
    REFERENCES ServiceRecord(ServiceID) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_inspection_mechanic FOREIGN KEY (MechanicID)
    REFERENCES Employee(EmployeeID) ON UPDATE CASCADE ON DELETE RESTRICT,
  CHECK (Odometer IS NULL OR Odometer >= 0)
);

CREATE TABLE IF NOT EXISTS ServiceEstimate (
  EstimateID INT AUTO_INCREMENT PRIMARY KEY,
  ServiceID INT NOT NULL UNIQUE,
  Status VARCHAR(20) NOT NULL DEFAULT 'Proposed',
  LaborDescription VARCHAR(255) NOT NULL,
  LaborCost DECIMAL(10,2) NOT NULL DEFAULT 0,
  PartsCost DECIMAL(10,2) NOT NULL DEFAULT 0,
  TotalAmount DECIMAL(12,2) NOT NULL DEFAULT 0,
  CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  DecisionAt DATETIME NULL,
  DecisionByCustomerID INT NULL,
  CustomerNotes VARCHAR(500) NULL,
  CONSTRAINT fk_estimate_service FOREIGN KEY (ServiceID)
    REFERENCES ServiceRecord(ServiceID) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_estimate_customer FOREIGN KEY (DecisionByCustomerID)
    REFERENCES Customer(CustomerID) ON UPDATE CASCADE ON DELETE RESTRICT,
  CHECK (Status IN ('Proposed', 'Approved', 'Rejected')),
  CHECK (LaborCost >= 0 AND PartsCost >= 0 AND TotalAmount >= 0)
);

CREATE TABLE IF NOT EXISTS ServiceEstimatePart (
  EstimateID INT NOT NULL,
  PartID INT NOT NULL,
  PartName VARCHAR(100) NOT NULL,
  Quantity INT NOT NULL,
  UnitPrice DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (EstimateID, PartID),
  CONSTRAINT fk_estimate_part_estimate FOREIGN KEY (EstimateID)
    REFERENCES ServiceEstimate(EstimateID) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_estimate_part_part FOREIGN KEY (PartID)
    REFERENCES Part(PartID) ON UPDATE CASCADE ON DELETE RESTRICT,
  CHECK (Quantity > 0),
  CHECK (UnitPrice >= 0)
);

-- The completion API uses this flag to make inventory deduction idempotent.
SET @has_stock_deducted = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'PartUsage'
    AND column_name = 'StockDeducted'
);
SET @stock_sql = IF(
  @has_stock_deducted = 0,
  'ALTER TABLE PartUsage ADD COLUMN StockDeducted BOOLEAN NOT NULL DEFAULT FALSE',
  'SELECT 1'
);
PREPARE stock_stmt FROM @stock_sql;
EXECUTE stock_stmt;
DEALLOCATE PREPARE stock_stmt;


-- Prevent completion until the mechanic confirms actual parts consumed.
SET @has_actual_confirmed = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'ServiceRecord'
    AND column_name = 'ActualPartsConfirmed'
);
SET @actual_sql = IF(
  @has_actual_confirmed = 0,
  'ALTER TABLE ServiceRecord ADD COLUMN ActualPartsConfirmed BOOLEAN NOT NULL DEFAULT FALSE',
  'SELECT 1'
);
PREPARE actual_stmt FROM @actual_sql;
EXECUTE actual_stmt;
DEALLOCATE PREPARE actual_stmt;
