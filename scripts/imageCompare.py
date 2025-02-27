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
import tqdm


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
    
    # Collecting all the file paths in the specified directory (root_directory)
    for root, _, files in os.walk(directory):
        for file in files:
            fullPath = os.path.join(root, file)
            allFilePaths.append(fullPath)
    
    # Assume the file extensions of images are of length 3 (e.g., jpg, png).
    imageExtensions = set(p.split('.')[-1] for p in allFilePaths
                          if len(p.split('.')[-1]) == 3)
    
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
    exifData = pd.DataFrame(columns=exifDataColumns, index=range(len(allImageFilePaths)))

    # Obtain the Exif metadata from each of the files in the list of paths.
    print()
    for i in tqdm.tqdm(range(len(allImageFilePaths)), desc='[START] Extracting exif metadata', bar_format="{desc}: {percentage:5.2f}% |{bar}| {n_fmt}/{total_fmt}", 
    ncols=80, 
    ascii=" ░▒▓█"):
        command = [exifToolPath, '-json', allImageFilePaths[i]]
        try:
            # Subprocess allows programs to run through the command-line-interface and capture its output
            # Has to be optimized so only the relevant fields are extracted by the exifTool itself.
            result = subprocess.run(command, capture_output=True, text=True)
           
            # Parse the JSON output.
            jsonResult = json.loads(result.stdout)[0]
            extractedData = {k: v for k, v in jsonResult.items() if k in relevantFields}
            extractedData['filePath'] = allImageFilePaths[i]
            for key, value in extractedData.items():
                exifData.loc[i, key] = value
        # When the process fails we print an error messagege               
        except Exception as e:
            print(f"Error processing {allImageFilePaths[i]}: {e}")

    print('[√] exif metadata extracted succesfully!')
    # Saving the exifData DataFrame to a CSV file.\
    exifData.to_csv(exifDataPath, index=False)
    
    return exifData


def getConversionNames(maisFlexisRecords, tablesPath):
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

    connection = sqlite3.connect(database=tablesPath)
    print()
    # Initialize tqdm progress bar for the transformation process
    tqdm.tqdm.pandas(desc=f'[START] Parsing MaisFlexis records', bar_format="{desc}: {percentage:5.2f}% |{bar}| {n_fmt}/{total_fmt}", 
    ncols=80, 
    ascii=" ░▒▓█")
    
    # Reading the raw records data file into a pandas DataFrame
    recordsDF = pd.read_excel(maisFlexisRecords, skiprows=1)
    
    # Stripping the HTML tags and transforming the fields
    def stripAndTransform(x):
        if isinstance(x, str):
            if '<b>' in x:
                return ','.join(x.split('<b>'))
            elif '<br>' in x:
                return ','.join(x.split('<br>'))
        return x
    
    # Apply the transformation with a single progress bar
    # Replacing applymap with progress_apply for better performance
    transformed = recordsDF[['AANVRAAGNUMMER', 'FOTONUMMER', 'NUMMERING_CONVERSIE']].progress_apply(stripAndTransform)
    
    # Assign the transformed columns back to the original DataFrame
    recordsDF[['AANVRAAGNUMMER', 'FOTONUMMER', 'NUMMERING_CONVERSIE']] = transformed
    
    # 'CODE', 'NUMMER' and 'CODE_1' are concatenated together
    # Dropping the empty values in 'NUMMER' beforehand to ensure correct concatenation.
    recordsDF = recordsDF.dropna(subset=['NUMMER'])
    recordsDF['NUMMER'] = recordsDF['NUMMER'].astype(int)
    
    recordsDF['codeAndNumber'] = (
        recordsDF['CODE'].astype(str) + "\\" + 
        recordsDF['NUMMER'].astype(str) + 
        np.where(recordsDF['CODE_1'].fillna('') != '', recordsDF['CODE_1'].astype(str), '')
    )
    print('[√] MaisFlexis records parsed succesfully')

    recordsDF.to_sql('conversionNames', con=connection, 
                       if_exists='replace', index=False)
    
    connection.close()

    return recordsDF

def getDescriptionData(maisFlexisDescriptions, tablesPath):
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

    connection = sqlite3.connect(database=tablesPath)
    # The description data.
    descriptionsDF = pd.read_csv(maisFlexisDescriptions, encoding='utf-8', on_bad_lines='skip')

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

    descriptionsDF.to_sql('descriptionData', con=connection,
                          if_exists='replace', index=False)      

    connection.close()


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
        #print(f'{algorithm} is: {imageHash}')
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
    filePaths (list): List of paths to the files to be hashed.
    exifToolPath (str): Path to the ExifTool executable.
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
    print()
    for filePath in tqdm.tqdm(filePaths, desc=f'[START] Calculating {algorithm} hashes', bar_format="{desc}: {percentage:5.2f}% |{bar}| {n_fmt}/{total_fmt}", 
    ncols=80, 
    ascii=" ░▒▓█"):
        try:
            # Create a temporary file.
            tempFile = tempfile.NamedTemporaryFile(delete=False)
            tempPath = tempFile.name
            tempFile.close()

            # Ensure the tempPath is deleted if it exists.
            if os.path.exists(tempPath):
                os.remove(tempPath)

            # The command to be used to run the locally installed ExifTool.
            command = [exifToolPath, '-all=', '-o', tempPath, filePath]
            # Subprocess allows programs to run through the command-line-interface and capture its output.
            process = subprocess.Popen(args=command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, error = process.communicate()

            # When the process fails, an exception is raised.
            if process.returncode != 0:
                raise Exception(f"ExifTool Error: {error.decode().strip()}")

            # From the dictionary of possible hash functions, the name of the hash function of the specified algorithm 
            # argument is obtained and used to calculate the hash of that specific function.
            with open(tempPath, "rb") as f:
                fileHash = hashFuncs.get(algorithm)(f.read()).hexdigest()
                hashList.append(fileHash)
                #print(f"{algorithm} hash is {file_hash}")

        # When the process fails we execute the following steps:
        except Exception as e:
            # Show the error message
            errorMessage = f"Error processing {filePath}: {e}"
            print(errorMessage)
            # Add to hashList to match the length of the pandas DataFrame.
            hashList.append(errorMessage)
            continue
        
        # To ensure the tempPath is always removed before the next iteration in the loop
        # we put it in the finally block.
        finally:
            if os.path.exists(tempPath):
                os.remove(tempPath)
    print(f'[√] Calculated {algorithm} hashes succesfully!')
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
    algorithm='average_hash'
    print()
    hashData['aHash'] = [getImageHash(p, algorithm='average_hash') for p in tqdm.tqdm(allImageFilePaths, desc=f'[START] Calculating {algorithm} hashes', bar_format="{desc}: {percentage:5.2f}% |{bar}| {n_fmt}/{total_fmt}", 
    ncols=80, 
    ascii=" ░▒▓█")]
    hashData['filePath'] = allImageFilePaths
    print(f'[√] {algorithm}es calculated succesfully!')
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
    for i in range(len(tqdm.tqdm(range(len(imageFilePaths)),
                    desc='[START] Extracting number of unique colors.',
                    bar_format="{desc}: {percentage:5.2f}% |{bar}| {n_fmt}/{total_fmt}", 
                    ncols=80, 
                    ascii=" ░▒▓█"))):
        try:
            image = Image.open(imageFilePaths[i])
            image = image.convert('RGB')
            colors = image.getcolors(maxcolors=256*256*256)
            numUniqueColors = len(colors)
            numUniqueColorsList.append(numUniqueColors)
        # When the process fails we execute the following steps:
        except Exception as e:
            message = f"Error processing {imageFilePaths[i]}: {e}"
            # Add to numUniqueColorsList to match the length of the pandas DataFrame.
            numUniqueColorsList.append(message)
            print(message)
    print(f'[√] Calculated number of unique colors succesfully!')
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
    
    # The similar images where this is the case  are used to calculate the number of unique colors if
    if len(uniqueColorsDF) > 0:
        uniqueColorsDF['numUniqueColors'] = getUniqueColors(uniqueColorsDF['filePath'].tolist())
    
    else:
        uniqueColorsDF['numUniqueColors'] = np.nan

    uniqueColorsDF.to_sql('uniqueColorData', con=connection,
                        if_exists='replace', index=False)

    # Saving the uniqueColorsDF to CSV.
    uniqueColorsDF.to_csv(os.path.join(processedDataPath, 'uniqueColors.csv'), index=False)


def getInitialImageData(allImageFilePaths, exifToolPath, hashPath, exifDataPath):
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

    print()
    print('###################### Obtaining initial image data ######################')
    print('|------------------------------------------------------------------------|')
    # The initial hash data (filePath, aHash, MD5)
    initialHashData = getInitialHashData(allImageFilePaths=allImageFilePaths,
                                         hashPath=hashPath, 
                                         exifToolPath=exifToolPath)
    
    # The initial exifData (filePath, FileSize, Resolution)
    exifData = getExifData(allImageFilePaths=allImageFilePaths,
                           exifDataPath=exifDataPath,
                           exifToolPath=exifToolPath)
       
    return initialHashData, exifData


def fillTablesInitialData(exifData, initialHashData, tablesPath):
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

        print('\n[START] Inserting the initial image data into the SQL tables.')
        print('[√] Tables filled succesfully!')

        exifData.to_sql('exifData', con=connection,
                       if_exists='replace', index=False)  
        initialHashData.to_sql('initialHashes', con=connection,
                             if_exists='replace', index=False)

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)
    # Closing the connection with the database when done.
    finally:
        if connection:
            connection.close()


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
    print('\n######################  Obtaining exact duplicates  ######################')
    print('|------------------------------------------------------------------------|')
    print('\n[START] Analyzing initial hash data.')
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

    # Images were md5Hash is duplicated but not aHash (possible md5 collision).
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

    # Images were md5Hash is not duplicated but aHash is (possible aHash collision).
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
    print('[√] Analyzed initial hash data succesfully!')
    # Calculating the additional hashes only when needed.
    if len(noAHashAndMD5) > 0 or len(aHashAndNotMD5) > 0:
        print('\nPossible hash collissions found.')
        print('\n[START] calculating additional hashes.')

    if len(noAHashAndMD5) > 0:
        noAHashAndMD5['sha256Hash'] = getFileHash(noAHashAndMD5['filePath'].tolist(), 
                                            exifToolPath, 
                                            algorithm='sha256')
    if len(aHashAndNotMD5) > 0:
        algorithm = 'pHash'
        print()
        aHashAndNotMD5['pHash'] = [getImageHash(aHashAndNotMD5['filePath'].tolist()[i], algorithm='phash') 
                                for i in tqdm.tqdm(range(len(aHashAndNotMD5['filePath'].tolist())),
                                desc=f' * [START] Calculating {algorithm}es', 
                                bar_format="{desc}: {percentage:5.2f}% |{bar}| {n_fmt}/{total_fmt}", 
                                ncols=80, 
                                ascii=" ░▒▓█")]
        
        print(f' * [√] {algorithm}es calculated succesfully!')
        print(f'\n[√] additional hashes calculated succesfully!')
    # Combining results into a single DataFrame.
    finalHashesDF = pd.concat([aHashAndMD5,
                                noAHashAndMD5,  
                                aHashAndNotMD5])

    # Extracting rows with calculated additional hashes only if data is available.
    # If no data is available, an empty DataFrame with the required column names will be created.
    # This ensures that SQL queries can still be run even when the resulting table has no data.
    sha256Rows =\
    finalHashesDF[['filePath', 'sha256Hash']].dropna() if 'sha256Hash' in finalHashesDF.columns \
                                                       else pd.DataFrame(columns=['filePath', 'sha256Hash'])

    pHashRows =\
    finalHashesDF[['filePath', 'pHash']].dropna() if 'pHash' in finalHashesDF.columns \
                                                  else pd.DataFrame(columns=['filePath', 'pHash'])


    # Conditional storing of the results in SQLite tables.
    # Only when there is data in the DataFrame.
    if not sha256Rows.empty:
        sha256Rows.to_sql(name='sha256Rows', 
                        con=connection, 
                        if_exists='replace',
                        index=False)
    # If the DataFrame is empty, create the table with the correct schema (no data).
    else:
        sha256Rows.iloc[0:0].to_sql(name='sha256Rows', 
                        con=connection, 
                        if_exists='replace',
                        index=False)
        
    if not pHashRows.empty:
        pHashRows.to_sql(name='pHashes',
                        con=connection,
                        if_exists='replace',
                        index=False)
    # If the DataFrame is empty, create the table with the correct schema (no data).
    else:
        pHashRows.iloc[0:0].to_sql(name='pHashes',
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
    exactDuplicatesDF =\
    exactDuplicatesDF.to_csv(os.path.join(processedDataPath, 'exactDuplicates.csv'), index=False)
    print('[√] Exact duplicates saved succesfully!')
    connection.close()


def mapDuplicatesToConversionNames(tablesPath, rawDataRecords, exactDuplicates, processedDataPath):
    """
    Maps duplicate images to the MaisFlexis records and saves the results to a CSV file.
    
    This function reads the MaisFlexis record data associated to the images.
    It also extracts duplicate images from the exactDuplicates DataFrame and transforms the file paths. 
    From here the unique filename ('Bestandsnaam') is extracted and used to perform a database join operation to map duplicates to MaisFlexis records.
    It outputs a CSV file with both mapped and unmapped duplicates, indicating if they are coupled to MaisFlexis or not.

    Parameters:
    tablesPath (str): The file path to the SQLite database that contains the conversion names.
    rawDataRecords (str): The file path to the CSV file containing record ID information such as ID and filename.
    exactDuplicates (str): The file path to the CSV file containing the exact duplicate image data.
    processedDataPath (str): The file path where the final mapped duplicates CSV will be saved.

    Returns:
    pandas.DataFrame: A DataFrame containing both linked and unlinked exact duplicate images, along with
    their associated record ID information such as file name and ID number.
    """

    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    cursor = connection.cursor()
    print('\n################## Mapping images to MaisFlexis records ##################')
    print('|------------------------------------------------------------------------|')
    print('\n[START] Transforming duplicate records and preparing data for mapping.')
    # Reading the dataRecords and exactDuplicatesDF.
    rawDataRecordsDF = pd.read_csv(rawDataRecords, sep=';', low_memory=False, skiprows=1)
    exactDuplicatesDF = pd.read_csv(exactDuplicates)
        
    # Transformation on filePath to obtain common unique column values. 
    exactDuplicatesDF['Bestandsnaam'] =\
    exactDuplicatesDF['filePath'].str.split('\\').str.get(-1)

    # Saving the records data as an sql table 
    exactDuplicatesDF.to_sql(name='exactDuplicates',
                             con=connection,
                             if_exists='replace',
                             index=False)

    rawDataRecordsDF.rename(columns={'BESTANDSNAAM' : 'Bestandsnaam'}, inplace=True)

    rawDataRecordsDF.to_sql(name='rawDataRecords', 
                  con=connection, 
                  if_exists='replace',
                  index=False)
    
    print('[√] Data transformed and loaded into the database.')
    print('\n[START] Mapping exact duplicates to MaisFlexis conversion names.')
    # Query to join the duplicate images with the MaisFlexis records.
    mappedDuplicatesQuery = """
    CREATE TABLE IF NOT EXISTS mappedDuplicates AS
    SELECT 
        c.ID, c.AANVRAAGNUMMER, c.NUMMERING_CONVERSIE, 
        d.filePath, d.hashValue, d.hashType, r.TOEGANGSCODE, r.SCN_ID
    FROM 
        conversionNames c
    JOIN 
        exactDuplicates d ON 
            d.Bestandsnaam = r.Bestandsnaam
    JOIN 
        rawDataRecords r ON r.ID = c.ID;
        """
        
    cursor.execute(mappedDuplicatesQuery)
    # Reading the exactDuplicates table as a pandas DataFrame.
    mappedDuplicatesDF = pd.read_sql("SELECT * FROM mappedDuplicates", con=connection)
    mappedDuplicatesDF.loc['Koppelingstatus'] = 'gekoppeld'
    
    # The exact duplicates where the 'Bestandsnaam' is not found in the MaisFlexis records dataframe
    # are not mapped to MaisFlexis yet. A copy is made of this resulting dataframe to avoid pandas warning when 
    # modifying a slice of a dataframe.  
    unmappedDuplicatesDF =\
    exactDuplicatesDF[~exactDuplicatesDF.Bestandsnaam.isin(rawDataRecordsDF['Bestandsnaam'].to_list())].copy()

    # If all the duplicates are mapped the above dataframe will be empty and no Koppelingstatus can be assigned.
    # First check if this is empty to avoid an error.
    if not unmappedDuplicatesDF.empty:
        unmappedDuplicatesDF.loc[:, 'Koppelingstatus'] = 'ongekoppeld'

    # Vertical concatenation of the unmapped and mapped duplicate dataframes.
    exactDuplicatesMapped = pd.concat([unmappedDuplicatesDF, mappedDuplicatesDF])   

    exactDuplicatesMapped.to_csv(os.path.join(processedDataPath, 'duplicateImagesMapped.csv'), index=False)

    # Closing the database connection.
    connection.close()
    print('[√] Exact duplicates successfully mapped to MaisFlexis records!')

    return exactDuplicatesMapped

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

    print('\n######################   Obtaining similar images   ######################')
    print('|------------------------------------------------------------------------|')
    print('\n[START] Analyzing image hashes.')
    # Query to select images with duplicate pHash.
    querySimilarImages = """
    CREATE TABLE IF NOT EXISTS similarImages AS
    SELECT 'pHash' as hashType, pHash as hashValue, filePath
    FROM pHashes
    WHERE pHash IN (
        SELECT pHash
        FROM pHashes
        GROUP BY pHash
        HAVING COUNT(*) > 1
    );
    """

    # Executing the query to create the table.
    cursor.execute(querySimilarImages)
    connection.commit()
    print('[√] Image hashes analyzed successfully!')
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
    print('\n[START] Ranking similar images.')
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
    
    # Committing the changes and closing the connection.
    connection.commit()
    connection.close()
    print('[√] Similar images ranked succesfully!')
    return similarImagesRankedDF

    
def mapSimilarImagesToConversionNames(tablesPath, rawDataRecords, similarImages, processedDataPath):
    """
    Maps similar images to the MaisFlexis records and saves the results to a CSV file.
    
    This function reads the MaisFlexis record data associated to the images.
    It also extracts similar images from the exactDuplicates DataFrame and transforms the file paths. 
    From here the unique filename ('Bestandsnaam') is extracted and used to perform a database join operation to map duplicates to MaisFlexis records.
    It outputs a CSV file with both mapped and unmapped duplicates, indicating if they are coupled to MaisFlexis or not.

    Parameters:
    tablesPath (str): The file path to the SQLite database that contains the conversion names.
    rawDataRecords (str): The file path to the CSV file containing record ID information such as ID and filename.
    exactDuplicates (str): The file path to the CSV file containing the exact duplicate image data.
    processedDataPath (str): The file path where the final mapped duplicates CSV will be saved.

    Returns:
    pandas.DataFrame: A DataFrame containing both linked and unlinked exact duplicate images, along with
    their associated record ID information such as file name and ID number.

    """

    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    cursor = connection.cursor()
    print('\n[START] Transforming similar records and preparing data for mapping.')
    # Reading the dataRecords and exactDuplicatesDF
    rawDataRecordsDF = pd.read_csv(rawDataRecords, delimiter=';', low_memory=False, skiprows=1)
    similarImagesDF = pd.read_csv(similarImages)

        
    # Transformation on filePath to obtain common unique column values 
    similarImagesDF['Bestandsnaam'] = similarImagesDF['filePath'].str.split('\\').str.get(-1)

    # Saving the records data as an sql table 
    similarImagesDF.to_sql(name='similarImages',
                             con=connection,
                             if_exists='replace',
                             index=False)
        
    print('[√] Data transformed and loaded into the database.')
    print('\n[START] Mapping similar images to MaisFlexis conversion names.')
    
    # Query to join the similar images with the MaisFlexis records.
    mappedDuplicatesQuery = """
    CREATE TABLE IF NOT EXISTS mappedSimilarImages AS
    SELECT 
        c.ID, c.AANVRAAGNUMMER, c.NUMMERING_CONVERSIE, 
        d.filePath, d.hashValue, d.hashType, r.TOEGANGSCODE, r.SCN_ID
    FROM 
        conversionNames c
    JOIN 
        similarImages d ON 
            d.Bestandsnaam = r.Bestandsnaam
    JOIN 
        rawDataRecords r ON r.ID = c.ID;
        """
        
    cursor.execute(mappedDuplicatesQuery)
    # Reading the exactDuplicates table as a pandas DataFrame.
    mappedSimilarImagesDF = pd.read_sql("SELECT * FROM mappedSimilarImages", con=connection)

    mappedSimilarImagesDF['Koppelingstatus'] = 'gekoppeld'

    # The similar images where the 'Bestandsnaam' is not found in the MaisFlexis records dataframe
    # are not mapped to MaisFlexis yet. A copy is made of this resulting dataframe to avoid pandas warning when 
    # modifying a slice of a dataframe.  
    
    unmappedSimilarImagesDF = similarImagesDF[~similarImagesDF.Bestandsnaam.isin(rawDataRecordsDF['BESTANDSNAAM'].to_list())]
    unmappedSimilarImagesDF['Koppelingstatus'] = 'ongekoppeld'
    similarImagesMapped = pd.concat([unmappedSimilarImagesDF, mappedSimilarImagesDF])   

    similarImagesMapped.to_csv(os.path.join(processedDataPath, 'similarImagesMapped.csv'), index=False)

    # Closing the database connection.
    connection.close()
    print('[√] Similar images successfully mapped to MaisFlexis records!')
    print('\n|------------------------------------------------------------------------|')
    print('########################### Analysis complete! ###########################')
    print('\nThe results are saved in the data\\processed folder.')

    return similarImagesMapped


