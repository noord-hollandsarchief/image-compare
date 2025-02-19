import os
import subprocess
import json
import hashlib
import tempfile
import sqlite3
import re

import numpy as np
import pandas as pd
from PIL import Image
from PIL.ExifTags import TAGS
import imagehash



def getAllImageFilePaths(directory):
    """
    Recursively retrieves all image file paths from the specified directory.

    This function walks through the directory tree starting from the given 
    file path, collects all file paths, and filters them to include only 
    image files based on their extensions. It assumes that image files have 
    three-character extensions (e.g., jpg, png).

    Parameters:
    directory (str): The root directory path to start the search.

    Returns:
    list: File paths for all image files found in the directory tree.
    """
    allFilePaths = []
    
    # Collecting all the file paths in the specified directory (archive) 
    for root, _, files in os.walk(directory):
        for file in files:
            allFilePaths.append(os.path.join(root, file))
    
    # Assume the file extensions of images are of length 3 (e.g., jpg, png).
    imageExtensions = list(set([p.split('.')[-1] 
                                for p in allFilePaths
                                if len(p.split('.')[-1]) == 3]))    
    
    # Filter the file paths to include only image files.
    allImageFilePaths = [p for p in allFilePaths 
                         if p.split('.')[-1] in imageExtensions] 

    return allImageFilePaths


def getExifData(allImageFilePaths, exifDataPath, exifToolPath):
    """
    This function extracts specified Exif metadata from image files using ExifTool.
    The output is captured in JSON format, parsed into a pandas DataFrame, and saved to a CSV file.

    Parameters:
    allImageFilePaths (list): List of paths to all image files.
    exifDataPath (str): Path to save the resulting exifData.csv.
    exifToolPath (str): Path to the ExifTool executable.

    Returns:
    pandas.DataFrame: DataFrame containing the extracted Exif data.
    """

    # Specifying the fields to extract 
    relevantFields = ["FileSize", "XResolution", "YResolution"]
   
    # Initialize the exifData DataFrame
    exifDataColumns = ['filePath'] + relevantFields
    exifData = pd.DataFrame(columns=exifDataColumns)
 
    # Obtain the Exif metadata from each of the files in the list of paths.
    for filePath in allImageFilePaths:
        command = [exifToolPath, '-json', filePath]
        try:
            # Subprocess allows programs to run through the command-line-interface and capture its output
            # Has to be optimized so only the relevant fields are extracted by the exifTool itself.
            result = subprocess.run(command, capture_output=True, text=True)
           
            # Parse the JSON output.
            json_result = json.loads(result.stdout)[0]
            #print(json_result)
            # Adding the relevant fields to the exifData DataFrame.
            # exifData = pd.concat([exifData, pd.DataFrame({k: [v]
            #                       for k, v in json_result.items() if k in relevantFields})])
            exifData = pd.concat([exifData, pd.DataFrame({k: [v] for k, v in json_result.items() if k in relevantFields})])

        # When the process fails we print an error messagege               
        except Exception as e:
            print(f"Error processing {filePath}: {e}")

    exifData['filePath'] = allImageFilePaths

    print(exifData)
    # Saving the exifData DataFrame to a CSV file.
    exifData.to_csv(exifDataPath, index=False)

    return exifData


def getConversionNames(maisFlexisRecords):
    """
    This function reformats the associated record data extracted from MaisFlexis.  
    It strips the file of the included html tags and transforms the fields.
    'CODE', 'NUMMER' and 'CODE_1' are concatenated together to create a common field between 
    the filepaths of the analyzed images and the maisFlexisRecords to allow coupling through a join.

    Parameters:
    maisFlexisRecords (str): The path to the file containing the records from MaisFlexis

    Returns:
    pandas DataFrame: The processed MaisFlexis records. 
    """
    
    # Reading the raw records data file into a pandas DataFrame
    recordsDF = pd.read_excel(maisFlexisRecords)
    
    # Stripping the html tags and transforming the fields.
    recordsDF[['AANVRAAGNUMMER', 'FOTONUMMER', 'NUMMERING_CONVERSIE']] =\
    recordsDF[['AANVRAAGNUMMER', 'FOTONUMMER', 'NUMMERING_CONVERSIE']].apply(lambda x: x.str.split('<b>')
                                                                           if '<b>' in x else x.str.split('<br>'))
    recordsDF[['AANVRAAGNUMMER', 'FOTONUMMER', 'NUMMERING_CONVERSIE']] = \
    recordsDF[['AANVRAAGNUMMER', 'FOTONUMMER', 'NUMMERING_CONVERSIE']].map(lambda x: ','.join(x) if isinstance(x, list) else x)
    
    # 'CODE', 'NUMMER' and 'CODE_1' are concatenated together
    # Dropping the empty values in 'NUMMER' beforehand to ensure correct concatenation.
    recordsDF = recordsDF.dropna(subset=['NUMMER'])
    recordsDF['NUMMER'] = recordsDF['NUMMER'].astype(int)
    
    recordsDF['codeAndNumber'] =\
    (recordsDF['CODE'].astype(str) + "\\" + recordsDF['NUMMER'].astype(str) + 
    np.where(recordsDF['CODE_1'].fillna('') != '', recordsDF['CODE_1'].astype(str), ''))

    return recordsDF

def getDescriptionData(maisFlexisDescriptions):
    """
    This function reformats the associated record data extracted from MaisFlexis.  
    It strips the file of the included html tags and transforms the fields.
    'CODE', 'NUMMER' and 'CODE_1' are concatenated together to create a common field between 
    the filepaths of the analyzed images and the maisFlexisRecords to allow coupling through a join.

    Parameters:
    maisFlexisDescriptions (str): The path to the file containing the MaisFlexis descriptions

    Returns:
    pandas DataFrame: The processed MaisFlexis descriptions. 
    """
    descriptionsDF = pd.read_csv(maisFlexisDescriptions, encoding='latin1')

    patterns = ['<ZR><BCURS>', '<BCURS>', '<ECURS>', '<ZR>']
    for pattern in patterns:
        descriptionsDF['BESCHRIJVING'] = descriptionsDF['BESCHRIJVING'].str.replace(pattern, '', regex=True)


    def toIntIfNumber(x):
        try:
            if re.match(r'^\d+\.?\d*$', str(x)):
                return int(float(x))
            else:
                return None
        except ValueError:
            return None

    # Apply the conversion
    descriptionsDF['NUMMER'] = descriptionsDF['NUMMER'].apply(lambda x: toIntIfNumber(x) if pd.notna(x) else None)
    descriptionsDF['CODE'] = descriptionsDF['CODE'].apply(lambda x: toIntIfNumber(x) if pd.notna(x) else None)
    descriptionsDF['CODE_1'] = descriptionsDF['CODE_1'].apply(lambda x: toIntIfNumber(x) if pd.notna(x) else None)
    
    # Create 'codeAndNumber' with conditional concatenation logic
    descriptionsDF['codeAndNumber'] = descriptionsDF.apply(lambda row: 
    (str(row['CODE']) if pd.notna(row['CODE']) else '') + "\\" + 
    (str(row['NUMMER']) if pd.notna(row['NUMMER']) else '') + 
    (str(row['CODE_1']) if pd.notna(row['CODE_1']) else ''), axis=1)

def getImageHash(filePath, algorithm='average_hash'):
    """
    This function allows calculation of imagehashes.
    These are used to identify visually similar images.
    The supported hash algorithms are 'average_hash' and 'phash'.
    
    Parameters:
    filePaths (list): List of paths to the files to be hashed.
    exifToolPath (str): Path to the ExifTool executable.
    algorithm (str): The name of the algorithm to be used (default='md5').

    Returns:
    list: A list of image hashes.
    """
    
    Image.MAX_IMAGE_PIXELS = None 
    # Dictionary of possible filehash functions.
    hashFuncs = {'average_hash': imagehash.average_hash,
                  'phash': imagehash.phash}
    
    # Error message when an unsupported hash function is selected.
    if algorithm not in hashFuncs:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    # Calculating the hash function passed as algorithm argument.
    try:
        img = Image.open(filePath)
        imageHash = str(hashFuncs.get(algorithm)(img))
        print(f'{algorithm} is: {imageHash}')
        return imageHash
    # If it fails, an error message is printed.
    except Exception as e:
        return(f"Error generating image hash for {filePath}: {e}")


def getFileHash(filePaths, exifToolPath, algorithm='md5'):
    """
    This function allows calculation of file hashes for exact duplicate checking.
    It removes the metadata from the file and saves the stripped file
    to a temporary path before doing so.
    The supported hash algorithms are 'md5' and 'sha256'.
    
    Parameters:
    file_paths (list): List of paths to the files to be hashed.
    exif_tool_path (str): Path to the ExifTool executable.
    algorithm (str): The name of the algorithm to be used (default='md5').

    Returns:
    list: A list of file hashes.
    """
    hashList = []
    # Dictionary of possible file hash functions.
    hashFuncs = {'md5': hashlib.md5,
                  'sha256': hashlib.sha256}
    
    # Error message when an unsupported hash function is selected.
    if algorithm not in hashFuncs:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    # Calculate the hashes for each of the files in the list of paths.
    for filePath in filePaths:
        try:
            # Create a temporary file
            tempFile = tempfile.NamedTemporaryFile(delete=False)
            tempPath = tempFile.name
            tempFile.close()

            # Ensure the tempPath is deleted if it exists
            if os.path.exists(tempPath):
                os.remove(tempPath)

            # The command to be used to run the locally installed ExifTool.
            command = [exifToolPath, '-all=', '-o', tempPath, filePath]
            # Subprocess allows programs to run through the command-line-interface and capture its output
            process = subprocess.Popen(args=command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, error = process.communicate()

            # When the process fails, an exception is raised.
            if process.returncode != 0:
                raise Exception(f"ExifTool Error: {error.decode().strip()}")

            # From the dictionary of possible hash functions, the name of the hash function of the specified algorithm 
            # argument is obtained and used to calculate the hash of that specific function.
            with open(tempPath, "rb") as f:
                file_hash = hashFuncs.get(algorithm)(f.read()).hexdigest()
                hashList.append(file_hash)
                print(f"{algorithm} hash is {file_hash}")

        # When the process fails we execute the following steps:
        except Exception as e:
            # Show the error message
            errorMessage = f"Error processing {filePath}: {e}"
            print(errorMessage)
            # Add to hash_list to match the length of the pandas DataFrame.
            hashList.append(errorMessage)
            continue
        
        # To ensure the tempPath is always removed before the next iteration in the loop
        # we put it in the finally block
        finally:
            if os.path.exists(tempPath):
                os.remove(tempPath)

    return hashList




def getInitialHashData(allImageFilePaths, hashPath, exifToolPath):
    """
    This function calculates the initial hashes (md5Hash, aHash) and assigns these
    together with the image filepaths to the hashData dataframe. 
    This dataframe is then saved to CSV in the specified hashPath.
    
    Parameters:
    allImageFilePaths (list): List of paths to the files to be hashed.
    hashPath (str): Path to save the resulting exifData.csv.
    exifToolPath (str): Path to the ExifTool executable.
    
    Returns:
    pandas DataFrame: The initial hash data. 
    """
    # Initializing the intial hashes pandas DataFrame.
    hashData = pd.DataFrame(index=range(len(allImageFilePaths)))
    
    # Assigning the values to the pandas DataFrame as lists.
    hashData['md5Hash'] = getFileHash(allImageFilePaths, exifToolPath, algorithm='md5')
    hashData['aHash'] = [getImageHash(p, algorithm='average_hash') for p in allImageFilePaths]
    hashData['filePath'] = allImageFilePaths

    # Saving the pandas DataFrame as CSV file.
    hashData.to_csv(hashPath, index=False)
    return hashData


def makeTables(tablesPath):
    """
    This function creates all the necessary SQL tables.

    Parameters:
    
    tablesPath (str): Specifies the path of the SQLite database file.

    Returns:
    None
    """
    # Creating the database file in the tablesPath and establishing a connection.
    connection = sqlite3.connect(database=tablesPath)
    cursor = connection.cursor()

    connection.executescript('PRAGMA foreign_keys = ON')

    # Creating the initial data tables.    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS initialHashes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        md5Hash TEXT NOT NULL UNIQUE,
        sha256Hash TEXT,
        aHash TEXT,
        filePath TEXT NOT NULL
        )
    ''')                 

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exifData (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        FileSize TEXT,
        XResolution TEXT,
        YResolution TEXT
        )
    ''')                 

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversionNames (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        CODE INTEGER,
        NUMMER INTEGER,
        AANVRAAGNUMMER TEXT,
        FOTONUMMER TEXT,
        NUMMERING_CONVERSIE TEXT,
        md5Hash TEXT, 
        FOREIGN KEY(md5Hash) REFERENCES initialHashes(md5Hash)
        )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS descriptionData (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        CODE TEXT,
        AET_ID TEXT,
        NUMMER TEXT,
        CODE_1 INTEGER,
        BEGINJAAR INTEGER,
        EINDJAAR INTEGER,
        BESCHRIJVING TEXT,
        DATERING TEXT,
        NOTABENE TEXT,
        md5Hash TEXT, 
        FOREIGN KEY(md5Hash) REFERENCES initialHashes(md5Hash)
        )
    ''')

    connection.commit()
    connection.close() 


def getUniqueColors(imageFilePaths):
    """
    This function calculates the number of unique colors 

    Parameters:
    imageFilePaths (list): Paths to image files.

    Returns:
    A list with the number of unique colors calculated using the 
    list of image filepaths. 
    """
    
    # This has to be further specified.
    # Find max value in database 
    Image.MAX_IMAGE_PIXELS = None

    numUniqueColorsList = [] 

    # Calculate the number of unique colors for each of the files in the list of paths.
    for filePath in imageFilePaths:
        try:
            image = Image.open(filePath)
            image = image.convert('RGB')
            colors = image.getcolors(maxcolors=256*256*256)
            numUniqueColors = len(colors)
            numUniqueColorsList.append(numUniqueColors)
        # When the process fails we execute the following steps:
        except Exception as e:
            message = f"Error processing {filePath}: {e}"
            # Add to numUniqueColorsList to match the length of the pandas DataFrame.
            numUniqueColorsList.append(message)
            print(message)

    return numUniqueColorsList


def getUniqueColorsTable(tablesPath, processedDataPath):
    """
    This function extracts image file paths with the highest resolution for each hash value,
    calls the getUniqueColors function to calculate the number of unique colors for each image, and stores the results in a SQLite table
    and a CSV file.

    Parameters:
    tablesPath (str): Specifies the path of the SQLite database file.
    processedDataPath (str): The path where the processed data is stored.
    
    Returns:
    None
    """
    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    
    # From the similar images, the highest resolutions are extracted.
    similarImagesSameResolution = """
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
    """ 
    
    uniqueColorsDF =\
    pd.read_sql(similarImagesSameResolution, con=connection)

    # These paths are used to calculate the number of unique colors.
    uniqueColorsDF['numUniqueColors'] = getUniqueColors(uniqueColorsDF['filePath'].tolist())
    uniqueColorsDF.to_sql('uniqueColorData', con=connection,
                    if_exists='replace', index=False)
    
    # Saving the uniqueColorsDF to CSV.
    uniqueColorsDF.to_csv(os.path.join(processedDataPath, 'uniqueColors.csv'), index=False)


def getInitialImageData(allImageFilePaths, exifToolPath, rawDataPath, processedDataPath):
    """
    This function gathers initial hashes (md5Hash, aHash) and assigns these
    together with the image filepaths to the hashData dataframe. 
    This dataframe is then saved to CSV in the specified hashPath.
    
    Parameters:
    allImageFilePaths (list): List of paths to the files to be hashed.
    exifToolPath (str): Path to the ExifTool executable.
    rawDataPath (str): The path where the raw data is stored.
    processedDataPath (str): The path where the processed data is stored.
    
    Returns:
    A pandas DataFrame with the initial hash data. 
    A pandas DataFrame with the processed MaisFlexis records. 
    A pandas DataFrame with the extracted Exif data.
    """

    # Defining the paths to the generated data files.
    exifDataPath = os.path.join(processedDataPath, 'exifData.csv')
    maisFlexisRecords = os.path.join(rawDataPath, 'Data_beeldbank.xlsx')
    maisFlexisDescriptions = os.path.join(rawDataPath, 'EB_DB_ZieOOK.csv')
    hashPath = os.path.join(processedDataPath, 'imagesHash.csv')
    
    # The parsed maisFlexisRecords.
    namesData = getConversionNames(maisFlexisRecords=maisFlexisRecords)
    
    # The description data.
    descriptionData = getDescriptionData(maisFlexisDescriptions=maisFlexisDescriptions)
    # The initial hash data (filePath, aHash, MD5)
    initialHashData = getInitialHashData(allImageFilePaths=allImageFilePaths,
                                         hashPath=hashPath, 
                                         exifToolPath=exifToolPath)
    
    
    # The initial exifData (filePath, FileSize, Resolution)
    exifData = getExifData(allImageFilePaths=allImageFilePaths,
                           exifDataPath=exifDataPath,
                           exifToolPath=exifToolPath)
    
    return namesData,  descriptionData, initialHashData, exifData


def fillTablesInitialData(exifData, namesData,  descriptionData, initialHashData, tablesPath):
    """
    This function fills the tables created by the makeTables function 
    and fills them with the three pandas DataFrames returned by getInitialImageData.

    Parameters:
    exifData (pandas DataFrame): The extracted Exif data
    namesData (pandas DataFrame): The processed MaisFlexis records.
    initialHashData (pandas DataFrame): The initial hash data. 
    tablesPath (str): Specifies the path of the SQLite database file.
    
    Returns:
    None
    """
    try:
        # Connecting to the database in tablesPath.
        connection = sqlite3.connect(database=tablesPath)
        # Inserting the data from the DataFrame into the SQLite tables.
        exifData.to_sql('exifData', con=connection,
                       if_exists='replace', index=False)
        namesData.to_sql('conversionNames', con=connection, 
                       if_exists='replace', index=False),
        #descriptionData.to_sql('descriptionData', con=connection,
        #                       if_exists='replace', index=False)        
        initialHashData.to_sql('initialHashes', con=connection,
                             if_exists='replace', index=False)
        
    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)
    # Closing the connection with the database when done.
    finally:
        if connection:
            connection.close()
            print("The SQLite connection is closed")


def getExactDuplicates(tablesPath, exifToolPath, processedDataPath):
  """
  This function identifies and processes duplicate images based on their hash values,
  calculates additional hashes for further verification, and stores the results in a SQLite database
  and a CSV file.

  Parameters:
  tablesPath (str): Specifies the path of the SQLite database file.
  exifToolPath (str): Path to the ExifTool executable.
  processedDataPath (str): The path where the processed data is stored.
  
  Returns:
  None
  """
  # Connecting to the database in tablesPath.
  connection = sqlite3.connect(database=tablesPath)
  cursor = connection.cursor()

  # Performing queries to find possible duplicates
  #images where both md5Hash and aHash are duplicated (exact duplicates).
  queryMD5andImageHash = """
  SELECT md5Hash, aHash, filePath
  FROM initialHashes

  WHERE (md5Hash, aHash) IN (
  SELECT md5Hash, aHash
  FROM initialHashes
  GROUP BY md5Hash, aHash
  HAVING COUNT(*) > 1
  )
  ORDER BY md5Hash
  """

  # Images were md5Hash is duplicated but not aHash (md5 collision).
  queryMD5notImageHash = """
  SELECT md5Hash, aHash, filePath
  FROM initialHashes
  WHERE md5Hash IN (
  SELECT md5Hash
  FROM initialHashes
  GROUP BY md5Hash
  HAVING COUNT(*) > 1
  )
  AND aHash NOT IN (
  SELECT aHash
  FROM initialHashes
  GROUP BY aHash
  HAVING COUNT(*) > 1
  )
  ORDER BY md5Hash, aHash;
  """

  # Images were md5Hash is not duplicated but aHash is (aHash collision or 
  # different metadata).
  queryNotMD5AndImageHash = """
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
  """

  # Executing the above queries and loading the results into DataFrames.
  aHashAndMD5 = pd.read_sql(queryMD5andImageHash,
                            con=connection)
  noAHashAndMD5 = pd.read_sql(queryMD5notImageHash,
                              con=connection)
  aHashAndNotMD5 = pd.read_sql(queryNotMD5AndImageHash,
                               con=connection)
  
  # Calculating the additional hashes.
  noAHashAndMD5['sha256Hash'] = getFileHash(noAHashAndMD5['filePath'].tolist(),
                                            exifToolPath, 
                                            algorithm='sha256')
  
  aHashAndNotMD5['pHash'] = [getImageHash(p, algorithm='phash') 
                             for p in aHashAndNotMD5['filePath'].tolist()]
  
  # Combining results into a single DataFrame.
  finalHashesDF = pd.concat([aHashAndMD5,
                             noAHashAndMD5,  
                             aHashAndNotMD5])

  # Extracting the rows with calculated hashes.
  sha256Rows =\
  finalHashesDF[['filePath', 'sha256Hash']].dropna()

  pHashRows =\
  finalHashesDF[['filePath', 'pHash']].dropna()

  # Storing the results in SQLite tables.
  sha256Rows.to_sql(name='sha256Rows', 
                  con=connection, 
                  if_exists='replace',
                  index=False)
  
  pHashRows.to_sql(name='pHashes',
                   con=connection,
                   if_exists='replace',
                   index=False)

  # Creating the table for exact duplicates.
  exactDuplicatesQuery = """
  CREATE TABLE IF NOT EXISTS exactDuplicates AS
  SELECT 'md5Hash' AS hashType, md5Hash AS hashValue, filePath
  FROM initialHashes
  WHERE (md5Hash, aHash) IN (
  SELECT md5Hash, aHash
  FROM initialHashes
  GROUP BY md5Hash, aHash
  HAVING COUNT(*) > 1
  )

  UNION ALL

  SELECT 'sha256Hash' AS hashType, sha256Hash AS hashValue, filePath
  FROM sha256Rows
  WHERE sha256Hash IN (
  SELECT sha256Hash
  FROM sha256Rows
  GROUP BY sha256Hash
  HAVING COUNT(*) > 1
  )
  ORDER BY hashType, hashValue, filePath;
  """
  
  cursor.execute(exactDuplicatesQuery)
  connection.commit()

  # Saving the final DataFrame to CSV.
  exactDuplicatesDF = pd.read_sql("SELECT * FROM exactDuplicates", con=connection)
  exactDuplicatesDF = exactDuplicatesDF.to_csv(os.path.join(processedDataPath, 'exactDuplicates.csv'), index=False)

  connection.close()


def mapDuplicatesToConversionNames(tablesPath, processedDataPath):
    """
    This function categorizes the exact duplicates as 'gekoppeld' or 'ongekoppeld', 
    extracts the code and number from the filePath of 'gekoppeld', combines it into a new
    column and maps it to the MaisFlexis records by joining on this column. This information is not obtainable 
    from the 'ongekoppeld' filepaths, so here they are instead mapped using the common hashvalue
    between 'ongekoppeld' and 'gekoppeld'. 

    Parameters:
    tablesPath (str): Specifies the path of the SQLite database file.
    exifToolPath (str): Path to the ExifTool executable.
    processedDataPath (str): The path where the processed data is stored.

    Returns:
    pandas.DataFrame: DataFrame containing the mapped duplicates and their conversion names.
    """
    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    cursor = connection.cursor()

    # Reading the exactDuplicates table as a pandas DataFrame.
    exactDuplicates = pd.read_sql("SELECT * FROM exactDuplicates", con=connection)
    
    # Adding a new column 'koppelingStatus' and setting its default value to 'gekoppeld'.
    exactDuplicates['koppelingStatus'] = 'gekoppeld'

    # Update 'koppelingStatus' to 'ongekoppeld' for rows where 'filePath' contains '_OGK' or '_OGKB'.
    exactDuplicates.loc[exactDuplicates['filePath'].str.contains('_OGK|_OGKB'), 'koppelingStatus'] = 'ongekoppeld'

    # Create a new column 'codeAndNumber' for rows where 'koppelingStatus' is 'gekoppeld'
    exactDuplicates.loc[exactDuplicates['koppelingStatus'] == 'gekoppeld', 'codeAndNumber'] = exactDuplicates['filePath'].apply(
    lambda x: os.path.join(*os.path.dirname(x).split(os.sep)[1:3]))
    exactDuplicates.to_sql(name='exactDuplicates', 
                  con=connection, 
                  if_exists='replace',
                  index=False)
    
    # Query to join the duplicate files with 'gekoppeld' as 'koppelingStatus'
    # with the MaisFlexis records on codeEnNummer.
    mapDuplicatesToConversionGekoppeld = """
    CREATE TABLE IF NOT EXISTS exactDuplicatesConversionGekoppeld AS 
    SELECT c.ID, c.AANVRAAGNUMMER, c.NUMMERING_CONVERSIE, d.filePath, d.hashValue AS fileHash, d.hashType, d.codeAndNumber, d.koppelingStatus  
    FROM exactDuplicates d  
    JOIN conversionNames c ON d.codeAndNumber = c.codeAndNumber
    WHERE d.koppelingStatus = 'gekoppeld'
    ORDER BY c.ID;
    """

    # Executing the query to create the table.
    cursor.execute(mapDuplicatesToConversionGekoppeld)

    # Query to join the duplicate files with 'ongekoppeld' as 'koppelingStatus'
    # with the 'gekoppeld' files in the exactDuplicatesConversionGekoppeld table created above on their fileHash
    mapDuplicatesToConversionOngekoppeld = """
    CREATE TABLE IF NOT EXISTS exactDuplicatesConversionOngekoppeld AS
    SELECT g.ID, g.AANVRAAGNUMMER, g.NUMMERING_CONVERSIE, d.filePath, g.fileHash, g.hashType, d.codeAndNumber, d.koppelingStatus
    FROM exactDuplicates d
    JOIN exactDuplicatesConversionGekoppeld g ON g.fileHash= d.hashValue
    WHERE d.koppelingStatus = 'ongekoppeld'
    ORDER BY g.ID;
    """

    # Executing the query to create the table.
    cursor.execute(mapDuplicatesToConversionOngekoppeld)

    # Read the tables into DataFrames.
    duplicatenConversieGekoppeld = pd.read_sql("SELECT * FROM exactDuplicatesConversionGekoppeld", con=connection)
    duplicatenConversieOngekoppeld = pd.read_sql("SELECT * FROM exactDuplicatesConversionOngekoppeld", con=connection)

    # Concatenating the DataFrames.
    duplicatesMappedToConversionDF =\
    pd.concat([duplicatenConversieGekoppeld, duplicatenConversieOngekoppeld])

    duplicatesMappedToConversionDF.to_sql('duplicatesMappedToConversion', con=connection,
                               if_exists='replace', index=False)

    if not duplicatesMappedToConversionDF.empty:
        # Split the 'codeAndNumber' column into two columns 'code' and 'number'
        splitColumns = duplicatesMappedToConversionDF['codeAndNumber'].str.split('\\', expand=True)

        # Ensure there are exactly two columns by filling any missing values
        splitColumns = splitColumns.fillna('')

        # Assign the split columns to 'code' and 'number'
        duplicatesMappedToConversionDF[['code', 'number']] = splitColumns

    duplicatesMappedToConversionDF.to_csv(os.path.join(processedDataPath, 'duplicatesMappedToConversion.csv'), index=False)

    # Closing the database connection.
    connection.close()

    return duplicatesMappedToConversionDF


def getSimilarImages(tablesPath, processedDataPath):
    """
    This function creates the similarImages SQL table based 
    on matching pHashes and aHashes between images, saves it to a
    pandas DataFrame and CSV file.

    Parameters:
    tablesPath (str): Specifies the path of the SQLite database file.
    processedDataPath (str): The path where the processed data is stored.

    Returns:
    pandas.DataFrame: DataFrame containing the similar images 
    """
    
    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    cursor = connection.cursor()

    # Query to select images with duplicate aHash and images with duplicate pHash.
    querySimilarImages = """
    CREATE TABLE IF NOT EXISTS similarImages AS
    SELECT 'pHash' as hashType, pHash as hashValue, filePath
    FROM pHashes
    WHERE pHash IN (
        SELECT pHash
        FROM pHashes
        GROUP BY pHash
        HAVING COUNT(*) > 1
    )
        
    UNION ALL

    SELECT 'aHash' AS hashType, aHash AS hashValue, filePath
    FROM initialHashes
    WHERE aHash IN (
    SELECT aHash
    FROM initialHashes
    GROUP BY aHash
    HAVING COUNT(*) > 1
    )
    ORDER BY hashType, hashValue, filePath;
    """

    # Executing the query to create the table.
    cursor.execute(querySimilarImages)
    connection.commit()

    # Reading the table into a pandas DataFrame.
    pHashSimilarImagesDF = pd.read_sql("SELECT * FROM similarImages", connection)
    
    # Saving the tables as CSV.
    pHashSimilarImagesDF =\
    pHashSimilarImagesDF.to_csv(os.path.join(processedDataPath, 'similarImages.csv'), index=False)

    connection.close() 

    return pHashSimilarImagesDF


def getSimilarImagesRanked(tablesPath, processedDataPath):
    """
    This function creates a ranked table of similar images based on their pHash values,
    resolution, and number of unique colors. The results are stored in a SQLite database
    and a CSV file.

    Parameters:
    tablesPath (str): Specifies the path of the SQLite database file.
    processedDataPath (str): The path where the processed data is stored.

    Returns:
    pandas.DataFrame: DataFrame containing the ranked similar images and their EXIF data.
    """
    
    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    cursor = connection.cursor()

    # Query to create the similarImagesRanked table based on pHash,
    # resolution and number of unique colors.
    # The best image is the one with the highest resolution.
    # However sometimes there is no highest resolution, in that 
    # case the number of unique color is used to determine the best image.
    rankedImagesQuery = """
    CREATE TABLE IF NOT EXISTS similarImagesRanked AS
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
                        WHEN u.numUniqueColors IS NOT NULL THEN 1
                        ELSE 0
                    END DESC,
                    u.numUniqueColors DESC,
                    e.XResolution DESC,
                    e.YResolution DESC
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
    SELECT * FROM RankedFiles
    ORDER BY hashValue ASC, rank ASC;
    """
    # Executing the query to create the ranked table.
    cursor.execute(rankedImagesQuery)

    # Reading the ranked similar images into a pandas DataFrame.
    similarImagesRankedDF = pd.read_sql("SELECT * FROM similarImagesRanked", con=connection)
   
    # Saving the DataFrame to a CSV file.
    similarImagesRankedDF = similarImagesRankedDF.to_csv(os.path.join(processedDataPath, 'similarImagesRanked.csv'), index=False)
    
    # Committing the changes and closing the connection
    connection.commit()
    connection.close()
    return similarImagesRankedDF


def mapSimilarImagesToConversionNames(tablesPath, processedDataPath):
    """
    This function categorizes the similar images as 'gekoppeld' or 'ongekoppeld', 
    extracts the code and number from the filePath of 'gekoppeld', combines it into a new
    column and maps it to the MaisFlexis records by joining on this column. This information is not obtainable 
    from the 'ongekoppeld' filepaths, so here they are instead mapped using the common hashvalue
    between 'ongekoppeld' and 'gekoppeld'. 

    Parameters:
    tablesPath (str): Specifies the path of the SQLite database file..
    exifToolPath (str): Path to the ExifTool executable.
    processedDataPath (str): The path where the processed data is stored.

    Returns:
    pandas.DataFrame: DataFrame containing the similar images and their conversion names.
    """
    
    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    cursor = connection.cursor()

    # Reading the similarImagesRanked table as a pandas DataFrame.
    similarImagesRanked = pd.read_sql("SELECT * FROM similarImagesRanked", con=connection)

    # Adding a new column 'koppelingStatus' and setting its default value to 'gekoppeld'.
    similarImagesRanked['koppelingStatus'] = 'gekoppeld'

    # Update 'koppelingStatus' to 'ongekoppeld' for rows where 'filePath' contains '_OGK' or '_OGKB'.
    similarImagesRanked.loc[similarImagesRanked['filePath'].str.contains('_OGK|_OGKB'), 'koppelingStatus'] = 'ongekoppeld'

    # Create a new column 'codeAndNumber' for rows where 'koppelingStatus' is 'gekoppeld'
    similarImagesRanked.loc[similarImagesRanked['koppelingStatus'] == 'gekoppeld', 'codeAndNumber'] = similarImagesRanked['filePath'].apply(
    lambda x: os.path.join(*os.path.dirname(x).split(os.sep)[1:3]))
    
    # Updating the similarImagesRanked SQL table.
    similarImagesRanked.to_sql(name='similarImagesRanked', 
                  con=connection, 
                  if_exists='replace',
                  index=False)

    # Query to join the similar images with 'gekoppeld' as 'koppelingStatus'
    # with the MaisFlexis records on codeEnNummer.
    mapSimilarToConversionGekoppeld = """
    CREATE TABLE IF NOT EXISTS similarImagesConversionGekoppeld AS 
    SELECT c.ID, c.AANVRAAGNUMMER, c.NUMMERING_CONVERSIE, d.filePath, d.hashValue AS imageHash, d.hashType, d.XResolution, d.YResolution, d.numUniqueColors, d.rank, d.codeAndNumber, d.koppelingStatus  
    FROM similarImagesRanked d  
    JOIN conversionNames c ON d.codeAndNumber = c.codeAndNumber
    WHERE d.koppelingStatus = 'gekoppeld'
    AND c.ID IN (
        SELECT ID
        FROM conversionNames
        JOIN similarImagesRanked ON conversionNames.codeAndNumber = similarImagesRanked.codeAndNumber
        WHERE similarImagesRanked.koppelingStatus = 'gekoppeld'
        GROUP BY ID
        HAVING COUNT(*) > 1
    )
    ORDER BY imageHash ASC, d.rank ASC;
    """
    # Executing the query to create the table.
    cursor.execute(mapSimilarToConversionGekoppeld)

    # Query to join the similar images with 'ongekoppeld' as 'koppelingStatus'
    # with the 'gekoppeld' files in the similarImagesConversionGekoppeld table created above on their fileHash
    mapSimilarToConversionOngekoppeld = """
    CREATE TABLE IF NOT EXISTS similarImagesConversionOngekoppeld AS
    SELECT g.ID, g.AANVRAAGNUMMER, g.NUMMERING_CONVERSIE, d.filePath, d.hashValue AS imageHash, d.hashType, d.XResolution, d.YResolution, d.numUniqueColors, d.rank, d.codeAndNumber, d.koppelingStatus
    FROM similarImagesRanked d
    JOIN similarImagesConversionGekoppeld g ON g.imageHash = d.hashValue
    WHERE d.koppelingStatus = 'ongekoppeld'
    AND g.ID IN (
        SELECT ID
        FROM similarImagesConversionGekoppeld
        GROUP BY ID
        HAVING COUNT(*) > 1
    )
    ORDER BY imageHash ASC, d.rank ASC;
    """

    cursor.execute(mapSimilarToConversionOngekoppeld)

    # Reading the tables into DataFrames.
    similarConversieGekoppeld = pd.read_sql("SELECT * FROM similarImagesConversionGekoppeld", con=connection)
    similarConversionOngekoppeld = pd.read_sql("SELECT * FROM similarImagesConversionOngekoppeld", con=connection)

    # Concatenating the DataFrames.
    similarMappedToConversionDF =\
    pd.concat([similarConversieGekoppeld, similarConversionOngekoppeld])

    similarMappedToConversionDF.to_sql('similarImagesMappedToConversion', con=connection,
                               if_exists='replace', index=False)
    
    if not similarMappedToConversionDF.empty:
        # Split the 'codeAndNumber' column into two columns 'code' and 'number'
        splitColumns = similarMappedToConversionDF['codeAndNumber'].str.split('\\', expand=True)

        # Ensure there are exactly two columns by filling any missing values
        splitColumns = splitColumns.fillna('')

        # Assign the split columns to 'code' and 'number'
        similarMappedToConversionDF[['code', 'number']] = splitColumns

    similarMappedToConversionDF.to_csv(os.path.join(processedDataPath, 'similarMappedToConversion.csv'), index=False)

    # Closing the connection.
    connection.close()

    # Returning the concatenated DataFrame.
    return similarMappedToConversionDF
    
def mapImagesToDescription(tablesPath):
    pass