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
    paths = {
        'tables': os.path.join(parentDir, 'data', 'images.db'),
        'requirements': os.path.join(parentDir, 'requirements.txt'),
        'rawData': os.path.join(parentDir, 'data', 'raw'),
        'processedData': os.path.join(parentDir, 'data', 'processed'),
        'scripts': os.path.join(parentDir, 'scripts'),
        'exifToolWindows': os.path.join(parentDir, 'tools', 'exiftool-13.04_64', 'exiftool.exe')
    }
    return paths

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
