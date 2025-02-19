# image-compare

## Description
This repository contains code that can find exact duplicates in a directory of images and rank similar images based on resolution and the number of unique colors. The exact duplicates and similar images are identified using a combined approach of file hashing and image hashing. Additionally, the images are (if possible) linked to MaisFlexis based on their accession number and inventory number. This information is specified in the path of the images and is also present in the corresponding MaisFlexis record. The corresponding duplicate/similar images that are not linkable by this information are connected through the matching hash values. The packages required to run the scripts are listed in `requirements.txt`. 

**Note**: This is a work in progress and will continue to be improved.

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
1. Visit the [download page](https://www.python.org/downloads/) on the official Python website.
2. Select the version of Python you wish to install (version 3.13.2 is highly recommended).
3. Click on the download link for your operating system (Windows, macOS, or Linux).

**Note**: This project was developed using Python 3.13.2. Therefore it is not guaranteed to work with other versions of Python.

### Windows
4. Run the downloaded installer.
5. Make sure to check the box that says "Add Python to PATH".
6. Click "Install Now" and follow the prompts.

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
1. **Install Homebrew** (if not already installed):
   Open Terminal and run:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. **Install Git** (Run the following command in Terminal:
   ```bash
   brew install git
   ```

4. **Verify Installation** To check if git is installed correctly, run the following command:
   ```bash
   git --version
   ```

### Linux
For Linux users, you can install Git using your package manager. For example, on Ubuntu:

1. **Update Package List**: Open Terminal and run:
   ```bash
   sudo apt-get update
   ```
2. **Install Git** Run:
   ```bash
   sudo apt-get install git
   ```
3. **Verify Installation** Run:
   ```bash
   git --version
   ```

## Install ExifTool 
### Windows
For Windows users, the ExifTool executable is already prepared and ready to use. 
The files are included in the tools folder of this repository.

### macOS and Linux
1. **Download ExifTool**:
   Get the latest version of ExifTool by Phil Harvey from the official website: [ExifTool Download.](https://exiftool.org/)
2. **Setting it up**:
   Detailed installation instructions are available here: [ExifTool Installation.](https://exiftool.org/install.html)
   
**Note**:
The integration of ExifTool into this program has been tested exclusively with the Windows executable on a Windows machine, using ExifTool version 13.04_64 (included in the tools folder of the repo). Compatibility with other operating systems has not been verified and is not guaranteed at this time.

---
## Installation and usage of the repository
Below are step-by-step instructions on how to install and set up the project using examples for both Windows and macOS/Linux. For both Windows and macOS/Linux, two different methods are described each with their own example. 

---
### Windows
Create and navigate to the directory where the repository will be saved.
```bash
mkdir %USERPROFILE%\Documents\GitHub && cd %USERPROFILE%\Documents\GitHub
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
Navigate to the scripts directory and run main.py.
```bash
cd %USERPROFILE%\Documents\GitHub\image-compare\scripts && python main.py
```
Follow the prompts:
- Enter the directory of images to be analyzed:

Test directory included in this repo:
```bash
..\testImages\270
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
- If you create a new enviornment you have to specify a name.
- Then it will install the packages listed in `requirements.txt` in this environment.
  
Activate the virtual environment and run the main.py script:
```bash
cd ..\ && .\yourvenv\Scripts\activate
```
```bash
cd scripts && python main.py
```
Follow the prompt:

- Enter the directory of images to be analyzed:

Test directory included in this repo:
```bash
..\testImages\270
```
The pipeline will then start running.

---
### macOS and Linux
Open the command-line interface.
Create and navigate to the directory where the repository will be saved.
```bash
mkdir ~Documents/GitHub && cd ~Documents/GitHub
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
../testImages/270
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
- If you create a new enviornment you have to specify a name.
- Then it will install the packages listed in `requirements.txt` in this environment.

Activate the environment and run the main.py script:
```bash
cd .. && source yourenv/bin/activate
```
```bash
cd scripts && python main.py
```
Follow the prompts:
- Enter the directory of images to be analyzed:

Test directory included in this repo:
```bash
../testImages/270
```
- Enter the directory where ExifTool is installed: 

The pipeline will then start running.

---

## Features
This project provides the following features:
- **Find exact duplicates** in a specified directory using a combined approach of file hashing and image hashing.
- **Rank similar images** based on resolution and the number of unique colors.
- **Link images to MaisFlexis** based on their accession number and inventory number, if possible.
- **Connect duplicate/similar images that are not linkable by accession and inventory number** through matching hash values between linked and non-linked images.

