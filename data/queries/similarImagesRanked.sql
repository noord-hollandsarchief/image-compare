WITH RankedFiles AS (
    SELECT 
        s.filePath, 
        s.hashType,
        s.hashValue, 
        e.XResolution, 
        e.YResolution, 
        u.numUniqueColors,
        DENSE_RANK() OVER (
            PARTITION BY s.hashValue 
            ORDER BY 
                CASE 
                    WHEN e.XResolution IS NOT NULL AND e.YResolution IS NOT NULL 
                    THEN e.XResolution * e.YResolution
                    ELSE 0
                END DESC,

                CASE 
                    WHEN u.numUniqueColors IS NOT NULL THEN u.numUniqueColors
                    ELSE 0
                END DESC
        ) AS rank
    FROM similarImages s
    JOIN exifdata e ON s.filePath = e.filePath
    LEFT JOIN uniqueColorData u ON s.filePath = u.filePath
    WHERE s.hashValue IN (
        SELECT hashValue
        FROM similarImages
        GROUP BY hashValue
        HAVING COUNT(hashValue) > 1
        )
    )
    SELECT * 
    FROM RankedFiles
    ORDER BY hashValue ASC, rank ASC;