# image-compare

## Description
This repository contains code to find exact duplicates in a directory of images and rank similar images based on resolution and unique colors using file and image hashing.

**Optional**: The images can also be mapped to MaisFlexis records based on filenames and record IDs, but only if the mapping files are in the correct format (see field descriptions in the first row of each file).

**Note**: This project is a work in progress. A more representative test set will be added soon. The current set lacks similar images.

## Data

Two excel files are used to link images to MaisFlexis record ID information.

These are:

1. Data_beeldbank_270 (located in `data/raw/Data_beeldbank/270`)
   - Contains MaisFlexis fields at the record ID level.
2. SCN_BEELDBANK_270 (located in `data/raw/SCN_BEELDBANK/270`)
   - Contains the MaisFlexis Record IDs and filenames of the images that are linked to MaisFlexis.
   
The field descriptions can be found in the first row of each respective file.
The queries used in the analysis are also included and can be found in the `data/queries` folder.

## Scripts
`imageCompare.py`: Contains the core functions of the image analysis pipeline. 
It calculates, collects, transforms, and maps image data, then saves the results as SQL tables in a `.db` file and `.csv` files.

`setup.py`: Installs the necessary dependencies, either in the current environment or a new virtual environment, to ensure the pipeline functions correctly.

`utils.py`: Manages file paths, helping to set up and reference directories and files across the project without hardcoding them in multiple places.

`main.py`: The entry point of the project. Running this script triggers the entire pipeline, executing functions from the other scripts.

---
## Table of Contents
- [Install Python](#install-python)
   - [Windows](#windows)
   - [macOS](#macos)
   - [Linux](#linux)
- [Install Git](#install-git)
   - [Windows](#windows-1)
   - [macOS](#macos-1)
   - [Linux](#linux-1)
- [Install ExifTool](#install-exiftool)
   - [Windows](#windows-2)
   - [macOS and Linux](#macos-and-linux)
- [Installation and usage of the repository](#installation-and-usage-of-the-repository)
   - [Windows](#windows-3)
   - [macOS and Linux](#macos-and-linux-1)
- [Features](#features)
---
## Install Python
If you don’t have Python installed already, make sure to download and install it using one of the links provided below.
You can choose to download Python from the official website or directly from the Microsoft Store, depending on your preference.

1. Download python
   - **From the Official Python Website**: Visit the Python [download page](https://www.python.org/downloads/) to get the version you need. Make sure to choose the correct installer for your operating system (Windows, macOS, or Linux).
   - **From the Microsoft Store**: Alternatively, you can download Python from the Python [product page](https://apps.microsoft.com/detail/9PNRBTZXMB4Z?hl=neutral&gl=NL&ocid=pdpshare) on the Windows Store.
2. Select the version of Python you wish to install (version 3.13.2 is highly recommended).
4. Click on the download link for your operating system (Windows, macOS, or Linux).

**Note**: This project was developed using Python 3.13.2. Therefore it is not guaranteed to work with other versions of Python.

### Windows
4. Run the downloaded installer.
5. **Important:** Make sure to check the box that says "Add Python to PATH".
6. Click "Install Now" and follow the prompts.
7. **Verify the installation**: Open Command Prompt and type `python --version` to check the installed version of Python.

### macOS
4. Open the downloaded `.pkg` file.
5. Follow the installation instructions.
6. Verify the installation by opening Terminal and typing `python3 --version`.

### Linux
4. Open Terminal.
5. Use the package manager to install Python. For example, on Ubuntu:
   ```bash
   sudo apt update
   sudo apt install python3
   ```

---
## Install Git
If you don’t have Git installed already, make sure to download and install it using the instructions provided below. 
### Windows
For Windows users, you can download and install Git using the following steps:
1. **Download Git**:
   Get the latest version of Git from the official website: [Git Download](https://git-scm.com/downloads).
2. **Run the Installer**:
   Run the downloaded installer and follow the prompts. It is recommended to choose the default options.
3. **Verify Installation**:
   Open Command Prompt and run:
   ```cmd
   git --version
   ```

### macOS
1. **Install Homebrew**: (if not already installed) Open Terminal and run:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. **Install Git**: Run the following command in Terminal:
   ```bash
   brew install git
   ```

4. **Verify Installation**: To check if git is installed correctly, run the following command:
   ```bash
   git --version
   ```

### Linux
For Linux users, you can install Git using your package manager. For example, on Ubuntu:

1. **Update Package List**: Open Terminal and run:
   ```bash
   sudo apt-get update
   ```
3. **Install Git**: To install Git, run the command:
   ```bash
   sudo apt-get install git
   ```
5. **Verify Installation**: To verify if git has been installed correctly, run the command:
   ```bash
   git --version
   ```

## Install ExifTool 
### Windows
For Windows users, the ExifTool executable is already prepared and ready to use. 
The files are included in the tools folder of this repository.

### macOS and Linux
1. **Download ExifTool**: Get the latest version of ExifTool by Phil Harvey from the official website: [ExifTool Download.](https://exiftool.org/)
2. **Setting it up**: Detailed installation instructions are available here: [ExifTool Installation.](https://exiftool.org/install.html)
   
**Note**:
The integration of ExifTool into this program has been tested exclusively with the Windows executable on a Windows machine, using ExifTool version 13.04_64 (included in the tools folder of the repo). Compatibility with other operating systems has not been verified and is not guaranteed at this time.

---
## Installation and usage of the repository
Below are step-by-step instructions on how to install and set up the project using examples for both Windows and macOS/Linux. For both Windows and macOS/Linux, two different methods are described each with their own example. 

---
## Windows
Create and navigate to the directory where the repository will be saved.

To do this, first open the command-line interface.
Then check if the following directory exists and create it if it doesn’t:
```bash
if not exist %USERPROFILE%\Documents\GitHub mkdir %USERPROFILE%\Documents\GitHub
```
Navigate to the directory:
```bash
cd %USERPROFILE%\Documents\GitHub
```
From here clone the repository.
```bash
git clone https://github.com/noord-hollandsarchief/image-compare.git
```

### Method 1
Using the command-line interface, navigate to the project directory and install the dependencies.
```bash
cd %USERPROFILE%\Documents\GitHub\image-compare\ && pip install -r requirements.txt
```
**Note:** 
If pip is not recognized by your machine, try restarting your command-line interface.
If that doesn’t resolve the issue, run the Python installer again, select “Repair”, and make sure to check the box that says “Add Python to environment variables” in the “Advanced Options” section.

Navigate to the scripts directory and run main.py.
```bash
cd %USERPROFILE%\Documents\GitHub\image-compare\scripts && python main.py
```
Follow the prompts:
- Enter the directory of images to be analyzed:

Test directory included in this repo:
```bash
..\testImages
```
The pipeline will then start running.

---

### Method 2:
Alternatively, the `setup.py` file can be run to install the required packages in either your current or a new virtual environment. For this we have to 
open the command-line interface, navigate to the scripts directory and run setup.py.
```bash.
cd %USERPROFILE%\Documents\GitHub\image-compare\scripts && python setup.py
```

Follow the prompts:
- It will ask you if you want to create a new virtual environment or use the current one.
- If you create a new virtual enviornment you have to specify a name for the environment (for example: .venv).
- Then it will install the packages listed in `requirements.txt` in this environment.
  
Activate the virtual environment and run the main.py script:
```bash
cd ..\ && .\.venv\Scripts\activate
```
```bash
cd scripts && python main.py
```
Follow the prompt:

- Enter the directory of images to be analyzed:

Test directory included in this repo:
```bash
..\testImages
```
The pipeline will then start running.

---
## macOS and Linux
Create and navigate to the directory where the repository will be saved.

To do this, first open the command-line interface.
Then check if the following directory exists and create it if it doesn’t:

```bash
[ ! -d "$HOME/Documents/GitHub" ] && mkdir -p "$HOME/Documents/GitHub"
```
Navigate to the directory:
```bash
cd "$HOME/Documents/GitHub"
```
From here clone the repository.
```bash
git clone https://github.com/noord-hollandsarchief/image-compare.git
```

### Method 1: 
Using the command-line interface, navigate to the project directory and install the dependencies.
```bash
cd ~/Documents/GitHub/image-compare/ && pip install -r requirements.txt
```
Navigate to the scripts directory and run main.py.
```bash
cd ~/Documents/GitHub/image-compare/scripts && python main.py
```
Follow the prompts:
- Enter the directory of images to be analyzed:

Test directory included in this repo:
```bash
../testImages/
```
- Enter the directory where ExifTool is installed:
  
The pipeline will then start running.

---

### Method 2:
Alternatively, the `setup.py` file can be run to install the required packages in either your current or a new environment. For this we have to open the command-line interface, navigate to the scripts directory and run setup.py
```bash
cd ~/Documents/GitHub/image-compare/scripts && python setup.py
```
Follow the prompts:
- It will ask you if you want to create a new environment or use the current one.
- If you create a new virtual enviornment you have to specify a name for the environment (example: .venv).
- Then it will install the packages listed in `requirements.txt` in this environment.

Activate the environment and run the main.py script:
```bash
cd .. && source .venv/bin/activate
```
```bash
cd scripts && python main.py
```
Follow the prompts:
- Enter the directory of images to be analyzed:

Test directory included in this repo:
```bash
../testImages
```
- Enter the directory where ExifTool is installed: 

The pipeline will then start running.

---

## Features
This project provides the following features:
- **Find exact duplicates** A combined approach of file hashing and image hashing.
- **Find similar images** A combined approach of file hashing and image hashing followed by image ranking based on resolution and the number of unique colors.
- **Link images to MaisFlexis record ID information** Based on record ID and filename of images that are linked to MaisFlexis.
- **Provides lists of images to remove** Based on arbitrary choice for exact duplicates and highest rank for similar images. 
