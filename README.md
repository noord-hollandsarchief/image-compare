# image_compare

## Description
This repository contains code that can find exact duplicates in a directory of images and rank similar images based on resolution and the number of unique colors. The exact duplicates and similar images are identified using a combined approach of file hashing and image hashing. Additionally, the images are (if possible) linked to MaisFlexis based on their accession number and inventory number. This information is specified in the path of the images and is also present in the corresponding MaisFlexis record. The corresponding duplicate/similar images that are not linkable by this information are connected through the matching hash values. The packages required to run the scripts are listed in `requirements.txt`. **Note: This is a work in progress and will continue to be improved.**

## Table of Contents
- Installation
- Usage
- Features

## Installation
Below are step-by-step instructions on how to install and set up the project using examples. This can of course be adjusted to your liking.
In this example we first create and navigate to the directory where we want to save the repository. 

**Windows:**
```bash
mkdir %USERPROFILE%\Documents\GitHub
cd %USERPROFILE%\Documents\GitHub
```
**macOS/Linux:**
```bash
mkdir -p ~/Documents/GitHub
cd ~/Documents/GitHub
```
### Clone the repository
```bash
git clone https://github.com/noord-hollandsarchief/image_compare.git
```
### Install ExifTool
To use ExifTool for extracting EXIF metadata, follow these steps:
1. **Download ExifTool**:
   Get the latest version of ExifTool by Phil Harvey from the official website: [ExifTool Download.](https://exiftool.org/)
2. **Installation Instructions**:
   Detailed installation instructions are available here:[ ExifTool Installation.](https://exiftool.org/install.html )
**Note**: The integration of ExifTool into this program has only been tested with the Windows executable on a Windows machine. Compatibility with other operating systems is not guaranteed at this time.

### Usage
Below are two examples of how to run the script:

## First method
### Navigate to the scripts directory:
**Windows:**
```bash
cd %USERPROFILE%\Documents\GitHub\image_compare\scripts
```

**macOS/Linux:**
```bash
cd ~/Documents/GitHub/image_compare/scripts
```

### Install dependencies:
```bash
pip install -r requirements.txt
```

### Run the main.py script:
```bash
python main.py
```
### Follow the prompts:
- Enter the directory of images to be analyzed.:
- Enter the directory where ExifTool is installed: 
- Then it will install the packages listed in `requirements.txt` in this environment.

## Second method
Alternatively, the `setup.py` file can be run to install the required packages in either your current or a new environment. This is done as follows:
### Navigate to the scripts directory:
**Windows:**
```bash
cd %USERPROFILE%\Documents\GitHub\image_compare\scripts
```
**macOS/Linux:**
```bash
cd ~/Documents/GitHub/image_compare/scripts
```

### Install dependencies in a specific environment:
```bash
python setup.py
```
### Follow the prompts:
- It will ask you if you want to create a new environment or use the current one.
- If you create a new enviornment you have to specify a name.
- Then it will install the packages listed in `requirements.txt` in this environment.

### Activate the environment and run the main.py script:
**Windows:**
```bash
cd ..\
.\yourenv\Scripts\activate
cd scripts
python main.py

```
**macOS/Linux:**
```bash
cd ..
source yourenv/bin/activate
cd scripts
python main.py
```
### Follow the prompts:
- Enter the directory of images to be analyzed.:
- Enter the directory where ExifTool is installed: 
- Then it will install the packages listed in `requirements.txt` in this environment.

## Features
This project provides the following features:
- **Find exact duplicates** in a specified directory using a combined approach of file hashing and image hashing.
- **Rank similar images** based on resolution and the number of unique colors.
- **Link images to MaisFlexis** based on their accession number and inventory number, if possible.
- **Connect duplicate/similar images that are not linkable by accession and inventory number** through matching hash values between linked and non-linked images.

