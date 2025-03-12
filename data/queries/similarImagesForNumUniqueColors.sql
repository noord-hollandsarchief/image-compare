WITH TotalPixelCounts AS (
SELECT
    s.hashValue,
    e.filePath,
    e.XResolution,
    e.YResolution,
    e.XResolution * e.YResolution AS PixelCount
FROM
    exifData e
JOIN similarImages s ON e.filePath = s.filePath
),
MaxPixelCounts AS (
    SELECT
        hashValue,
        MAX(PixelCount) AS MaxPixelCount
    FROM
        TotalPixelCounts
    GROUP BY
        hashValue
),
GroupsWithEqualPixelCounts AS (
    SELECT
        t.hashValue
    FROM
        TotalPixelCounts t
    JOIN MaxPixelCounts m ON t.hashValue = m.hashValue
    WHERE
        t.PixelCount = m.MaxPixelCount
    GROUP BY
        t.hashValue
    HAVING COUNT(*) > 1
)
SELECT
    t.hashValue,
    t.filePath,
    t.XResolution,
    t.YResolution,
    t.PixelCount
FROM
    TotalPixelCounts t
JOIN GroupsWithEqualPixelCounts g ON t.hashValue = g.hashValue
ORDER BY
    t.hashValue,
    t.PixelCount DESC;