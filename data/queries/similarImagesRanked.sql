WITH RankedFiles AS (
    SELECT 
        p.filePath, 
        p.pHash, 
        e.XResolution, 
        e.YResolution, 
        u.numUniqueColors,
        DENSE_RANK() OVER (
            PARTITION BY p.pHash 
            ORDER BY 
                CASE 
                    WHEN u.numUniqueColors IS NOT NULL THEN 1
                    ELSE 0
                END DESC,
                u.numUniqueColors DESC,
                e.XResolution DESC,
                e.YResolution DESC
        ) AS rank
    FROM pHashes p
    JOIN exifdata e ON p.filePath = e.filePath
    LEFT JOIN uniqueColorData u ON p.filePath = u.filePath
    WHERE p.pHash IN (
        SELECT pHash
        FROM pHashes
        GROUP BY pHash
        HAVING COUNT(pHash) > 1
    )
)
SELECT * FROM RankedFiles
ORDER BY pHash ASC, rank ASC;
