SELECT p.pHash, p.filePath, i.md5Hash
FROM pHashes p
JOIN initialHashes i ON p.filePath = i.filePath
WHERE p.pHash IN (
  SELECT pHash
  FROM pHashes
  GROUP BY pHash
  HAVING COUNT(*) > 1
)
ORDER BY i.md5Hash;
