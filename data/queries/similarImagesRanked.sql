SELECT
    e.filePath,
    e.XResolution,
    e.YResolution
FROM
    exifData e
JOIN
    similarImages s ON e.filePath = s.filePath
WHERE
    (e.XResolution, e.YResolution) IN (
        SELECT
            MAX(e2.XResolution),
            MAX(e2.YResolution)
        FROM
            exifData e2
        JOIN
            similarImages s2 ON e2.filePath = s2.filePath
        WHERE
            s2.hashValue = s.hashValue
        GROUP BY
            s2.hashValue
    )
ORDER BY
    s.hashValue,    
    e.XResolution DESC,
    e.YResolution DESC;