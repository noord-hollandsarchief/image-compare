import os
from openpyxl import load_workbook
import pandas as pd

def createPaths():
    """
    Create and return key project folder and file paths.

    Returns
    -------
    folderPaths : dict
        Paths to important folders like raw data, processed data, scripts, and tools.
    filePaths : dict
        Paths to key files such as databases, Excel/CSV datasets, and processed outputs.
    """
    currentPath = os.getcwd()
    parentDir = os.path.dirname(currentPath)
    folderPaths = {

        'requirements': os.path.join(parentDir, 'requirements.txt'),
        'rawData': os.path.join(parentDir, 'data', 'raw'),
        'processedData': os.path.join(parentDir, 'data', 'processed'),
        'scripts': os.path.join(parentDir, 'scripts'),
        'exifToolWindows': os.path.join(parentDir, 'tools', 'exiftool-13.04_64', 'exiftool.exe')
    }
    
    filePaths = {
        'tables': os.path.join(parentDir, 'data', 'images.db'),
        'maisFlexisRecords': os.path.join(folderPaths['rawData'], 'Data_beeldbank.xlsx'),
        'rawDataRecords': os.path.join(folderPaths['rawData'], 'SCN_BEELDBANK.csv'),
        'maisFlexisDescriptions' : os.path.join(folderPaths['rawData'], 'Beeldcollecties.xlsx'),
        'conversionNames': os.path.join(folderPaths['processedData'], 'conversionNames.csv'),
        'exifData': os.path.join(folderPaths['processedData'], 'exifData.csv'),
        'exactDuplicates': os.path.join(folderPaths['processedData'], 'exactDuplicates.csv'),
        'similarImages': os.path.join(folderPaths['processedData'], 'similarImages.csv'),
        'similarImagesRanked': os.path.join(folderPaths['processedData'], 'similarImagesRanked.csv'),
        'exactDuplicatesMatchedMapped': os.path.join(folderPaths['processedData'], 'exactDuplicatesMatchedMapped.xlsx'),
        'similarImagesMatchedMapped': os.path.join(folderPaths['processedData'], 'similarImagesMatchedMapped.xlsx'),
        'hashPath': os.path.join(folderPaths['processedData'], 'imagesHash.csv')
    }

    return folderPaths, filePaths

def ensureDirectoriesExist(paths):
    """
    Ensure that required directories exist, creating them if they do not.

    Each path in the provided dictionary corresponding to important data folders 
    is checked. If a folder does not exist, it is automatically created to ensure 
    subsequent file operations do not fail.

    Parameters
    ----------
    paths : dict
        Dictionary containing folder paths. Expected keys include:
        - 'rawData': Path to store raw input files.
        - 'processedData': Path to store processed output files.

    Returns
    -------
    None
        This function modifies the filesystem by creating directories but does not return a value.
    """
    for path in [paths['rawData'], paths['processedData']]:
        if not os.path.exists(path):
            os.makedirs(path)


def writeDfToExcelSheet(path, df, sheet_name):
    """Appends a DataFrame to an existing Excel file or creates one."""
    try:
        # Try to load existing workbook
        with pd.ExcelWriter(path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    except FileNotFoundError:
        # If file doesn't exist yet, create it
        with pd.ExcelWriter(path, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def asciiArt():
    """
    Return ASCII art representations used in the image comparison tool.

    This function provides predefined ASCII art as a dictionary. The current keys include:
    - 'logo': A large, decorative ASCII logo for display in the terminal.
    - 'title': A title banner indicating the image comparison tool.

    Returns
    -------
    dict of str
        A dictionary containing ASCII art strings, keyed by descriptive names.
        Example:
            {
                'logo': "<ASCII art logo>",
                'title': "<ASCII art title banner>"
            }
    """
    art = {
        'logo': 
        """                                                   
 #######################@ %######################* 
 #######################@ @%####@@@@############## 
 #######################@ @%####@  @############## 
 #######@@@@@@@@@@######@ @%####@  @@@@@@@######## 
 #######@  @     @@#####@ @#####@  @     @@####### 
 ######*@   @@@@  @%####@ @#####@   @@@:  @####### 
 ######*@  @@#%@  @%####@ @#####@  @@#@@  @%###### 
 ######*@  @%#*@  @@####@ @#####@  @%#*@  @%###### 
 ######*@  @%#*@  @@####@ @#####@  @%#*@  @%###### 
 #######@  @%##@  @%####@ @#####@  @###@  @%###### 
 #######@@@@###@@@@#####@ @#####@@@@###@@@@####### 
 @@@@@@@@@@@@@@@@@@@@@@@@ @@@@@@@@@@@@@@@@@@@@@@@@ 
 +                                               = 
 @@@@@@@@@@@@@@@@@@@@@@@@ @@@@@@@@@@@@%@@@@@@@@@@@ 
 #######################@ @#@ @ @+*##@ @ %@ @ @ @* 
 ########@@@@@@@@@######@ @#@ @ @+*##@ @ @@ @ @ @* 
 ########@       @@#####@ @#@ @ @+*##@ @ @@ @ @ @* 
 ########@@@@@@@  @%####@ @#@ @ @+*##@ @ @@ @ @ @* 
 #######@@@       @@####@ @#@ @ @+*##@ @ @@ @ @ @* 
 #######@  :@@@@  @@####@ @#@ @ @+*##@ @ @@ @ @ @* 
 #######@  @@@@@  @@####@ @#@ @ @+*##@ @ @@ @ @ @* 
 #######@@        @%####@ @#@ @ @+*##@ @ @@ @ @ @* 
 ########@@@@@@@@@@#####@ @#@ @ @+*##@ @ @@ @ @ @* 
 #######################@ @#@ @ @+*##@ @ @@ @ @ @* 
 #######################@ @#% @ @=+##@ @ %@ @ @ @* 
                                                   
    """,
    'title': 
    """
    ========== image comparison tool ==========
          
    """
    }

    return art    