SELECT md5Hash, aHash, filePath
FROM initialHashes
WHERE md5Hash IN (
    SELECT md5Hash
    FROM initialHashes
    GROUP BY md5Hash
    HAVING COUNT(*) > 1
    )
AND aHash NOT IN (
    SELECT aHash
    FROM initialHashes
    GROUP BY aHash
    HAVING COUNT(*) > 1
)
ORDER BY md5Hash, aHash;