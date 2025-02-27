import os
import imageCompare
import utils 
import setup

def main():
    
    #### Program Initialization and Setup #### 

    art = utils.asciiArt()
    print(art['logo'], art['title'])
    
    folderPaths, filePaths = utils.createPaths()
    directory, mapping, exifToolPath = setup.getUserInputs(folderPaths)

    # List of paths to the image files to be analysed.
    allImageFilePaths = imageCompare.getAllImageFilePaths(directory=directory)  

    utils.ensureDirectoriesExist(folderPaths)

    # Initializing the SQL tables.
    imageCompare.makeTables(filePaths['tables'])

    ########### Gathering the data ###########
    ##########################################

    initialHashData, exifData =\
    imageCompare.getInitialImageData(allImageFilePaths=allImageFilePaths,
                                     exifToolPath=exifToolPath,
                                     hashPath = filePaths['hashPath'],
                                     exifDataPath = filePaths['exifData'])

    # Filling initial data tables
    imageCompare.fillTablesInitialData(exifData=exifData,
                                       initialHashData=initialHashData,
                                       tablesPath=filePaths['tables'])
    
    # Obtaining the exact duplicates
    imageCompare.getExactDuplicates(tablesPath=filePaths['tables'],
                                    exifToolPath=exifToolPath,
                                    processedDataPath=folderPaths['processedData'])

    ########## Analysis on the data ##########
    ##########################################

    imageCompare.getSimilarImages(tablesPath=filePaths['tables'],
                                  processedDataPath=folderPaths['processedData'])
    # Obtaining the number of unique colors data.
    imageCompare.getUniqueColorsTable(tablesPath=filePaths['tables'],
                                      processedDataPath=folderPaths['processedData'])
    #Ranking the similar images based on resolution and number of unique colors.
    imageCompare.getSimilarImagesRanked(tablesPath=filePaths['tables'],
                                        processedDataPath=folderPaths['processedData']) 
     
    ## Mapping images to MaisFlexis records ##
    ################ *OPTIONAL* ################

    if mapping == 'Y':
        # Parsing the MaisFlexis records.
        imageCompare.getConversionNames(maisFlexisRecords=filePaths['maisFlexisRecords'],
                                        tablesPath=filePaths['tables'])
        # Mapping the images to MaisFlexis Records
        imageCompare.mapDuplicatesToConversionNames(tablesPath=filePaths['tables'], 
                                                    rawDataRecords=filePaths['rawDataRecords'],
                                                    exactDuplicates=filePaths['exactDuplicates'],
                                                    processedDataPath=folderPaths['processedData'])
        
        imageCompare.mapSimilarImagesToConversionNames(tablesPath=filePaths['tables'], 
                                                    rawDataRecords=filePaths['rawDataRecords'],
                                                    similarImages=filePaths['similarImages'],
                                                    processedDataPath=folderPaths['processedData'])
        
if __name__ == "__main__":
    main()
