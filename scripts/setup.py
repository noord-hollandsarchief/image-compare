import os
import subprocess
import sys
from utils import createPaths, ensureDirectoriesExist

def createVirtualEnv(envName):
    """
    Create a virtual environment with the given name.

    Parameters:
    envName (str): The name of the virtual environment

    Returns:
    str: The path to the created virtual environment
    """
    currentPath = os.getcwd()
    relativeEnvPath = os.path.join(currentPath, '..', envName)
    envPath = os.path.abspath(relativeEnvPath)
    subprocess.call([sys.executable, '-m', 'venv', envPath])
    print(f"Virtual environment created in: {envPath}")
    return envPath

def installRequirements(paths, envPath=None):
    """
    Install the packages listed in the requirements.txt

    Parameters:
    paths (dict): A dictionary containing the paths
    envPath (str): Path to the virtual environment directory

    Returns:
    None
    """
    if envPath:
        activateScript = os.path.join(envPath, 'Scripts', 'activate') if os.name == 'nt' else os.path.join(envPath, 'bin', 'activate')
        command = f'"{activateScript}" && pip install -r "{paths["requirements"]}"'
        subprocess.call(command, shell=True)
    else:
        command = f'pip install -r "{paths["requirements"]}"'
        subprocess.call(command, shell=True)


def getEnvInputs(paths):
    """
    This function prompts the user to choose between installing requirements in the current environment or creating a new virtual environment.
    Based on the user's choice, it calls the appropriate functions to create a virtual environment and install the requirements.

    Parameters:
    paths (dict): A dictionary containing the paths

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

def getUserInputs():
    """
    This function prompts the user to enter the images directory and the directory where the ExifTool is installed.

    Parameters:
    None

    Returns:
    """
    
    directory = input('Enter the images directory: ')
    exifToolPath = input('Enter the directory where the ExifTool is installed: ')

    return directory, exifToolPath

def main():
    paths = createPaths()
    ensureDirectoriesExist(paths)
    getEnvInputs(paths)

if __name__ == "__main__":
    main()
