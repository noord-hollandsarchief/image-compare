-- SELECT c.ID, c.AANVRAAGNUMMER, c.NUMMERING_CONVERSIE, d.hashValue AS fileHash, d.hashType, d.codeAndNumber, d.filePath AS filePath, d.koppelingStatus  
-- FROM exactDuplicates d  
-- JOIN conversionNames c on d.codeAndNumber = c.codeAndNumber
-- WHERE d.koppelingStatus = 'gekoppeld'
-- ORDER BY c.ID;





SELECT g.ID, g.AANVRAAGNUMMER, g.NUMMERING_CONVERSIE, d.filePath, g.fileHash, g.hashType, d.codeAndNumber, d.koppelingStatus
FROM exactDuplicates d
JOIN exactDuplicatesConversionGekoppeld g ON g.fileHash= d.hashValue
WHERE d.koppelingStatus = 'ongekoppeld'
ORDER BY g.ID;
