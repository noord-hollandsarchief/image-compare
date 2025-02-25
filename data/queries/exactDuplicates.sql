SELECT md5Hash, aHash, filePath
  FROM initialHashes
  WHERE aHash IN (
  SELECT aHash
  FROM initialHashes
  GROUP BY aHash
  HAVING COUNT(*) > 1
  )
  AND md5Hash NOT IN (
  SELECT md5Hash
  FROM initialHashes
  GROUP BY md5Hash
  HAVING COUNT(*) > 1
  )
  ORDER BY aHash, md5Hash;

