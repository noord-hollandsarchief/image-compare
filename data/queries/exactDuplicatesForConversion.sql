CREATE TABLE IF NOT EXISTS mappedDuplicates AS
SELECT 
    c.ID, c.AANVRAAGNUMMER, c.NUMMERING_CONVERSIE, 
    d.filePath, d.hashValue, d.hashType, r.TOEGANGSCODE, r.SCN_ID
FROM 
    conversionNames c
JOIN 
    exactDuplicates d ON 
        d.Bestandsnaam = r.Bestandsnaam
JOIN 
    rawDataRecords r ON r.ID = c.ID;