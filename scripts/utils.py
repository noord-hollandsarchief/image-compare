import os

def createPaths():
    """
    This function sets up the necessary paths for the project.

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
        'exifData': os.path.join(folderPaths['processedData'], 'exifData.csv'),
        'maisFlexisRecords': os.path.join(folderPaths['rawData'], 'Data_beeldbank.xlsx'),
        'maisFlexisDescriptions': os.path.join(folderPaths['rawData'], 'EB_DB_ZieOOK.csv'),
        'hashPath': os.path.join(folderPaths['processedData'], 'imagesHash.csv')
    }

    return folderPaths, filePaths

def ensureDirectoriesExist(paths):
    """
    This function ensures that the required directories exist.

    Parameters:
    paths (dict): A dictionary containing the paths

    Returns:
    None
    """
    for path in [paths['rawData'], paths['processedData']]:
        if not os.path.exists(path):
            os.makedirs(path)
