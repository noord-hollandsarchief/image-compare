WITH ResolutionRanks AS (
    SELECT
        p.pHash,
        e.filePath,
        e.XResolution,
        e.YResolution,
        DENSE_RANK() OVER (PARTITION BY p.pHash ORDER BY e.XResolution DESC, e.YResolution DESC) AS res_rank
    FROM  
        pHashes p
        JOIN exifData e ON p.filePath = e.filePath
),
HighestResCounts AS (
    SELECT
        pHash,
        res_rank,
        COUNT(*) AS res_count
    FROM
        ResolutionRanks
    WHERE 
        res_rank = 1
    GROUP BY 
        pHash,
        res_rank
)
SELECT 
    rr.filePath,
    rr.XResolution,
    rr.YResolution,
    rr.pHash
FROM   
    ResolutionRanks rr
    JOIN HighestResCounts hrc ON rr.pHash = hrc.pHash
WHERE
    rr.res_rank = 1
ORDER BY
    rr.pHash,
    rr.XResolution DESC,
    rr.YResolution DESC;
