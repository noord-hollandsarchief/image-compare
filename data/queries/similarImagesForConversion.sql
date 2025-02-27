SELECT 'pHash' as hashType, pHash as hashValue, filePath
FROM pHashes
WHERE pHash IN (
    SELECT pHash
    FROM pHashes
    GROUP BY pHash
    HAVING COUNT(*) > 1
);