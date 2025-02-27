SELECT pHash, filePath
FROM pHashes
WHERE pHash IN (
    SELECT pHash
    FROM pHashes
    GROUP BY pHash
    HAVING COUNT(pHash) > 1
)
ORDER BY pHash;
