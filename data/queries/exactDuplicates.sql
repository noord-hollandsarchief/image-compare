SELECT md5Hash, aHash, filePath
FROM initialHashes
WHERE (md5Hash, aHash) IN (
    SELECT md5Hash, aHash
    FROM initialHashes
    GROUP BY md5Hash, aHash
    HAVING COUNT(*) > 1
)
ORDER BY md5Hash