
USE VehicleServiceDB;

-- 1. Check current inventory and recorded part usage
SELECT
    p.PartID,
    p.PartName,
    p.StockQuantity AS CurrentStock,
    COALESCE(SUM(pu.QuantityUsed), 0) AS RecordedUsage
FROM Part p
LEFT JOIN PartUsage pu ON pu.PartID = p.PartID
GROUP BY p.PartID, p.PartName, p.StockQuantity
ORDER BY p.PartID;

-- 2. Compare invoice totals with labour + parts
SELECT
    sr.ServiceID,
    sr.Status AS ServiceStatus,
    COALESCE(l.LaborTotal, 0) AS LaborTotal,
    COALESCE(p.PartsTotal, 0) AS PartsTotal,
    i.TotalAmount AS StoredInvoiceTotal,
    COALESCE(l.LaborTotal, 0)
      + COALESCE(p.PartsTotal, 0) AS CalculatedTotal
FROM ServiceRecord sr
LEFT JOIN Invoice i ON i.ServiceID = sr.ServiceID
LEFT JOIN (
    SELECT ServiceID, SUM(LaborCost) AS LaborTotal
    FROM ServiceTask
    GROUP BY ServiceID
) l ON l.ServiceID = sr.ServiceID
LEFT JOIN (
    SELECT ServiceID,
           SUM(QuantityUsed * UnitPrice) AS PartsTotal
    FROM PartUsage
    GROUP BY ServiceID
) p ON p.ServiceID = sr.ServiceID
ORDER BY sr.ServiceID;

-- 3. Check existing triggers
SHOW TRIGGERS FROM VehicleServiceDB;

-- 4. Check the current PartUsage schema
SHOW CREATE TABLE PartUsage;


ALTER TABLE PartUsage
ADD COLUMN StockDeducted BOOLEAN NOT NULL DEFAULT FALSE;
SHOW COLUMNS FROM PartUsage;




START TRANSACTION;

-- Lock inventory records that will be affected.
SELECT DISTINCT p.PartID
FROM Part p
JOIN PartUsage pu ON pu.PartID = p.PartID
WHERE pu.StockDeducted = FALSE
FOR UPDATE;

-- Abort this transaction manually if any part lacks stock.
SELECT
    p.PartID,
    p.PartName,
    p.StockQuantity,
    SUM(pu.QuantityUsed) AS RequiredQuantity
FROM Part p
JOIN PartUsage pu ON pu.PartID = p.PartID
WHERE pu.StockDeducted = FALSE
GROUP BY p.PartID, p.PartName, p.StockQuantity
HAVING p.StockQuantity < SUM(pu.QuantityUsed);

-- If the previous query returns no rows, continue:
UPDATE Part p
JOIN (
    SELECT PartID, SUM(QuantityUsed) AS Qty
    FROM PartUsage
    WHERE StockDeducted = FALSE
    GROUP BY PartID
) usage_totals ON usage_totals.PartID = p.PartID
SET p.StockQuantity = p.StockQuantity - usage_totals.Qty
WHERE p.StockQuantity >= usage_totals.Qty;

-- Mark the usage rows as applied.
UPDATE PartUsage
SET StockDeducted = TRUE
WHERE StockDeducted = FALSE;

COMMIT;

SELECT PartID, PartName, StockQuantity
FROM Part
ORDER BY PartID;

SELECT
    PartName,
    StockQuantity,
    ReorderLevel,
    CASE
        WHEN StockQuantity <= ReorderLevel THEN 'REORDER'
        ELSE 'OK'
    END AS StockStatus
FROM Part
ORDER BY PartID;

