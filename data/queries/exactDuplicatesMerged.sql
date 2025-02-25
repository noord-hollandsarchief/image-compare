SELECT 'md5Hash' AS hashType, md5Hash AS hashValue, GROUP_CONCAT(filePath) AS filePaths
FROM initialHashes
WHERE (md5Hash, aHash) IN (
SELECT md5Hash, aHash
FROM initialHashes
GROUP BY md5Hash, aHash
HAVING COUNT(*) > 1
)
GROUP BY md5Hash

UNION ALL

SELECT 'sha256Hash' AS hashType, sha256Hash AS hashValue, GROUP_CONCAT(filePath) AS filePaths
FROM sha256Rows
WHERE sha256Hash IN (
SELECT sha256Hash
FROM sha256Rows
GROUP BY sha256Hash
HAVING COUNT(*) > 1
)
GROUP BY sha256Hash
ORDER BY hashType, hashValue