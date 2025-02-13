import os
import imageCompare
import utils 
import setup

def main():
    paths = utils.createPaths()
    directory, exifToolPath = setup.getUserInputs(paths)


    # List of paths to the image files to be analysed.
    allImageFilePaths = imageCompare.getAllImageFilePaths(directory=directory)  
    #allImageFilePaths = [p for p in allImageFilePaths if basePath + '270' in p]   

    utils.ensureDirectoriesExist(paths)

    # Initializing the SQL tables.
    imageCompare.makeTables(paths['tables'])

    ### Gathering the data ###
    ##########################
    namesData, initialHashData, exifData =\
    imageCompare.getInitialImageData(allImageFilePaths=allImageFilePaths,
                                     exifToolPath=exifToolPath,
                                     rawDataPath=paths['rawData'],
                                     processedDataPath=paths['processedData'])

    # Filling initial data tables
    imageCompare.fillTablesInitialData(exifData=exifData,
                                       namesData=namesData,
                                       initialHashData=initialHashData,
                                       tablesPath=paths['tables'])

    # Obtaining the exact duplicates
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

if __name__ == "__main__":
    main()
