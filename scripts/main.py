import os
import imageCompare
import utils 
import setup

def main():
    folderPaths, filePaths = utils.createPaths()
    print()
    directory, exifToolPath = setup.getUserInputs(folderPaths)


    # List of paths to the image files to be analysed.
    allImageFilePaths = imageCompare.getAllImageFilePaths(directory=directory)  

    utils.ensureDirectoriesExist(folderPaths)

    # Initializing the SQL tables.
    imageCompare.makeTables(filePaths['tables'])

    ### Gathering the data ###
    ##########################pip 
    initialHashData, exifData =\
    imageCompare.getInitialImageData(allImageFilePaths=allImageFilePaths,
                                     exifToolPath=exifToolPath,
                                     hashPath = filePaths['hashPath'],
                                     exifDataPath = filePaths['exifData'])

    # # Filling initial data tables
    imageCompare.fillTablesInitialData(exifData=exifData,
                                       initialHashData=initialHashData,
                                       tablesPath=filePaths['tables'])

    # # Obtaining the exact duplicates
    imageCompare.getExactDuplicates(tablesPath=filePaths['tables'],
                                    exifToolPath=exifToolPath,
                                    processedDataPath=folderPaths['processedData'])

    ## Analysis on the data ##
    ##########################
    imageCompare.getSimilarImages(tablesPath=filePaths['tables'],
                                  processedDataPath=folderPaths['processedData'])
    # Obtaining the number of unique colors data
    imageCompare.getUniqueColorsTable(tablesPath=filePaths['tables'],
                                      processedDataPath=folderPaths['processedData'])
    
    imageCompare.getSimilarImagesRanked(tablesPath=filePaths['tables'],
                                        processedDataPath=folderPaths['processedData'])  
    # The parsed maisFlexisRecords
    imageCompare.getConversionNames(maisFlexisRecords=filePaths['maisFlexisRecords'],
                                    tablesPath=filePaths['tables'])

    #imageCompare.getDescriptionData(maisFlexisDescriptions=filePaths['maisFlexisRecords'],
    #                                tablesPath=filePaths['tables']) 

    imageCompare.mapDuplicatesToConversionNames(tablesPath=filePaths['tables'], 
                                                processedDataPath=folderPaths['processedData'])
    
    imageCompare.mapSimilarImagesToConversionNames(tablesPath=filePaths['tables'],
                                                   processedDataPath=folderPaths['processedData'])
    
    imageCompare.mapImagesToDescription(maisFlexisDescriptions=filePaths['maisFlexisRecords'],
                                        tablesPath=filePaths['tables'])
    
if __name__ == "__main__":
    main()
