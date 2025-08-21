import os
import subprocess
import sys
import platform
import venv
from utils import createPaths, ensureDirectoriesExist

def createVirtualEnv(envName):
    """
    Create a Python virtual environment with the given name.

    Parameters:
    envName (str): The name of the virtual environment

    Returns:
    str: The absolute path to the created virtual environment
    """
    currentPath = os.getcwd()
    relativeEnvPath = os.path.join(currentPath, '..', envName)
    envPath = os.path.abspath(relativeEnvPath)
    venv.create(envPath, with_pip=True)
    print(f"Virtual environment created in: {envPath}")
    return envPath

def installRequirements(paths, envPath=None):
    """
    Install Python packages listed in a requirements.txt file.

    Parameters:
    paths (dict): A dictionary containing the path to the requirements.txt
    envPath (str, optional): Path to the virtual environment; installs in current environment if None

    Returns:
    None
    """
    if envPath:
        pythonExecutable = os.path.join(envPath, 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(envPath, 'bin', 'python')
        print(f"Using Python executable: {pythonExecutable}")
        subprocess.check_call([pythonExecutable, '-m', 'pip', 'install', '-r', paths["requirements"]])
    else:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', paths["requirements"]])

def getEnvInputs(paths):
    """
    Prompt the user to choose between installing requirements in the current 
    environment or creating a new virtual environment. Calls the appropriate 
    functions based on the user's choice.

    Parameters:
    paths (dict): A dictionary containing the path to the requirements.txt

    Returns:
    None
    """
    envChoice = input("Do you want to install requirements in the current environment or a new virtual environment? (current/new): ").strip().lower()

    while True:
        if envChoice == 'new':
            envName = input("Enter the name for the new virtual environment: ").strip()
            envPath = createVirtualEnv(envName)
            installRequirements(paths=paths, envPath=envPath)
            break
        elif envChoice == 'current':
            installRequirements(paths=paths, envPath=None)
            break
        else:
            print('Invalid choice. Please enter "current" or "new".')
            envChoice = input("Do you want to install requirements in the current environment or a new virtual environment? (current/new): ").strip().lower()

def getUserInputs(paths):
    """
    Prompt the user for input directories, mapping choice, and ExifTool path.

    For non-Windows systems, the user is asked for the ExifTool installation directory.
    For Windows, the default ExifTool path from 'paths' is used.

    Parameters:
    paths (dict): A dictionary containing paths, including default ExifTool path for Windows

    Returns:
    tuple: A tuple containing the list of image directories, mapping choice ('Y'/'N'), and ExifTool path
    """
    print('####################### Program Initialization ###########################')
    print('|------------------------------------------------------------------------|')

    directories = []
    while True:
        directory = input('Enter an images directory (or press Enter to finish): ').strip()
        # stop if empty
        if not directory:
            break
        directories.append(directory)

    mapping = input(
                    'Would you like the output to be mapped to MaisFlexis records? (Y/N)\n\n'
                    'IMPORTANT: This will only work if your mapping files are set up exactly like the fields in the following files:\n'
                    '- data\\raw\\Data_beeldbank_270\n'
                    '- data\\raw\\SCN_BEELDBANK_270\n\n'
                    ).upper()
    
    while mapping not in ('Y', 'N'):
        print('Invalid choice. Please enter "Y" or "N".')
        mapping = input('Would you like the output to be mapped to MaisFlexis records? (Y/N) \n'
                    'IMPORTANT: This will only work if your mapping files are set up exactly like the fields in the following files: \n\
                    - data\\raw\\Data_beeldbank_270\n - data\\raw\\SCN_BEELDBANK_270 \n\n')   
        
    if platform.system() != 'Windows':
        exifToolPath = input('Enter the directory where the ExifTool is installed: ')
    else:
        exifToolPath = paths['exifToolWindows']

    return directories, mapping, exifToolPath

def main():
    paths = createPaths()
    ensureDirectoriesExist(paths)
    getEnvInputs(paths)

if __name__ == "__main__":
    main()
