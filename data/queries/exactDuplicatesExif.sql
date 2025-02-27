SELECT h.md5Hash, h.aHash, h.filePath, e.*
FROM initialHashes h
JOIN exifData e ON h.filePath = e.filePath
WHERE (h.md5Hash, h.aHash) IN (
    SELECT md5Hash, aHash
    FROM initialHashes
    GROUP BY md5Hash, aHash
    HAVING COUNT(*) > 1
)
ORDER BY h.md5Hash;
