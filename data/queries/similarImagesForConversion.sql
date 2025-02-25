-- SELECT c.ID, c.AANVRAAGNUMMER, c.NUMMERING_CONVERSIE, d.filePath, d.pHash AS imageHash, 'pHash' AS hashType, d.codeAndNumber, d.koppelingStatus  
-- FROM similarImagesRanked d  
-- JOIN conversionNames c ON d.codeAndNumber = c.codeAndNumber
-- WHERE d.koppelingStatus = 'gekoppeld'
-- AND c.ID IN (
--     SELECT ID
--     FROM conversionNames
--     JOIN similarImagesRanked ON conversionNames.codeAndNumber = similarImagesRanked.codeAndNumber
--     WHERE similarImagesRanked.koppelingStatus = 'gekoppeld'
--     GROUP BY ID
--     HAVING COUNT(*) > 1
-- )
-- ORDER BY c.ID;


-- SELECT c.ID, c.AANVRAAGNUMMER, c.NUMMERING_CONVERSIE, d.filePath, d.hashValue AS imageHash, d.hashType, d.XResolution, d.YResolution, d.numUniqueColors, d.rank, d.codeAndNumber, d.koppelingStatus  
--     FROM similarImagesRanked d  
--     JOIN conversionNames c ON d.codeAndNumber = c.codeAndNumber
--     WHERE d.koppelingStatus = 'gekoppeld'
--     AND c.ID IN (
--         SELECT ID
--         FROM conversionNames
--         JOIN similarImagesRanked ON conversionNames.codeAndNumber = similarImagesRanked.codeAndNumber
--         WHERE similarImagesRanked.koppelingStatus = 'gekoppeld'
--         GROUP BY ID
--         HAVING COUNT(*) > 1
--     )


SELECT g.ID, g.AANVRAAGNUMMER, g.NUMMERING_CONVERSIE, d.filePath, d.pHash AS imageHash, 'pHash' AS hashType, d.XResolution, d.YResolution, d.numUniqueColors, d.rank, d.codeAndNumber, d.koppelingStatus
    FROM similarImagesRanked d
    JOIN similarImagesConversionGekoppeld g ON g.imageHash = d.pHash
    WHERE d.koppelingStatus = 'ongekoppeld'
    AND g.ID IN (
        SELECT ID
        FROM similarImagesConversionGekoppeld
        GROUP BY ID
        HAVING COUNT(*) > 1
    )
    ORDER BY imageHash ASC, d.rank ASC;