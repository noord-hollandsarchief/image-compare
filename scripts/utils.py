import os

def createPaths():
    """
    Sets up and returns the necessary project paths for directories and important files.

    Parameters:
    None

    Returns:
    dict: A dictionary containing the paths
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
        'maisFlexisRecords': os.path.join(folderPaths['rawData'], 'Data_beeldbank_270.xlsx'),
        'rawDataRecords': os.path.join(folderPaths['rawData'], 'SCN_BEELDBANK_270.csv'),
        'exifData': os.path.join(folderPaths['processedData'], 'exifData.csv'),
        'exactDuplicates': os.path.join(folderPaths['processedData'], 'exactDuplicates.csv'),
        'similarImages': os.path.join(folderPaths['processedData'], 'similarImages.csv'),
        'similarImagesRanked': os.path.join(folderPaths['processedData'], 'similarImagesRanked.csv'),
        'exactDuplicatesMapped': os.path.join(folderPaths['processedData'], 'exactDuplicatesMapped.csv'),
        'similarImagesMapped': os.path.join(folderPaths['processedData'], 'similarImagesMapped.csv'),
        'hashPath': os.path.join(folderPaths['processedData'], 'imagesHash.csv')
    }

    return folderPaths, filePaths

def ensureDirectoriesExist(paths):
    """
    Checks if the required directories exist; if not, it creates them.

    Parameters:
    paths (dict): A dictionary containing the paths

    Returns:
    None
    """
    for path in [paths['rawData'], paths['processedData']]:
        if not os.path.exists(path):
            os.makedirs(path)


def asciiArt():

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