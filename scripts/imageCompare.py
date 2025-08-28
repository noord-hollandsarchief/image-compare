import os
import subprocess
import json
import hashlib
import tempfile
import sqlite3
import re

import numpy as np
import pandas as pd
import imagehash
from PIL import Image
import tqdm
from bs4 import BeautifulSoup

import utils

def getAllImageFilePaths(directories):
    """
    Recursively collect all image file paths from one or more directories.

    This function:
    - Walks through the given directory (or list of directories) and 
      collects all file paths.
    - Automatically detects 3-character file extensions present in the
      collected files (e.g., 'jpg', 'png', 'tif').
    - Returns only those files with the detected image extensions.

    Parameters
    ----------
    directories : str or list of str
        A directory path (string) or a list of directory paths to search.

    Returns
    -------
    list of str
        A list of full file paths pointing to image files.
    """
    # Handle single path passed as a string
    if isinstance(directories, str):
        directories = [directories]

    allFilePaths = []

    for directory in directories:
        # Recursively walk through all subdirectories
        for root, _, files in os.walk(directory):
            for file in files:
                fullPath = os.path.join(root, file)
                allFilePaths.append(fullPath)

    # Detect 3-character file extensions (e.g., jpg, png)
    imageExtensions = set(
        p.split('.')[-1].lower() for p in allFilePaths
        if len(p.split('.')[-1]) == 3
    )

    # Filter to include only image files
    allImageFilePaths = [
        p for p in allFilePaths
        if p.split('.')[-1].lower() in imageExtensions
    ]

    return allImageFilePaths


def getExifData(allImageFilePaths, exifDataPath, exifToolPath):
    """
    Extract Exif metadata from a list of image files using ExifTool.

    For each image file provided, this function calls the ExifTool executable
    via subprocess, requesting metadata in JSON format. Only a predefined set 
    of relevant fields (e.g., resolution, dimensions, file size) is kept. The 
    extracted metadata is stored in a pandas DataFrame and also saved to a CSV file.

    Parameters
    ----------
    allImageFilePaths : list of str
        List of full file paths to image files.
    exifDataPath : str
        Path to save the resulting CSV file containing extracted Exif metadata.
    exifToolPath : str
        Path to the ExifTool executable.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing extracted Exif metadata for all processed images.
        Columns include:
        - 'filePath'
        - 'FileSize'
        - 'XResolution'
        - 'YResolution'
        - 'ImageWidth'
        - 'ImageHeight'

    Notes
    -----
    - Uses tqdm to display progress with a custom progress bar.
    - Errors during extraction for a file are caught and printed, and that file’s 
      metadata row may be incomplete.
    - The CSV output is always written, even if some files fail.
    """
    # Specifying the fields to extract 
    relevantFields = ["FileSize", "XResolution", "YResolution", "ImageWidth", "ImageHeight"]
   
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


def getConversionNames(maisFlexisRecords, tablesPath, pathToConversionNames):
    """
    Clean and transform MaisFlexis record data for downstream use.

    This function:
    - Reads MaisFlexis export data from an Excel file into a pandas DataFrame.
    - Strips HTML tags from selected text fields 
      (AANVRAAGNUMMER, FOTONUMMER, NUMMERING_CONVERSIE).
    - Ensures the NUMMER field is present and numeric.
    - Saves the cleaned records both as a CSV file and as a table 
      ('conversionNames') in a SQLite database.

    Parameters
    ----------
    maisFlexisRecords : str
        Path to the Excel file containing records exported from MaisFlexis.
    tablesPath : str
        Path to the SQLite database file where the processed records will be stored.
    pathToConversionNames : str
        Path to save the cleaned records as a CSV file.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the cleaned and transformed MaisFlexis records.
    """
    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)

    connection.commit()
    print()
    # Initialize tqdm progress bar for the transformation process
    tqdm.tqdm.pandas(desc=f'[START] Parsing MaisFlexis records', bar_format="{desc}: {percentage:5.2f}% |{bar}| {n_fmt}/{total_fmt}", 
    ncols=80, 
    ascii=" ░▒▓█")
    
    # Reading the raw records data file into a pandas DataFrame
    recordsDF = pd.read_excel(maisFlexisRecords)
    
    # Function to remove HTML tags and replace them with ', '
    def removeHtmlTags(text):
        if not isinstance(text, str):
            return text  # Return as-is if not string

        # Replace <br> and variants with comma
        text = re.sub(r'<br\s*/?>', ', ', text, flags=re.IGNORECASE)

        # Parse with BeautifulSoup to remove all other HTML tags properly
        soup = BeautifulSoup(text, "html.parser")

        # Get text content (tags stripped)
        clean_text = soup.get_text(separator=', ')

        # Clean up multiple commas/spaces
        clean_text = re.sub(r'\s*,\s*', ', ', clean_text)  # Normalize commas with spaces
        clean_text = re.sub(r',(,)+', ', ', clean_text)     # Remove duplicate commas
        clean_text = re.sub(r'\s+', ' ', clean_text)        # Replace multiple spaces with one
        clean_text = clean_text.strip(' ,')                  # Strip trailing commas/spaces

        return clean_text
    
    # Apply the transformation with a single progress bar
    # Replacing applymap with progress_apply for better performance
    recordsDF[['AANVRAAGNUMMER', 'FOTONUMMER', 'NUMMERING_CONVERSIE']] =\
    recordsDF[['AANVRAAGNUMMER', 'FOTONUMMER', 'NUMMERING_CONVERSIE']].fillna('').map(removeHtmlTags)
        
    recordsDF = recordsDF.dropna(subset=['NUMMER'])
    recordsDF['NUMMER'] = recordsDF['NUMMER'].astype(int)
    
    print('[√] MaisFlexis records parsed succesfully')
    recordsDF.to_csv(pathToConversionNames, index=False)
    recordsDF.to_sql('conversionNames', con=connection, 
                       if_exists='replace', index=False)
    
    connection.close()

    return recordsDF


def getImageHash(filePath, algorithm='average_hash'):
    """
    Calculate an image hash to help identify visually similar images.

    Supported algorithms:
    - 'average_hash'
    - 'phash'

    Parameters
    ----------
    filePath : str
        Path to the image file to be hashed.
    algorithm : str, optional
        Hashing algorithm to use. Default is 'average_hash'.

    Returns
    -------
    list
        A list containing the computed image hash (hexadecimal string).
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
    Calculate file hashes for duplicate detection after removing metadata.

    Each file is processed by ExifTool to create a temporary, metadata-stripped
    copy. The hash of this stripped file is then calculated using the specified
    algorithm. This ensures that only file content (not metadata differences)
    influences the hash value.

    Supported algorithms:
    - 'md5'
    - 'sha256'

    Parameters
    ----------
    filePaths : list of str
        Paths to the files to be hashed.
    exifToolPath : str
        Path to the ExifTool executable.
    algorithm : str, optional
        Hash algorithm to use. Default is 'md5'.

    Returns
    -------
    list of str
        A list of file hashes in hexadecimal format, one per input file.
        If a file cannot be processed, an error message string is returned
        in place of its hash.
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
    Generate initial hash data (MD5 and average hash) for a collection of image files.

    For each file, this function computes:
    - An MD5 hash (based on a metadata-stripped copy, using ExifTool)
    - An average perceptual hash (aHash), useful for detecting visually similar images

    The resulting data is stored in a pandas DataFrame with the following columns:
    - 'md5Hash': MD5 hashes of the files
    - 'aHash': average perceptual image hashes
    - 'filePath': original file paths

    The DataFrame is also saved as a CSV file at the specified path.

    Parameters
    ----------
    allImageFilePaths : list of str
        Paths to the image files to be hashed.
    hashPath : str
        Path where the resulting CSV file will be saved.
    exifToolPath : str
        Path to the ExifTool executable.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the initial hash data for all input files.
    """
    # Initializing the intial hashes pandas DataFrame.
    hashData = pd.DataFrame(index=range(len(allImageFilePaths)))
    
    # Assigning the values to the pandas DataFrame as lists.
    hashData['md5Hash'] = getFileHash(allImageFilePaths, exifToolPath, algorithm='md5')
    algorithm='average_hash'
  
    hashData['aHash'] = [getImageHash(path, algorithm='average_hash') for path in
                         tqdm.tqdm(allImageFilePaths, desc=f'[START] Calculating {algorithm} hashes',\
                         bar_format="{desc}: {percentage:5.2f}% |{bar}| {n_fmt}/{total_fmt}", 
                         ncols=80, ascii=" ░▒▓█")]
    
    hashData['filePath'] = allImageFilePaths
    print(f'[√] {algorithm}es calculated succesfully!')
    # Saving the pandas DataFrame as CSV file.
    hashData.to_csv(hashPath, index=False)
    return hashData


def makeTables(tablesPath):
    """
    Initialize the SQLite database schema by creating all required tables.

    This function sets up the core database structure used for storing file hashes,
    Exif metadata, and descriptive information. It enables foreign key constraints
    and creates the following tables if they do not already exist:

    - initialHashes: Stores file-level hash values (md5, sha256, aHash) and file paths.
    - exifData: Stores selected Exif metadata (e.g., file size, resolution).
    - conversionNames: Stores MaisFlexis conversion records, linked to files by md5Hash.
    - descriptionData: Stores descriptive metadata, also linked to files by md5Hash.

    Parameters
    ----------
    tablesPath : str
        Path to the SQLite database file to be created or updated.

    Returns
    -------
    None
    """
    # Creating the database file in tablesPath and establishing a connection.
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
        XResolution INT,
        YResolution INT
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
        CODE INTEGER,
        AET_ID TEXT,
        NUMMER INTEGER,
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
    Count the number of unique RGB colors for each image in a list of file paths.

    Each image is opened, converted to RGB, and analyzed to determine the total
    number of distinct colors. Since each channel (R, G, B) has 256 possible values,
    the theoretical maximum is 256^3 = 16,777,216 unique colors per image.

    **Important:** To avoid errors when processing very large images, the function
    disables the PIL.Image.MAX_IMAGE_PIXELS limit by setting it to None. By default,
    Pillow raises a DecompressionBombError for images with an extremely high pixel count
    to prevent potential denial-of-service (DDoS) attacks. Disabling this limit allows
    large images to be processed but should be done with caution, especially when
    processing untrusted images, as it could consume a large amount of memory.

    The results are returned as a list, where each entry corresponds to one input file.
    If an image cannot be processed, an error message string is stored instead to
    preserve alignment with the input list.

    Parameters
    ----------
    imageFilePaths : list of str
        List of file paths to the images to analyze.

    Returns
    -------
    list of int or str
        A list containing either:
        - the number of unique colors (int) for each image, or
        - an error message (str) if processing failed.
    """
    # This has to be further specified.
    # Find max value in database 
    Image.MAX_IMAGE_PIXELS = None

    numUniqueColorsList = [] 
   
    # Calculate the number of unique colors for each of the files in the list of paths.
    for i in tqdm.tqdm(range(len((imageFilePaths))),
                    desc='[START] Extracting number of unique colors.',
                    bar_format="{desc}: {percentage:5.2f}% |{bar}| {n_fmt}/{total_fmt}", 
                    ncols=80, 
                    ascii=" ░▒▓█"):
        try:
            image = Image.open(imageFilePaths[i])
            image = image.convert('RGB')
            colors = image.getcolors(maxcolors=256*256*256)
            numUniqueColors = len(colors)
            numUniqueColorsList.append(numUniqueColors)
        # When the process fails we execute the following steps:
        except Exception as e:
            message = f"Error processing {imageFilePaths[i]}: {e}"
            # Add to numUniqueColorsList to match the lengath of the pandas DataFrame.
            numUniqueColorsList.append(message)
            print(message)
    print(f'[√] Calculated number of unique colors succesfully!')
    return numUniqueColorsList


def getUniqueColorsTable(tablesPath, processedDataPath):
    """
    Extract the highest-resolution image per hash, compute the number of unique RGB colors,
    and store the results in both an SQLite table and a CSV file.

    For each hash value, the function selects images with the highest resolution. It then calculates
    the number of unique colors in these images (up to 256^3 possible RGB values) using the
    `getUniqueColors` function. The results are saved to a table named 'uniqueColorData' in the
    database and as a CSV file in the specified processed data path.

    Parameters
    ----------
    tablesPath : str
        Path to the SQLite database file containing image and similarity data.
    processedDataPath : str
        Path to the directory where the processed CSV file will be saved.

    Returns
    -------
    None
    """
    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    
    # From the similar images, the highest resolutions are extracted.
    similarImagesSameResolution = """
    WITH BaseData AS (
    SELECT
        s.hashValue,
        e.filePath,
        e.XResolution,
        e.YResolution,
        e.ImageWidth,
        e.ImageHeight,
        COALESCE(e.XResolution, 0) * COALESCE(e.YResolution, 0) AS ResolutionProduct,
        CASE
            WHEN e.ImageWidth IS NOT NULL AND e.ImageHeight IS NOT NULL THEN e.ImageWidth * e.ImageHeight
            ELSE NULL
        END AS ImagePixelCount
    FROM
        exifData e
    JOIN similarImages s ON e.filePath = s.filePath
    ),

    -- Step 1: Find hashValues where X*Y resolution is not unique (i.e. all values are the same)
    GroupedResolution AS (
        SELECT
            hashValue,
            COUNT(DISTINCT ResolutionProduct) AS UniqueResCount
        FROM BaseData
        GROUP BY hashValue
    ),

    SameResolutionGroups AS (
        SELECT b.*
        FROM BaseData b
        JOIN GroupedResolution gr ON b.hashValue = gr.hashValue
        WHERE gr.UniqueResCount = 1
    ),

    -- Step 2: From same-resolution groups, check if ImagePixelCount is also not unique
    GroupedImagePixels AS (
        SELECT
            hashValue,
            COUNT(DISTINCT ImagePixelCount) AS UniquePixelCount
        FROM SameResolutionGroups
        GROUP BY hashValue
    ),

    SameImagePixelsOrMissing AS (
        SELECT s.*
        FROM SameResolutionGroups s
        JOIN GroupedImagePixels gip ON s.hashValue = gip.hashValue
        WHERE gip.UniquePixelCount = 1 OR s.ImagePixelCount IS NULL
    )

    SELECT *
    FROM SameImagePixelsOrMissing
    ORDER BY hashValue, filePath;
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
    Gather initial image hashes and resolution-related Exif metadata for a list of image files.

    This function computes initial hash values (MD5 and aHash) for each image and extracts
    the resolution-related Exif metadata: XResolution, YResolution, ImageWidth, and ImageHeight.  
    These fields are critical for downstream processing, such as selecting the highest-resolution
    image per hash and ranking similar images.

    - MD5 provides a cryptographic hash for exact file integrity checks.
    - aHash (average hash) is a perceptual hash that allows comparison of image content,
    even if the file has minor modifications (e.g., compression or format changes).

    The hash data is saved as a CSV in the specified `hashPath`, while the Exif metadata
    is returned as a separate DataFrame.

    Parameters
    ----------
    allImageFilePaths : list of str
        Paths to the image files to process.
    exifToolPath : str
        Path to the ExifTool executable for extracting image metadata.
    hashPath : str
        Path where the CSV file containing initial hash data will be saved.
    exifDataPath : str
        Path where the CSV file containing extracted Exif data will be saved.

    Returns
    -------
    initialHashData : pandas.DataFrame
        DataFrame containing the initial hash values (MD5, aHash) and corresponding file paths.
    exifData : pandas.DataFrame
        DataFrame containing resolution-related Exif metadata (XResolution, YResolution,
        ImageWidth, ImageHeight) for each image.
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
    Populate the SQLite database tables with initial image hash and Exif metadata.

    This function inserts the data from the DataFrames returned by `getInitialImageData`
    into the corresponding SQLite tables (`initialHashes` and `exifData`). These tables
    are typically created by the `makeTables` function before being populated. Existing
    tables with the same names will be replaced.

    Parameters
    ----------
    exifData : pandas.DataFrame
        DataFrame containing resolution-related Exif metadata (XResolution, YResolution,
        ImageWidth, ImageHeight) for each image.
    initialHashData : pandas.DataFrame
        DataFrame containing the initial hash values (MD5, aHash) and corresponding file paths.
    tablesPath : str
        Path to the SQLite database file where the tables will be created or replaced.

    Returns
    -------
    None

    Notes
    -----
    - This function overwrites any existing tables with the same names in the database.
    - Connection to the database is automatically closed after the operation.
    - Errors during insertion are caught and printed.
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
    Identify and process exact duplicate images, calculate additional hashes when needed, 
    and store results in SQLite and CSV.

    This function analyzes image hashes to detect exact duplicates based on MD5 and aHash. 
    In cases where collisions may exist (duplicate MD5 but different aHash, or vice versa), 
    additional hashes (SHA-256 or pHash) are computed for further verification. 
    The results are stored in a SQLite table and exported to a CSV file.

    Parameters
    ----------
    tablesPath : str
        Path to the SQLite database file containing initial hash data.
    exifToolPath : str
        Path to the ExifTool executable, used to compute additional file hashes.
    processedDataPath : str
        Path to the folder where the resulting CSV of exact duplicates will be saved.

    Returns
    -------
    None
        The function saves results to the database and CSV file; it does not return a value.

    Notes
    -----
    - The function creates or replaces the following database tables: `sha256Rows`, `pHashes`, `exactDuplicates`.
    - Additional hash calculations are performed only when potential collisions are detected.
    - The CSV is always written to `processedDataPath/exactDuplicates.csv`.
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

    cursor.execute("DROP TABLE IF EXISTS exactDuplicates;")
    connection.commit()

    # Creating the table for exact duplicates.
    cursor.executescript("""
    DROP TABLE IF EXISTS exactDuplicates;

    CREATE TABLE exactDuplicates AS
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
    """)
    connection.commit()

    # Saving the final DataFrame to CSV.
    exactDuplicatesDF = pd.read_sql("SELECT * FROM exactDuplicates", con=connection)
    exactDuplicatesDF =\
    exactDuplicatesDF.to_csv(os.path.join(processedDataPath, 'exactDuplicates.csv'), index=False)
    print('[√] Exact duplicates saved succesfully!')
    connection.close()


def mapDuplicatesToConversionNames(tablesPath, rawDataRecords, exactDuplicates, pathToExactDuplicatesMatchedMapped):
    """
    Map exact duplicate images to MaisFlexis conversion records and export the results.

    This function reads exact duplicate image records and raw MaisFlexis data, transforms 
    the data, and maps each duplicate image to its corresponding MaisFlexis record based on 
    filename matching. Additional conversion and description information is added, and a 
    mapping status column indicates whether a match was found. The final results are saved 
    to an Excel sheet and returned as a DataFrame.

    Parameters
    ----------
    tablesPath : str
        Path to the SQLite database file used for intermediate storage.
    rawDataRecords : str
        Path to the CSV file containing raw MaisFlexis records.
    exactDuplicates : str
        Path to the CSV file containing exact duplicate image information.
    pathToExactDuplicatesMatchedMapped : str
        Path to the Excel file where the mapped results will be saved.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing mapped duplicates, conversion information, hash details, 
        and mapping status ('gekoppeld' or 'ongekoppeld').

    Notes
    -----
    - Existing tables in the database (`exactDuplicates`, `rawDataRecords`, `mappedDuplicates`) will be replaced.
    - Filename extraction assumes backslash (`\\`) separators in paths.
    - Uses a utility function `utils.writeDfToExcelSheet` to export results to Excel.
    """
    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    cursor = connection.cursor()
    print('\n################## Mapping duplicates to MaisFlexis records ##################')
    print('|------------------------------------------------------------------------|')
    print('\n[START] Transforming duplicate records and preparing data for mapping.')

    rawDataRecordsDF = pd.read_csv(rawDataRecords, delimiter=',', low_memory=False)
    exactDuplicatesDF = pd.read_csv(exactDuplicates)

    exactDuplicatesDF['Bestandsnaam'] = exactDuplicatesDF['filePath'].str.split('\\').str.get(-1)

    # Save tables to DB
    exactDuplicatesDF.to_sql(name='exactDuplicates', con=connection, if_exists='replace', index=False)

    rawDataRecordsDF.rename(columns={'BESTANDSNAAM': 'Bestandsnaam'}, inplace=True)
    rawDataRecordsDF.to_sql(name='rawDataRecords', con=connection, if_exists='replace', index=False)

    print('[√] Data transformed and loaded into the database.')
    print('\n[START] Mapping exact duplicates to MaisFlexis conversion names.')

    mappedDuplicatesQuery = """
    DROP TABLE IF EXISTS mappedDuplicates;

    CREATE TABLE mappedDuplicates AS
    SELECT 
        c.ID, c.CODE, c.NUMMER, c.CODE_1, c.AANVRAAGNUMMER, c.NUMMERING_CONVERSIE,
        r.Bestandsnaam, r.TOEGANGSCODE, r.SCN_ID,
        d.filePath, d.hashValue, d.hashType,
        CASE WHEN r.Bestandsnaam IS NOT NULL THEN 'gekoppeld' ELSE 'ongekoppeld' END AS Koppelingstatus, dd.INHOUD, dd.OPMERKINGEN
    FROM 
        exactDuplicates d
    LEFT JOIN 
        rawDataRecords r ON d.Bestandsnaam = r.Bestandsnaam
    LEFT JOIN
        conversionNames c ON r.ID = c.ID
    LEFT JOIN
        descriptionData dd ON dd.ID = c.ID;
    """
    cursor.executescript(mappedDuplicatesQuery)
    connection.commit()

    mappedDuplicatesDF = pd.read_sql("SELECT * FROM mappedDuplicates", con=connection)
    mappedDuplicatesDF = mappedDuplicatesDF.reset_index(drop=True)

    utils.writeDfToExcelSheet(pathToExactDuplicatesMatchedMapped, mappedDuplicatesDF, sheet_name='exactDuplicatesMapped')

    connection.close()

    print('[√] Exact duplicates successfully mapped to MaisFlexis records!')
    print(f'Results saved to: {pathToExactDuplicatesMatchedMapped}')

    return mappedDuplicatesDF


def getSimilarImages(tablesPath, processedDataPath):
    """
    Identify and store images with similar perceptual hashes (pHashes) in a database and CSV.

    This function analyzes the `pHashes` table in the SQLite database to detect images that
    share the same perceptual hash, indicating potential visual similarity. It creates a new
    `similarImages` SQL table, reads it into a pandas DataFrame, and exports the results to
    a CSV file in the specified processed data folder.

    Parameters
    ----------
    tablesPath : str
        Path to the SQLite database file containing the initialHashes and pHashes table.
    processedDataPath : str
        Path to the folder where the resulting CSV of similar images will be saved.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the similar images, including:
        - `hashType`: type of hash used ('aHash or pHash')
        - `hashValue`: the perceptual hash value
        - `filePath`: path to the image file

    Notes
    -----
    - The function drops and recreates the `similarImages` table each time it is run.
    - Only images with duplicate pHashes are considered as similar.
    - The CSV file is saved as `similarImages.csv` in `processedDataPath`.
    """
    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    cursor = connection.cursor()

    print('\n######################   Obtaining similar images   ######################')
    print('|------------------------------------------------------------------------|')
    print('\n[START] Analyzing image hashes.')

    # Check if pHashes table has any rows
    pHashCount = pd.read_sql("SELECT COUNT(*) as cnt FROM pHashes", connection)['cnt'][0]

    if pHashCount > 0:
        # Use pHash
        querySimilarImages = """
        DROP TABLE IF EXISTS similarImages;
        CREATE TABLE similarImages AS
        SELECT 'pHash' as hashType, pHash as hashValue, filePath
        FROM pHashes
        WHERE pHash IN (
            SELECT pHash
            FROM pHashes
            GROUP BY pHash
            HAVING COUNT(*) > 1
        );
        """
        print("[INFO] Using pHash table for similarity detection.")
    else:
        # Fallback to aHash from initialHashes
        querySimilarImages = """
        DROP TABLE IF EXISTS similarImages;
        CREATE TABLE similarImages AS
        SELECT 'aHash' as hashType, aHash as hashValue, filePath
        FROM initialHashes
        WHERE aHash IN (
            SELECT aHash
            FROM initialHashes
            GROUP BY aHash
            HAVING COUNT(*) > 1
        );
        """
        print("[INFO] pHashes table empty. Falling back to aHash from initialHashes.")

    # Executing the query to drop and create the table.
    cursor.executescript(querySimilarImages)
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
    Rank similar images based on perceptual hash, resolution, and unique color count.

    This function identifies images with the same perceptual hash (pHash) from the 
    `similarImages` table and ranks them to determine the "best" version. Ranking 
    prioritizes images with higher resolution (calculated from X and Y resolution or 
    ImageWidth * ImageHeight). If resolution information is missing, the number of unique 
    colors is used as a fallback criterion. The results are stored in a SQLite table 
    `similarImagesRanked` and exported as a CSV file.

    Parameters
    ----------
    tablesPath : str
        Path to the SQLite database file containing the `similarImages`, `exifData`, 
        and `uniqueColorData` tables.
    processedDataPath : str
        Path to the folder where the resulting ranked similar images CSV will be saved.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the ranked similar images, including:
        - `filePath`: path to the image file
        - `hashType`: type of hash used ('pHash')
        - `hashValue`: perceptual hash value
        - `XResolution`, `YResolution`: image resolution in pixels
        - `ImageWidth`, `ImageHeight`: image dimensions
        - `resolutionScore`: product of X and Y resolution
        - `pixelCount`: fallback resolution metric based on image dimensions
        - `numUniqueColors`: number of unique colors in the image
        - `rank`: ranking of the image within its hash group (1 = best)

    Notes
    -----
    - The function drops and recreates the `similarImagesRanked` table each time it is run.
    - Images are ranked per `hashValue` using resolution first, then unique colors, and 
      finally `filePath` as a tie-breaker.
    - The CSV file is saved as `similarImagesRanked.csv` in `processedDataPath`.
    """
    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    cursor = connection.cursor()
    print('\n[START] Ranking similar images.')
    # Create a table 'similarImagesRanked' to identify the best representative image 
    # for each set of visually similar images. Ranking is based on pHash similarity,
    # image resolution, pixel count, and number of unique colors.

    # The best image is generally the one with the highest resolution.
    # Resolution is considered in two ways:
    # 1. resolutionScore = XResolution * YResolution (DPI-based)
    # 2. pixelCount = ImageWidth * ImageHeight (actual dimensions, used if available)

    # If multiple images have the same resolution or resolution data is missing,
    # the number of unique colors is used as a secondary criterion to determine 
    # the best image.

    # Finally, if there is still a tie, the filePath is used as a deterministic
    # tie-breaker to ensure consistent ranking.

    # Drop any existing table to avoid conflicts
    rankedImagesQuery = """
    DROP TABLE IF EXISTS similarImagesRanked;

    CREATE TABLE similarImagesRanked AS
    WITH RankedFiles AS (
        SELECT 
            s.filePath, 
            s.hashType,
            s.hashValue, 
            e.XResolution, 
            e.YResolution,
            e.ImageWidth,
            e.ImageHeight,
            (e.XResolution * e.YResolution) AS resolutionScore,
            (CASE 
                WHEN e.ImageWidth IS NOT NULL AND e.ImageHeight IS NOT NULL 
                    AND e.ImageWidth > 0 AND e.ImageHeight > 0 
                THEN e.ImageWidth * e.ImageHeight 
                ELSE NULL 
            END) AS pixelCount,
            u.numUniqueColors,
            DENSE_RANK() OVER (
                PARTITION BY s.hashValue 
                ORDER BY 
                    (e.XResolution * e.YResolution) DESC,
                    -- Only use pixelCount if present
                    CASE 
                        WHEN e.ImageWidth IS NOT NULL AND e.ImageHeight IS NOT NULL 
                            AND e.ImageWidth > 0 AND e.ImageHeight > 0 
                        THEN e.ImageWidth * e.ImageHeight
                        ELSE NULL
                    END DESC,
                    -- numUniqueColors fallback
                    u.numUniqueColors DESC,
                    -- Tie-breaker
                    s.filePath ASC
            ) AS rank
        FROM similarImages s
        JOIN exifData e ON s.filePath = e.filePath
        LEFT JOIN uniqueColorData u ON s.filePath = u.filePath
        WHERE s.hashValue IN (
            SELECT hashValue
            FROM similarImages
            GROUP BY hashValue
            HAVING COUNT(*) > 1
        )
    )
    SELECT * 
    FROM RankedFiles
    ORDER BY hashValue ASC, rank ASC;

    """
    # Executing the query to create the ranked table.
    cursor.executescript(rankedImagesQuery)
    connection.commit()

    # Reading the ranked similar images into a pandas DataFrame.
    similarImagesRankedDF = pd.read_sql("SELECT * FROM similarImagesRanked", con=connection)
   
    # Saving the DataFrame to a CSV file.
    similarImagesRankedDF = similarImagesRankedDF.to_csv(os.path.join(processedDataPath, 'similarImagesRanked.csv'), index=False)
    
    # Committing the changes and closing the connection.
    connection.commit()
    connection.close()
    print('[√] Similar images ranked succesfully!')
    return similarImagesRankedDF

    
def mapSimilarImagesToConversionNames(tablesPath, rawDataRecords, similarImagesRanked, pathToSimilarImagesMatchedMapped):
    """
    Map ranked similar images to MaisFlexis records and export the results.

    This function loads ranked similar images and MaisFlexis metadata, extracts filenames, 
    performs SQL joins to match images with records, adds a mapping status column, and 
    saves the final mapped results to an Excel file.

    Parameters
    ----------
    tablesPath : str
        Path to the SQLite database file used for temporary storage and SQL operations.
    rawDataRecords : str
        Path to the CSV file containing MaisFlexis record metadata.
    similarImagesRanked : str
        Path to the CSV file containing ranked similar image information.
    pathToSimilarImagesMatchedMapped : str
        Path to the Excel file where the mapped results will be saved.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing mapped and unmapped similar images, including:
        - MaisFlexis record fields (ID, CODE, NUMMER, etc.)
        - Image fields (filePath, hashValue, hashType, resolution, unique colors, rank)
        - `Koppelingstatus`: Indicates whether the image is linked ("gekoppeld") or unlinked ("ongekoppeld")
        - Description field (`INHOUD`) from the description table

    Notes
    -----
    - Existing `mappedSimilarImages` table in the database will be replaced.
    - Filename extraction assumes backslash (`\\`) separators in paths.
    - The function saves the results using `utils.writeDfToExcelSheet` in a sheet named `similarImagesMapped`.
    """
    # Connecting to the database in tablesPath.
    connection = sqlite3.connect(database=tablesPath)
    cursor = connection.cursor()

    print('\n[START] Transforming similar records and preparing data for mapping.')

    # Load the MaisFlexis and similar image data CSVs
    rawDataRecordsDF = pd.read_csv(rawDataRecords, delimiter=',', low_memory=False)
    # Normalize column name for join
    rawDataRecordsDF.rename(columns={'BESTANDSNAAM': 'Bestandsnaam'}, inplace=True)
    similarImagesRankedDF = pd.read_csv(similarImagesRanked)

    # Extract filename from filePath in similarImagesRankedDF for joining
    similarImagesRankedDF['Bestandsnaam'] = similarImagesRankedDF['filePath'].str.split('\\').str.get(-1)

    # Save rawDataRecordsDF to SQL for join (replace existing table)
    rawDataRecordsDF.to_sql(name='rawDataRecords', con=connection, if_exists='replace', index=False)

    # similarImagesRankedDF already saved in your previous code, but safer to also save rawDataRecords here:
    similarImagesRankedDF.to_sql(name='similarImagesRanked', con=connection, if_exists='replace', index=False)

    print('[√] Data loaded into the database.')

    # SQL: LEFT JOIN to get both mapped and unmapped, with status column
    mappedSimilarImagesQuery = """
    DROP TABLE IF EXISTS mappedSimilarImages;

    CREATE TABLE mappedSimilarImages AS
    SELECT 
        c.ID, c.CODE, c.NUMMER, c.CODE_1, c.AANVRAAGNUMMER, c.NUMMERING_CONVERSIE, 
        r.Bestandsnaam, r.TOEGANGSCODE, r.SCN_ID,
        d.filePath, d.hashValue, d.hashType, d.XResolution, d.YResolution, d.numUniqueColors, d.rank,
        CASE WHEN r.Bestandsnaam IS NOT NULL THEN 'gekoppeld' ELSE 'ongekoppeld' END AS Koppelingstatus, dd.INHOUD, dd.OPMERKINGEN
    FROM 
        similarImagesRanked d
    LEFT JOIN 
        rawDataRecords r ON d.Bestandsnaam = r.Bestandsnaam
    LEFT JOIN
        conversionNames c ON r.ID = c.ID
    LEFT JOIN
        descriptionData dd ON dd.ID = c.ID;
    """

    cursor.executescript(mappedSimilarImagesQuery)
    connection.commit()

    print('[√] SQL join completed. Loading results.')

    # Load results from the database
    mappedSimilarImagesDF = pd.read_sql("SELECT * FROM mappedSimilarImages", con=connection)

    # Save to CSV

    utils.writeDfToExcelSheet(pathToSimilarImagesMatchedMapped, mappedSimilarImagesDF, sheet_name='similarImagesMapped')

    # Close DB connection
    connection.close()

    print('[√] Similar images successfully mapped to MaisFlexis records!')
    print(f'Results saved to: {pathToSimilarImagesMatchedMapped}')

    return mappedSimilarImagesDF


def compareSimilarImages(tablesPath, pathToSimilarImagesMatchedMapped):
    """
    Compare similar images within the mapped dataset to identify duplicates and select the best image.

    This function loads the mapped similar images from a SQLite database, standardizes 
    columns, filters duplicates, and identifies the top-ranked image for each `hashValue` 
    group. It records other images in the group to remove and saves the results to Excel.

    Parameters
    ----------
    tablesPath : str
        Path to the SQLite database containing the `mappedSimilarImages` table.
    pathToSimilarImagesMatchedMapped : str
        Path to the Excel file where the matched results will be saved.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing one row per hash group with the following columns:
        - `hashValue`: Hash identifying the group of similar images.
        - `bestImage`: File path of the top-ranked image.
        - `imagesToRemove`: Comma-separated file paths of duplicate images.
        - `toegangsnummer`: Access number from the record (or "niet van toepassing").
        - `inventarisnummer`: Inventory number from the record (or "niet van toepassing").

    Notes
    -----
    - Only images with duplicate `hashValue`s are considered.
    - Assumes that the image with `rank == 1` is the preferred image to keep.
    - Uses filename matching to identify duplicates within a hash group.
    - The final results are saved using `utils.writeDfToExcelSheet`.
    """
    print(f"[INFO] Connecting to database: {tablesPath}")
    conn = sqlite3.connect(tablesPath)

    print("[INFO] Loading data from 'mappedSimilarImages'...")
    df = pd.read_sql("SELECT * FROM mappedSimilarImages", conn)
    conn.close()
    print(f"[INFO] Loaded {len(df)} records from 'mappedSimilarImages'")

    if 'Bestandsnaam' not in df.columns:
        raise KeyError("[ERROR] 'Bestandsnaam' column not found in the loaded data.")

    # Convert CODE / NUMMER naar Int64 (met NaN als ze leeg zijn)
    if 'CODE' in df.columns:
        df['CODE'] = pd.to_numeric(df['CODE'], errors='coerce').astype('Int64')
    if 'NUMMER' in df.columns:
        df['NUMMER'] = pd.to_numeric(df['NUMMER'], errors='coerce').astype('Int64')

    # Rename naar toegangsnummer / inventarisnummer
    rename_map = {'CODE': 'toegangsnummer', 'NUMMER': 'inventarisnummer'}
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    print("[INFO] Stripping extensions from 'Bestandsnaam' column...")
    df['Bestandsnaam'] = df['Bestandsnaam'].str.split('.').str[0]

    print("[INFO] Filtering for duplicate hash groups...")
    original_len = len(df)
    df = df[df['hashValue'].duplicated(keep=False)]
    print(f"[INFO] Reduced from {original_len} to {len(df)} rows with duplicate hashValues")

    matched_rows = []
    print("[INFO] Starting group-by 'hashValue' to find matched images...")

    for i, (hash_val, group) in enumerate(df.groupby('hashValue'), start=1):
        print(f"\n[GROUP {i}] hashValue = {hash_val} | {len(group)} images")

        rank1 = group[group['rank'] == 1]
        if rank1.empty:
            print(" → [SKIP] No rank 1 image in this group")
            continue

        best = rank1.iloc[0]
        best_name = best['Bestandsnaam']
        best_image_path = best['filePath']

        # Convert naar int of "niet van toepassing"
        toegangsnummer = (
            int(best['toegangsnummer']) if pd.notna(best.get('toegangsnummer')) else "niet van toepassing"
        )
        inventarisnummer = (
            int(best['inventarisnummer']) if pd.notna(best.get('inventarisnummer')) else "niet van toepassing"
        )

        print(f" → Best image: {best_image_path} "
              f"(Bestandsnaam: {best_name}, Toegangsnummer: {toegangsnummer}, Inventarisnummer: {inventarisnummer})")

        # Prepare for matching
        best_name_str = str(best_name) if pd.notna(best_name) else ''
        images_to_remove_rows = group[
            (group['Bestandsnaam'] != best_name) &
            (
                group['AANVRAAGNUMMER'].str.contains(best_name_str, na=False) |
                group['NUMMERING_CONVERSIE'].str.contains(best_name_str, na=False)
            )
        ]

        if not images_to_remove_rows.empty:
            images_to_remove = ', '.join(images_to_remove_rows['filePath'].tolist())
            print(f" → [MATCH] {len(images_to_remove_rows)} matching files to remove:")
            print(images_to_remove_rows[['filePath']])
        else:
            images_to_remove = ''
            print(" → [NO MATCH] Nothing matched AANVRAAGNUMMER or NUMMERING_CONVERSIE")

        matched_rows.append({
            'hashValue': hash_val,
            'bestImage': best_image_path,
            'imagesToRemove': images_to_remove,
            'toegangsnummer': toegangsnummer,
            'inventarisnummer': inventarisnummer
        })

    print(f"[INFO] Writing {len(matched_rows)} matched groups to Excel: {pathToSimilarImagesMatchedMapped}")
    similarImagesMatchedDF = pd.DataFrame(matched_rows)
    utils.writeDfToExcelSheet(
        pathToSimilarImagesMatchedMapped,
        similarImagesMatchedDF,
        sheet_name='similarImagesMatched'
    )
    print(f"[√] Done. Output saved to {pathToSimilarImagesMatchedMapped}")

    return similarImagesMatchedDF


def compareExactDuplicates(tablesPath, pathToDescriptionData, pathToExactDuplicatesMatchedMapped):
    """
    Identify exact duplicate images, join with description data, and determine which images to keep or remove.

    This function connects to a SQLite database, loads description data from Excel, joins it 
    with the mapped duplicates table, and identifies the best image to keep within each 
    duplicate group based on `hashValue`. The results are saved to Excel and returned as a DataFrame.

    Parameters
    ----------
    tablesPath : str
        Path to the SQLite database containing the `mappedDuplicates` table.
    pathToDescriptionData : str
        Path to the Excel file containing description data to join with duplicates.
    pathToExactDuplicatesMatchedMapped : str
        Path to the Excel file where the matched exact duplicates results will be saved.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing one row per `hashValue` group with the following columns:
        - `hashValue`: Hash identifying the duplicate group.
        - `bestImage`: File path of the image selected as the best.
        - `imagesToRemove`: Comma-separated file paths of duplicate images to remove.

    Notes
    -----
    - If no exact duplicates are found, an empty DataFrame is returned and saved.
    - Requires the `ID` column to exist in both the database and description Excel file.
    - Assumes the first row of each hash group is the preferred image to keep.
    """

    print(f"[INFO] Connecting to database: {tablesPath}")
    connection = sqlite3.connect(tablesPath)

    # Load description data (Excel) into SQLite table
    print(f"[INFO] Loading description data from: {pathToDescriptionData}")
    maisFlexisDescriptionsDF = pd.read_excel(pathToDescriptionData, engine="openpyxl")
    maisFlexisDescriptionsDF.to_sql('descriptionData', connection, if_exists='replace', index=False)

    # Create joined table with matched duplicates and description data
    cursor = connection.cursor()
    create_table_sql = """
    DROP TABLE IF EXISTS exactDuplicateImagesMatched;
    CREATE TABLE exactDuplicateImagesMatched AS
    SELECT m.*, d.*
    FROM mappedDuplicates m
    LEFT JOIN descriptionData d ON m.ID = d.ID;
    """
    cursor.executescript(create_table_sql)
    connection.commit()
    print("[INFO] Loaded matched exact duplicates with descriptions from DB.")

    exactDuplicatesMatchedDF = pd.read_sql("SELECT * FROM exactDuplicateImagesMatched", con=connection)
    connection.close()

    if exactDuplicatesMatchedDF.empty:
        print("[WARNING] No matched exact duplicates found!")
        # Save empty DataFrame to Excel for consistency
        utils.similarImagesMatchedDF(pathToExactDuplicatesMatchedMapped, exactDuplicatesMatchedDF, sheet_name='exactDuplicatesMatched')
        return exactDuplicatesMatchedDF

    print(f"[INFO] Processing {len(exactDuplicatesMatchedDF)} matched exact duplicates...")

    # We expect 'hashValue', 'filePath', 'Bestandsnaam' columns to exist from mappedDuplicates
    if 'hashValue' not in exactDuplicatesMatchedDF.columns or 'filePath' not in exactDuplicatesMatchedDF.columns:
        raise KeyError("[ERROR] 'hashValue' and/or 'filePath' columns are missing in the exact duplicates data.")

    results = []

    # Group by hashValue (duplicates)
    for hash_val, group in exactDuplicatesMatchedDF.groupby('hashValue'):
        # Pick arbitrary one as best image (e.g., first row)
        best_row = group.iloc[0]
        best_image = best_row['filePath']

        # All others are to remove
        images_to_remove_list = group['filePath'].iloc[1:].tolist()
        images_to_remove = ', '.join(images_to_remove_list)

        print(f"\n[GROUP] hashValue={hash_val} | total={len(group)} images")
        print(f" → Best image: {best_image}")
        if images_to_remove_list:
            print(f" → Images to remove ({len(images_to_remove_list)}): {images_to_remove}")
        else:
            print(" → No images to remove in this group (only one image)")

        results.append({
            'hashValue': hash_val,
            'bestImage': best_image,
            'imagesToRemove': images_to_remove
        })

    resultDF = pd.DataFrame(results)
    utils.writeDfToExcelSheet(pathToExactDuplicatesMatchedMapped, resultDF, sheet_name='exactDuplicatesMatched')
    print(f"[√] Done. Output saved to: {pathToExactDuplicatesMatchedMapped}")

    return resultDF