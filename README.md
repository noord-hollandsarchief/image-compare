# image-compare

## Description
This repository contains code that can find exact duplicates in a directory of images and rank similar images based on resolution and the number of unique colors. The exact duplicates and similar images are identified using a combined approach of file hashing and image hashing. Additionally, the images are (if possible) linked to MaisFlexis based on their accession number and inventory number. This information is specified in the path of the images and is also present in the corresponding MaisFlexis record. The corresponding duplicate/similar images that are not linkable by this information are connected through the matching hash values. The packages required to run the scripts are listed in `requirements.txt`. 

**Note**: This is a work in progress and will continue to be improved.

---
## Table of Contents
- [Install ExifTool](#install-exiftool)
- [Installation and usage of the repository](#installation-and-usage-of-the-repository)
   - [Windows](#windows)
   - [macOS and Linux](#macos-and-linux)
- [Features](#features)
---
## Install ExifTool 
### Windows
For Windows users, the ExifTool executable is already prepared and included in the tools folder of this repository.

### macOS and Linux
1. **Download ExifTool**:
   Get the latest version of ExifTool by Phil Harvey from the official website: [ExifTool Download.](https://exiftool.org/)
2. **Setting it up**:
   Detailed installation instructions are available here:[ ExifTool Installation.](https://exiftool.org/install.html )
   
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
From here clone the repository
```bash
git clone https://github.com/noord-hollandsarchief/image-compare.git
```

### Method 1
Navigate to the project directory and install the dependencies.
```bash
cd %USERPROFILE%\Documents\GitHub\image-compare\ && pip install -r requirements.txt
```
Navigate to the scripts directory and run main.py
```bash
cd %USERPROFILE%\Documents\GitHub\image-compare\scripts && python main.py
```
Follow the prompts:
- Enter the directory of images to be analyzed.:

Test directory included in this repo:
```bash
%USERPROFILE%\Documents\GitHub\image-compare\testImages\270
```
The pipeline will then start running.

---

### Method 2:
Alternatively, the `setup.py` file can be run to install the required packages in either your current or a new environment. For this we have to navigate to the scripts directory and run setup.py
```bash
cd %USERPROFILE%\Documents\GitHub\image-compare\scripts && python setup.py
```

Follow the prompts:
- It will ask you if you want to create a new environment or use the current one.
- If you create a new enviornment you have to specify a name.
- Then it will install the packages listed in `requirements.txt` in this environment.
  
Activate the environment and run the main.py script:
```bash
cd ..\ && .\yourenv\Scripts\activate
```
```bash
cd scripts && python main.py
```
Follow the prompt:

- Enter the directory of images to be analyzed:

Test directory included in this repo:
```bash
%USERPROFILE%\Documents\GitHub\image-compare\testImages\270
```
The pipeline will then start running.

---
### macOS and Linux
Create and navigate to the directory where the repository will be saved.
```bash
mkdir ~Documents/GitHub && cd ~Documents/GitHub
```
From here clone the repository.
```bash
git clone https://github.com/noord-hollandsarchief/image-compare.git
```

### Method 1: 
Navigate to the project directory and install the dependencies.
```bash
cd ~/Documents/GitHub/image-compare/ && pip install -r requirements.txt
```
Navigate to the scripts directory and run main.py
```bash
cd ~/Documents/GitHub/image-compare/scripts && python main.py
```
Follow the prompts:
- Enter the directory of images to be analyzed.:

Test directory included in this repo:
```bash
~Documents/GitHub/image-compare/testImages/270
```
- Enter the directory where ExifTool is installed: 
The analysis will then be done.
---

### Method 2:
Alternatively, the `setup.py` file can be run to install the required packages in either your current or a new environment. For this we have to navigate to the scripts directory and run setup.py
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
- Enter the directory of images to be analyzed.:

Test directory included in this repo:
```bash
~Documents/GitHub/image-compare/testImages/270
```
- Enter the directory where ExifTool is installed: 
The analysis will then be done.
---

## Features
This project provides the following features:
- **Find exact duplicates** in a specified directory using a combined approach of file hashing and image hashing.
- **Rank similar images** based on resolution and the number of unique colors.
- **Link images to MaisFlexis** based on their accession number and inventory number, if possible.
- **Connect duplicate/similar images that are not linkable by accession and inventory number** through matching hash values between linked and non-linked images.

