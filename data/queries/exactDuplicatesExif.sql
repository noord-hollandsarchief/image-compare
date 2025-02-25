-- SELECT h.md5Hash, h.aHash, h.filePath, e.*
-- FROM initialHashes h
-- JOIN exifData e ON h.filePath = e.filePath
-- WHERE (h.md5Hash, h.aHash) IN (
--     SELECT md5Hash, aHash
--     FROM initialHashes
--     GROUP BY md5Hash, aHash
--     HAVING COUNT(*) > 1
-- )
-- ORDER BY h.md5Hash;


    WITH ResolutionRanks AS (
        SELECT
            s.hashValue,
            e.filePath,
            e.XResolution,
            e.YResolution,
            DENSE_RANK() OVER (PARTITION BY s.hashValue ORDER BY e.XResolution DESC, e.YResolution DESC) AS res_rank
        FROM  
            similarImages s
            JOIN exifData e ON s.filePath = e.filePath
    ),
    HighestResCounts AS (
        SELECT
            hashValue,
            res_rank,
            COUNT(*) AS res_count
        FROM
            ResolutionRanks
        WHERE 
            res_rank = 1
        GROUP BY 
            hashValue,
            res_rank
    )
    SELECT 
        rr.filePath
    FROM   
        ResolutionRanks rr
        JOIN HighestResCounts hrc ON rr.hashValue = hrc.hashValue
    WHERE
        rr.res_rank = 1
    ORDER BY
        rr.hashValue,
        rr.XResolution DESC,
        rr.YResolution DESC;