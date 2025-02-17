import os
import imageCompare
import utils 
import setup

def main():
    paths = utils.createPaths()
    directory, exifToolPath = setup.getUserInputs(paths)


    # List of paths to the image files to be analysed.
    allImageFilePaths = imageCompare.getAllImageFilePaths(directory=directory)  

    utils.ensureDirectoriesExist(paths)

    # Initializing the SQL tables.
    imageCompare.makeTables(paths['tables'])

    ### Gathering the data ###
    ##########################pip 
    namesData, descriptionData, initialHashData, exifData =\
    imageCompare.getInitialImageData(allImageFilePaths=allImageFilePaths,
                                     exifToolPath=exifToolPath,
                                     rawDataPath=paths['rawData'],
                                     processedDataPath=paths['processedData'])

    # # Filling initial data tables
    imageCompare.fillTablesInitialData(exifData=exifData,
                                       namesData=namesData,
                                       descriptionData=descriptionData,
                                       initialHashData=initialHashData,
                                       tablesPath=paths['tables'])

    # # Obtaining the exact duplicates
    imageCompare.getExactDuplicates(tablesPath=paths['tables'],
                                    exifToolPath=exifToolPath,
                                    processedDataPath=paths['processedData'])

    ## Analysis on the data ##
    ##########################
    imageCompare.getSimilarImages(tablesPath=paths['tables'],
                                  processedDataPath=paths['processedData'])
    # Obtaining the number of unique colors data
    imageCompare.getUniqueColorsTable(tablesPath=paths['tables'],
                                      processedDataPath=paths['processedData'])
    imageCompare.getSimilarImagesRanked(tablesPath=paths['tables'],
                                        processedDataPath=paths['processedData'])    
    imageCompare.mapDuplicatesToConversionNames(tablesPath=paths['tables'], 
                                                processedDataPath=paths['processedData'])
    imageCompare.mapSimilarImagesToConversionNames(tablesPath=paths['tables'],
                                                   processedDataPath=paths['processedData'])
    imageCompare.mapImagesToDescription(tablesPath=paths['tables'])
if __name__ == "__main__":
    main()
