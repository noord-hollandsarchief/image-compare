SELECT p.filePath, p.pHash, e.*
FROM pHashes p
JOIN exifData e ON p.filePath = e.filePath
WHERE p.pHash IN (
    SELECT pHash
    FROM pHashes
    GROUP BY pHash
    HAVING COUNT(pHash) > 1
)
ORDER BY p.pHash;
