# image_compare

## Description
This repository contains code that can find exact duplicates in a directory of images and rank similar images based on resolution and the number of unique colors. The exact duplicates and similar images are identified using a combined approach of file hashing and image hashing. Additionally, the images are (if possible) linked to MaisFlexis based on their accession number and inventory number. This information is specified in the path of the images and is also present in the corresponding MaisFlexis record. The corresponding duplicate/similar images that are not linkable by this information are connected through the matching hash values. The packages required to run the scripts are listed in `requirements.txt`. **Note: This is a work in progress and will continue to be improved.**

## Table of Contents
- Installation
- Usage
- Features

## Installation
Step-by-step instructions on how to install and set up your project.

### Clone the repository
```bash
git clone https://github.com/noord-hollandsarchief/image_compare.git
```

### Usage
Below are two examples of how to run the script:

## First method
```bash
# Navigate to the scripts directory:
cd C:\Users\your_username\Documents\GitHub\image_compare\scripts
```

### Install dependencies:
```bash
pip install -r requirements.txt
```

### Run the script:
```bash
python main.py
```

## Second method
Alternatively, the `setup.py` file can be run to install the required packages in either your current or a new environment. This is done as follows:

### Navigate to the scripts directory:
```bash
cd C:\Users\your_username\Documents\GitHub\image_compare\scripts
```

### Install dependencies in a specific environment:
```bash
python setup.py
```

### Follow the prompts:
- It will ask you if you want to create a new environment or use the current one.
- Then it will install the packages listed in `requirements.txt` in this environment.

### Activate the environment and run the main.py script:
```bash
../yourEnvironment/Scripts/activate
cd scripts
python main.py
```

## Features
This project provides the following features:
- **Find exact duplicates** in a specified directory using a combined approach of file hashing and image hashing.
- **Rank similar images** based on resolution and the number of unique colors.
- **Link images to MaisFlexis** based on their accession number and inventory number, if possible.
- **Connect duplicate/similar images that are not linkable by accession and inventory number** through matching hash values between linked and non-linked images.

