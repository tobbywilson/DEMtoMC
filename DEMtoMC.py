# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 17:55:53 2020

@author: Toby
"""

#Data import and manipulation
import numpy as np
import pandas as pd

#Data visualisation
import matplotlib.pyplot as plt

#logging
import sys
import logging
import logging.handlers

#miscellaneous file functions
import os

#GUI
from PySide2 import QtCore, QtWidgets, QtGui

#Geoprocessing
from osgeo import gdal
gdal.AllRegister()

#Minecraft world editing
import anvil

#Random number generation
import random

#Execution Timing
import time

quant = 0.5

def flex_round(number):
    return round(number*(1/quant))/(1/quant)



blockList = [
'stone',
'grass_block',
'concrete',
'dirt',
'sand',
'gravel',
'ice',
'sandstone',
'planks',
'snow_block',
'bricks',
'bedrock',
'soul_sand',
'grass',
'water'
]

half_blockList = [
'stone_slab',
'oak_slab',
'sandstone_slab',
'brick_slab',
]

tree_list = [
'oak',
'birch',
'spruce',
'acacia',
'dark_oak',
'jungle'
]

bedrock = anvil.Block('minecraft','bedrock')
water = anvil.Block('minecraft','water')


logFormat = "%(asctime)s - %(levelname)s: %(message)s"

logToFile = logging.handlers.RotatingFileHandler('DEMtoMC.log',mode='a',maxBytes=5*1024*1024,backupCount=3)
logToFile.setLevel(logging.DEBUG)

logToConsole = logging.StreamHandler(sys.stdout)
logToConsole.setLevel(logging.INFO)


logging.basicConfig(level=logging.DEBUG,
                    format=logFormat,
                    handlers=[logToFile,logToConsole])

logger = logging.getLogger('DEMtoMC')


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.logger = QtWidgets.QPlainTextEdit(parent)
        self.logger.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.logger.appendPlainText(msg)


class win(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.threadpool = QtCore.QThreadPool()

        self.setWindowTitle('DEMtoMC')
        self.setGeometry(300,200,500,300)

        self.createGridLayout()
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.ioBox)
        vbox.addWidget(self.settingsBox)
        vbox.addWidget(self.buttonBox)
        #vbox.addWidget(self.logBox)
        self.setLayout(vbox)

    def createGridLayout(self):
        self.buttonBox = QtWidgets.QGroupBox("")
        self.settingsBox = QtWidgets.QGroupBox("Settings")
        self.ioBox = QtWidgets.QGroupBox("File")
        self.forestBox = QtWidgets.QGroupBox("Forest")
        self.classifierBox = QtWidgets.QGroupBox("Classifier Raster Dictionary")
        self.featuresBox = QtWidgets.QGroupBox("Features Raster Dictionary")
        #self.logBox = QtWidgets.QGroupBox("Execution Log")

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.settingsLayout = QtWidgets.QGridLayout()
        self.ioLayout = QtWidgets.QVBoxLayout()
        self.fileLayout = QtWidgets.QHBoxLayout()
        self.outLayout = QtWidgets.QHBoxLayout()
        self.classifierInLayout = QtWidgets.QHBoxLayout()
        self.featuresInLayout = QtWidgets.QHBoxLayout()
        self.featuresHeightsInLayout = QtWidgets.QHBoxLayout()
        self.forestLayout = QtWidgets.QGridLayout()
        self.classifierLayout = QtWidgets.QGridLayout()
        self.featuresLayout = QtWidgets.QGridLayout()
        #self.logLayout = QtWidgets.QVBoxLayout()

        #self.executeLog = QTextEditLogger(self)
        #self.executeLog.setFormatter(logFormat)
        #logger.getLogger().addHandler(self.executeLog)
        #logger.getLogger().setLevel(logger.DEBUG)

        self.fileText = QtWidgets.QLabel("Choose a DEM file.")
        self.outLabel = QtWidgets.QLabel("Choose an output directory.")
        self.openClassifierLabel = QtWidgets.QLabel("Choose a classifier raster. [optional]")
        self.openFeaturesLabel = QtWidgets.QLabel("Choose a features raster. [optional]")
        self.openFeaturesHeightsLabel = QtWidgets.QLabel("Choose a feature heights raster. [optional]")

        global blockIn
        blockIn = QtWidgets.QComboBox()
        blockLabel = QtWidgets.QLabel("Main Block")
        blockIn.addItems(blockList)

        global topBlockIn
        topBlockIn = QtWidgets.QComboBox()
        topBlockLabel = QtWidgets.QLabel("Top Block")
        topBlockIn.addItems(blockList)

        global half_blocksIn
        half_blocksIn = QtWidgets.QCheckBox()
        half_blocksLabel = QtWidgets.QLabel("Use half blocks:")

        global halfBlockTypeIn
        halfBlockTypeIn = QtWidgets.QComboBox()
        halfBlockTypeLabel = QtWidgets.QLabel("Half Block Type:")
        halfBlockTypeIn.addItems(half_blockList)

        global scaleHIn
        scaleHIn = QtWidgets.QSpinBox()
        scaleHLabel = QtWidgets.QLabel("Horizontal Scale 1:")
        scaleHIn.setValue(1)
        scaleHIn.setRange(1,16)

        global scaleVIn
        scaleVIn = QtWidgets.QSpinBox()
        scaleVLabel = QtWidgets.QLabel("Vertical Scale 1:")
        scaleVIn.setValue(1)
        scaleVIn.setRange(1,16)

        global autoScaleIn
        autoScaleIn = QtWidgets.QCheckBox()
        autoScaleLabel = QtWidgets.QLabel("Auto Vertical Scale:")
        autoScaleLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        global waterLevelIn
        waterLevelIn = QtWidgets.QSpinBox()
        waterLabel = QtWidgets.QLabel("Water Level:")
        waterLevelIn.setValue(1)
        waterLevelIn.setRange(0,256)

        global baselineHeightIn
        baselineHeightIn = QtWidgets.QSpinBox()
        baselineHeightLabel = QtWidgets.QLabel("Baseline Height")
        baselineHeightIn.setValue(5)
        baselineHeightIn.setRange(-9000,256)

        global forestCheckIn
        forestCheckIn = QtWidgets.QCheckBox()
        forestCheckLabel = QtWidgets.QLabel("Add Forest")

        global forestFreqIn
        forestFreqIn = QtWidgets.QSpinBox()
        forestFreqLabel = QtWidgets.QLabel("Forest Frequency")
        forestFreqIn.setValue(25)
        forestFreqIn.setMinimum(4)

        global treeTypesIn
        treeTypesIn = QtWidgets.QListWidget()
        treeTypesLabel = QtWidgets.QLabel("Tree Type(s)")
        treeTypesIn.addItems(tree_list)
        treeTypesIn.setSelectionMode(QtWidgets.QListWidget.MultiSelection)

        global largeTreesIn
        largeTreesIn = QtWidgets.QCheckBox()
        largeTreesLabel = QtWidgets.QLabel("Use Large Trees")

        global largeTreesFreqIn
        largeTreesFreqIn = QtWidgets.QSpinBox()
        largeTreesFreqLabel = QtWidgets.QLabel("Large Trees Frequency")
        largeTreesFreqIn.setValue(25)
        largeTreesFreqIn.setMinimum(1)

        global classifierDictIn
        classifierDictIn = QtWidgets.QTableWidget(1,2)
        classifierDictLabel = QtWidgets.QLabel("Classifier Raster Classes")
        tableHeaders = ["Id","Block"]
        classifierDictIn.setHorizontalHeaderLabels(tableHeaders)
        classifierDictIn.cellChanged.connect(self.addRow)

        global featuresDictIn
        featuresDictIn = QtWidgets.QTableWidget(1,2)
        featuresDictLabel = QtWidgets.QLabel("Features Raster Classes")
        tableHeaders = ["Id","Block"]
        featuresDictIn.setHorizontalHeaderLabels(tableHeaders)
        featuresDictIn.cellChanged.connect(self.addRow)

        self.open = QtWidgets.QPushButton("Open File")
        self.out = QtWidgets.QPushButton("Select Output Directory")
        self.openClassifier = QtWidgets.QPushButton("Open Classifier Raster")
        self.openClassifierDict = QtWidgets.QPushButton("Load Classifier Dictionary from File")
        self.saveClassifierDict = QtWidgets.QPushButton("Save Classifier Dictionary to File")
        self.openFeatures = QtWidgets.QPushButton("Open Features Raster")
        self.openFeaturesHeights = QtWidgets.QPushButton("Open Feature Heights Raster")
        self.openFeaturesDict = QtWidgets.QPushButton("Load Features Dictionary from File")
        self.saveFeaturesDict = QtWidgets.QPushButton("Save Features Dictionary to File")
        self.debugCheckLabel = QtWidgets.QLabel("Run in debug mode:")
        self.debugCheck = QtWidgets.QCheckBox()
        self.run = QtWidgets.QPushButton("Run")
        self.run.setEnabled(False)
        self.closeWin = QtWidgets.QPushButton("Close")

        self.fileLayout.addWidget(self.fileText)
        self.fileLayout.addWidget(self.open)
        self.outLayout.addWidget(self.outLabel)
        self.outLayout.addWidget(self.out)
        self.classifierInLayout.addWidget(self.openClassifierLabel)
        self.classifierInLayout.addWidget(self.openClassifier)
        self.featuresInLayout.addWidget(self.openFeaturesLabel)
        self.featuresInLayout.addWidget(self.openFeatures)
        self.featuresHeightsInLayout.addWidget(self.openFeaturesHeightsLabel)
        self.featuresHeightsInLayout.addWidget(self.openFeaturesHeights)

        self.ioLayout.addItem(self.fileLayout)
        self.ioLayout.addItem(self.outLayout)
        self.ioLayout.addItem(self.classifierInLayout)
        self.ioLayout.addItem(self.featuresInLayout)
        self.ioLayout.addItem(self.featuresHeightsInLayout)
        self.ioBox.setLayout(self.ioLayout)


        self.settingsLayout.addWidget(scaleHLabel,0,0)
        self.settingsLayout.addWidget(scaleHIn,0,1)
        self.settingsLayout.addWidget(scaleVLabel,1,0)
        self.settingsLayout.addWidget(scaleVIn,1,1)
        self.settingsLayout.addWidget(autoScaleLabel,2,0)
        self.settingsLayout.addWidget(autoScaleIn,2,1)

        self.settingsLayout.addWidget(waterLabel,0,2)
        self.settingsLayout.addWidget(waterLevelIn,0,3)
        self.settingsLayout.addWidget(baselineHeightLabel,1,2)
        self.settingsLayout.addWidget(baselineHeightIn,1,3)

        self.settingsLayout.addWidget(blockLabel,3,0)
        self.settingsLayout.addWidget(blockIn,3,1)
        self.settingsLayout.addWidget(topBlockLabel,3,2)
        self.settingsLayout.addWidget(topBlockIn,3,3)
        self.settingsLayout.addWidget(half_blocksLabel,4,0)
        self.settingsLayout.addWidget(half_blocksIn,4,1)
        self.settingsLayout.addWidget(halfBlockTypeLabel,4,2)
        self.settingsLayout.addWidget(halfBlockTypeIn,4,3)

        self.forestLayout.addWidget(forestCheckLabel,0,0)
        self.forestLayout.addWidget(forestCheckIn,0,1)
        self.forestLayout.addWidget(forestFreqLabel,0,2)
        self.forestLayout.addWidget(forestFreqIn,0,3)
        self.forestLayout.addWidget(largeTreesLabel,1,0)
        self.forestLayout.addWidget(largeTreesIn,1,1)
        self.forestLayout.addWidget(largeTreesFreqLabel,1,2)
        self.forestLayout.addWidget(largeTreesFreqIn,1,3)
        self.forestLayout.addWidget(treeTypesLabel,2,0)
        self.forestLayout.addWidget(treeTypesIn,3,0,1,4)

        self.forestBox.setLayout(self.forestLayout)
        self.settingsLayout.addWidget(self.forestBox,5,0,1,4)


        self.classifierLayout.addWidget(classifierDictIn,0,0,1,2)
        self.classifierLayout.addWidget(self.openClassifierDict,1,0)
        self.classifierLayout.addWidget(self.saveClassifierDict,1,1)
        self.classifierBox.setLayout(self.classifierLayout)

        self.featuresLayout.addWidget(featuresDictIn,0,0,1,2)
        self.featuresLayout.addWidget(self.openFeaturesDict,1,0)
        self.featuresLayout.addWidget(self.saveFeaturesDict,1,1)
        self.featuresBox.setLayout(self.featuresLayout)

        self.settingsLayout.addWidget(self.classifierBox,6,0,1,4)
        self.settingsLayout.addWidget(self.featuresBox,7,0,1,4)

        self.settingsBox.setLayout(self.settingsLayout)

        self.buttonLayout.addWidget(self.debugCheckLabel)
        self.buttonLayout.addWidget(self.debugCheck)
        self.buttonLayout.addWidget(self.run)
        self.buttonLayout.addWidget(self.closeWin)

        self.buttonBox.setLayout(self.buttonLayout)

        #self.logLayout.addWidget(self.executeLog.logger)
        #self.logBox.setLayout(self.logLayout)

        self.fileSelected = False
        self.directorySelected = False

        self.closeWin.clicked.connect(self.close)
        self.run.clicked.connect(self.execute)
        self.open.clicked.connect(self.openFile)
        self.out.clicked.connect(self.selDirect)
        self.openClassifier.clicked.connect(self.openClassifierFile)
        self.openFeatures.clicked.connect(self.openFeaturesFile)
        self.openFeaturesHeights.clicked.connect(self.openFeaturesHeightsFile)
        self.openClassifierDict.clicked.connect(self.openClassifierDictFile)
        self.saveClassifierDict.clicked.connect(self.saveClassifierDictFile)
        self.openFeaturesDict.clicked.connect(self.openFeaturesDictFile)
        self.saveFeaturesDict.clicked.connect(self.saveFeaturesDictFile)
        self.debugCheck.stateChanged.connect(self.debugCheckFunc)

    def debugCheckFunc(self):
        if self.sender().isChecked():
            logToConsole.setLevel(logger.DEBUG)
            logger.info("Changing to Debug Mode")
        else:
            logger.info("Changing to Normal Mode")

    def addRow(self):
        if self.sender().item(self.sender().rowCount()-1,0) is not None:
            if self.sender().item(self.sender().rowCount()-1,0).text() != "":
                self.sender().insertRow(self.sender().rowCount())
        if self.sender().item(self.sender().rowCount()-1,1) is not None:
            if self.sender().item(self.sender().rowCount()-1,1).text() != "":
                self.sender().insertRow(self.sender().rowCount())

    def close(self):
        QtWidgets.QWidget.close(self)

    def openFile(self):
        global file
        fileOpenDialog = QtWidgets.QFileDialog(self)
        file = fileOpenDialog.getOpenFileName(self,"Open File","","GDAL Raster Formats (*.asc *.tif *.tiff *.adf *.ACE2 *.gen *.thf *.arg *.bsb *.bt *.ctg *.dds *.dimap *.doq1 *.doq2 *.e00grid *.hdr *.eir *.fits *.grd *.gxf *.ida *.mpr *.isce *.mem *.kro *.gis *.lan *.mff *.ndf *.gmt *.aux *.png *.pgm *.slc *.int *.gri *.sdat *.sdts *.sgi *.snodas *.hgt *.xpm *.gff *.zmap);;Any File (*)")[0]
        if file == "":
            logging.info("No File Chosen. Please Choose a File")
        else:
            if not self.directorySelected:
                global directory
                directory = os.path.dirname(file)
                self.outLabel.setText("Output Directory: {}".format(directory))
                logging.info("Output Directory: {}".format(directory))
            self.run.setEnabled(True)
            self.fileSelected = True
            self.fileText.setText("DEM: {}".format(file))
            logging.info("DEM: {}".format(file))

    def selDirect(self):
        global directory
        fileDirectDialog = QtWidgets.QFileDialog(self)
        directory = fileDirectDialog.getExistingDirectory(self,"Select Output Directory")
        if directory == "":
            logging.info("No Directory Chosen. Please Choose a Directory")
        else:
            if self.fileSelected:
                self.run.setEnabled(True)
            self.directorySelected = True
            self.outLabel.setText("Output Directory: {}".format(directory))
            logging.info("Output Directory: {}".format(directory))

    def openClassifierFile(self):
        global classifierFile
        fileOpenDialog = QtWidgets.QFileDialog(self)
        classifierFile = fileOpenDialog.getOpenFileName(self,"Open File","","GDAL Raster Formats (*.asc *.tif *.tiff *.adf *.ACE2 *.gen *.thf *.arg *.bsb *.bt *.ctg *.dds *.dimap *.doq1 *.doq2 *.e00grid *.hdr *.eir *.fits *.grd *.gxf *.ida *.mpr *.isce *.mem *.kro *.gis *.lan *.mff *.ndf *.gmt *.aux *.png *.pgm *.slc *.int *.gri *.sdat *.sdts *.sgi *.snodas *.hgt *.xpm *.gff *.zmap);;Any File (*)")[0]
        if classifierFile == "":
            logging.info("No File Chosen. Please Choose a File")
        else:
            self.rasterSelected = True
            self.openClassifierLabel.setText("Classifier Raster: {}".format(classifierFile))
            logging.info("Classifier Raster: {}".format(classifierFile))

    def openClassifierDictFile(self):
        classifierDictFileDialog = QtWidgets.QFileDialog(self)
        classifierDictFile = classifierDictFileDialog.getOpenFileName(self,"Open File","","CSV File (*.csv);;Any File (*)")
        classifierDictFromFile = pd.read_csv(classifierDictFile[0],header=None)
        for i in range(len(classifierDictFromFile)):
            classifierId = QtWidgets.QTableWidgetItem(str(classifierDictFromFile.iloc[i,0]))
            classifierBlock = QtWidgets.QTableWidgetItem(classifierDictFromFile.iloc[i,1])
            classifierDictIn.setItem(i,0,classifierId)
            classifierDictIn.setItem(i,1,classifierBlock)
        del classifierDictFromFile
        del classifierDictFile

    def saveClassifierDictFile(self):
        classifierDictFileDialog = QtWidgets.QFileDialog(self)
        classifierDictFile = classifierDictFileDialog.getSaveFileName(self,"Save File","","CSV File (*.csv);;Any File (*)")
        classifierDict = []
        for i in range(classifierDictIn.rowCount()):
            itemKey = classifierDictIn.item(i,0)
            itemBlock = classifierDictIn.item(i,1)
            if itemKey is not None:
                if itemBlock is not None:
                    classifierDict.append([int(itemKey.text()),itemBlock.text()])
        classifierDictOut = pd.DataFrame(classifierDict)
        classifierDictOut.to_csv(classifierDictFile[0],index=False,header=False)
        del classifierDictOut
        del classifierDictFile

    def openFeaturesFile(self):
        global featuresFile
        fileOpenDialog = QtWidgets.QFileDialog(self)
        featuresFile = fileOpenDialog.getOpenFileName(self,"Open File","","GDAL Raster Formats (*.asc *.tif *.tiff *.adf *.ACE2 *.gen *.thf *.arg *.bsb *.bt *.ctg *.dds *.dimap *.doq1 *.doq2 *.e00grid *.hdr *.eir *.fits *.grd *.gxf *.ida *.mpr *.isce *.mem *.kro *.gis *.lan *.mff *.ndf *.gmt *.aux *.png *.pgm *.slc *.int *.gri *.sdat *.sdts *.sgi *.snodas *.hgt *.xpm *.gff *.zmap);;Any File (*)")[0]
        if featuresFile == "":
            logging.info("No File Chosen. Please Choose a File")
        else:
            self.rasterSelected = True
            self.openFeaturesLabel.setText("Features Raster: {}".format(featuresFile))
            logging.info("Features Raster: {}".format(featuresFile))

    def openFeaturesHeightsFile(self):
        global featuresHeightsFile
        fileOpenDialog = QtWidgets.QFileDialog(self)
        featuresHeightsFile = fileOpenDialog.getOpenFileName(self,"Open File","","GDAL Raster Formats (*.asc *.tif *.tiff *.adf *.ACE2 *.gen *.thf *.arg *.bsb *.bt *.ctg *.dds *.dimap *.doq1 *.doq2 *.e00grid *.hdr *.eir *.fits *.grd *.gxf *.ida *.mpr *.isce *.mem *.kro *.gis *.lan *.mff *.ndf *.gmt *.aux *.png *.pgm *.slc *.int *.gri *.sdat *.sdts *.sgi *.snodas *.hgt *.xpm *.gff *.zmap);;Any File (*)")[0]
        if featuresHeightsFile == "":
            logging.info("No File Chosen. Please Choose a File")
        else:
            self.rasterSelected = True
            self.openFeaturesHeightsLabel.setText("Feature Heights Raster: {}".format(featuresHeightsFile))
            logging.info("Feature Heights Raster: {}".format(featuresHeightsFile))

    def openFeaturesDictFile(self):
        featuresDictFileDialog = QtWidgets.QFileDialog(self)
        featuresDictFile = featuresDictFileDialog.getOpenFileName(self,"Open File","","CSV File (*.csv);;Any File (*)")
        featuresDictFromFile = pd.read_csv(featuresDictFile[0],header=None)
        for i in range(len(featuresDictFromFile)):
            featuresId = QtWidgets.QTableWidgetItem(str(featuresDictFromFile.iloc[i,0]))
            featuresBlock = QtWidgets.QTableWidgetItem(featuresDictFromFile.iloc[i,1])
            featuresDictIn.setItem(i,0,featuresId)
            featuresDictIn.setItem(i,1,featuresBlock)
        del featuresDictFromFile
        del featuresDictFile

    def saveFeaturesDictFile(self):
        featuresDictFileDialog = QtWidgets.QFileDialog(self)
        featuresDictFile = featuresDictFileDialog.getSaveFileName(self,"Save File","","CSV File (*.csv);;Any File (*)")
        featuresDict = []
        for i in range(featuresDictIn.rowCount()):
            itemKey = featuresDictIn.item(i,0)
            itemBlock = featuresDictIn.item(i,1)
            if itemKey is not None:
                if itemBlock is not None:
                    featuresDict.append([int(itemKey.text()),itemBlock.text()])
        featuresDictOut = pd.DataFrame(featuresDict)
        featuresDictOut.to_csv(featuresDictFile[0],index=False,header=False)
        del featuresDictOut
        del featuresDictFile



    def execute(self):

        #self.executeLog = QTextEditLogger(self)
        #self.executeLog.setFormatter(logFormat)
        #logging.getLogger().addHandler(self.executeLog)
        #logging.getLogger().setLevel(logging.DEBUG)
        self.run.setEnabled(False)

        start = time.perf_counter()
        numberOfBlocks = 0

        logging.info("Setting Parameters")

        waterLevel = waterLevelIn.value()
        baselineHeight = baselineHeightIn.value()
        waterHeight = waterLevel + baselineHeight
        scaleH = scaleHIn.value()
        scaleV = scaleVIn.value()
        blockName = blockIn.currentText()
        topBlockName = topBlockIn.currentText()
        halfBlockTypeName = halfBlockTypeIn.currentText()
        half_blocks = half_blocksIn.isChecked()
        forest = forestCheckIn.isChecked()
        forestFreq = forestFreqIn.value()
        treeTypes = treeTypesIn.selectedItems()
        largeTrees = largeTreesIn.isChecked()
        largeTreesFreq = largeTreesFreqIn.value()
        autoScale = autoScaleIn.isChecked()

        if half_blocks:
            quant = 0.5
        else:
            quant = 1

        block = anvil.Block('minecraft',blockName)
        halfBlock = anvil.Block('minecraft',halfBlockTypeName)
        topBlock = anvil.Block('minecraft',topBlockName)

        logging.info("Horizontal Scale: {}\n \
        Vertical Scale: {}\n \
        Water Level: {}\n \
        Baseline Height: {}\n \
        Main Block: {}\n \
        Top Block: {}\n \
        Half Block: {}\n \
        Using Half Blocks? {}\n\
        Output Directory: {}".format(scaleH,scaleV,waterLevel,baselineHeight,blockName,topBlockName,halfBlockTypeName,half_blocks,directory))

        logging.info("Importing Data")

        demIn = gdal.Open(file)
        dem = np.rot90(np.flip(demIn.ReadAsArray(),1))

        if 'classifierFile' in globals():
            logging.debug("Classifier file found")
            classifierIn = gdal.Open(classifierFile)
            classifier = np.rot90(np.flip(classifierIn.ReadAsArray(),1))

        if 'featuresFile' in globals():
            featuresIn = gdal.Open(featuresFile)
            features = np.rot90(np.flip(featuresIn.ReadAsArray(),1))

        if 'featuresHeightsFile' in globals():
            featuresHeightsIn = gdal.Open(featuresHeightsFile)
            featuresHeights = np.rot90(np.flip(featuresHeightsIn.ReadAsArray(),1))


        del demIn
        if 'classifierIn' in globals():
            del classifierIn
        if 'featuresHeightsIn' in globals():
            del featuresHeightsIn
        if 'featuresIn' in globals():
            del featuresIn


        logging.info("Scaling Horizontally")


        def h_scale(data,scaleH):
            dataLists = []
            if scaleH != 1:
                for n in range(int(len(data[:,0])/scaleH)):
                    row=[]
                    for m in range(int(len(data[0,:])/scaleH)):
                        row.append(data[n*scaleH:n*scaleH+scaleH,m*scaleH:m*scaleH+scaleH].max())
                    dataLists.append(row)
            else:
                dataLists = data
            return dataLists

        data = pd.DataFrame(h_scale(dem,scaleH))

        if 'classifierFile' in globals():
            Classifier = pd.DataFrame(h_scale(classifier,scaleH))
        if 'featuresFile' in globals():
            Features = pd.DataFrame(h_scale(features,scaleH))
        if 'featuresHeightsFile' in globals():
            FeaturesHeights = pd.DataFrame(h_scale(featuresHeights,scaleH))

        logging.info("Scaling Vertically")

        del dem
        if 'classifier' in globals():
            del classifier

        def vert_scale(number,scale=scaleV):
            return number/scale

        if autoScale:
            demHeight = max(data.max()) - min(data.min())
            autoScaleV = np.ceil(demHeight/254)
            scaleV = max(autoScaleV,scaleV)
            baselineHeight = np.floor(1-min(data.min())/scaleV)

        if scaleV != 1:
            dataVScaled = data.applymap(vert_scale)
        else:
            dataVScaled = data

        logging.info("Rounding elevations to nearest half metre")

        del data

        global Data
        Data = dataVScaled.applymap(flex_round)

        del dataVScaled
        if max(Data.max()) > 255:
            overTall = max(Data.max()) - 255
            logging.error("Data {} blocks too tall, try increasing the vertical scale, or reducing the baseline height (even making it negative if necessary)".format(overTall))

        if ('classifierFile' and 'classifierDictIn') in globals():
            classifierDict = {}
            for i in range(classifierDictIn.rowCount()):
                itemKey = classifierDictIn.item(i,0)
                itemBlock = classifierDictIn.item(i,1)
                if itemKey is not None:
                    if itemBlock is not None:
                        classifierDict[int(itemKey.text())] = itemBlock.text()
            if bool(classifierDict):
                classified = True
            else:
                classified = False
        else:
            classified = False
        logging.debug("Classified: {}".format(classified))

        if ('featuresFile' and 'featuresDictIn') in globals():
            featuresDict = {}
            for i in range(featuresDictIn.rowCount()):
                itemKey = featuresDictIn.item(i,0)
                itemBlock = featuresDictIn.item(i,1)
                if itemKey is not None:
                    if itemBlock is not None:
                        featuresDict[int(itemKey.text())] = itemBlock.text()
            if bool(featuresDict):
                useFeatures = True
            else:
                useFeatures = False
        else:
            useFeatures = False
        logging.debug("Using Features: {}".format(useFeatures))

        logging.debug("Data:\n{}".format(Data))

        logging.info("Finding DEM Size")

        x_len = len(Data.iloc[:,0])
        z_len = len(Data.iloc[0,:])

        logging.info("x size:{}\n \
                        z size:{}".format(x_len,z_len))

        logging.info("Calculating number of regions required")

        xRegions = int(np.ceil(x_len/512))
        zRegions = int(np.ceil(z_len/512))

        logging.info("Regions: {}, {}".format(xRegions, zRegions))

        logging.debug('Local variables: {}\nGlobal Variables: {}'.format(locals(),globals()))

        try:
            for xRegion in range(xRegions):
                for zRegion in range(zRegions):

                    logging.info("Creating Minecraft Region: {}, {}".format(xRegion,zRegion))

                    region = anvil.EmptyRegion(xRegion,zRegion)

                    logging.info("Region: {}, {}".format(xRegion,zRegion))

                    for Regionx in range(min(512,x_len-(xRegion)*512)):
                        for Regionz in range(min(512,z_len-(zRegion)*512)):
                            x = Regionx + xRegion*512
                            z = Regionz + zRegion*512
                            if classified:
                                topBlock = anvil.Block('minecraft',classifierDict[Classifier.iloc[x,z]])
                            yRange = int(Data.iloc[x,z]+baselineHeight)
                            if z%512 == 0 and x%64 == 0:
                                logging.debug('Current Rows: {} to {} of {}, Columns: {} to {} of {}, Blocks before now: {}, Region: {}, {}'.format(z,min(z+511,z_len),z_len,x,min(x+63,x_len),x_len,numberOfBlocks,xRegion,zRegion))
                            if z%512 == 0 and x%64 != 0:
                                logging.debug('Current Rows: {} to {} of {}, Column: {} of {}, Blocks before now: {}, Region: {}, {}'.format(z,min(z+511,z_len),z_len,x,x_len,numberOfBlocks,xRegion,zRegion))
                            if Data.iloc[x,z] == -9999:
                                pass
                            elif Data.iloc[x,z] <= waterLevel:
                                region.set_block(bedrock, x, 0, z)
                                numberOfBlocks += 1
                                for y in range(1,waterHeight):
                                    region.set_block(water, x, y, z)
                                    numberOfBlocks += 1
                            elif Data.iloc[x,z]%1 == 0 or half_blocks == False:
                                for y in range(yRange):
                                    if y == 0:
                                        region.set_block(bedrock, x, y, z)
                                        numberOfBlocks += 1
                                    elif y != yRange - 1:
                                        region.set_block(block, x, y, z)
                                        numberOfBlocks += 1
                                    else:
                                        region.set_block(topBlock, x, y, z)
                                        numberOfBlocks += 1
                                        if useFeatures:
                                            if featuresDict[Features.iloc[x,z]] != (0 or 'None') or featuresDict[Features.iloc[x,z]] is not None:
                                                featureBool = True
                                                featureBlock = anvil.Block(featuresDict[Features.iloc[x,z]])
                                                for h in range(FeaturesHeights.iloc[x,z]):
                                                    yObj = y + 1 + h
                                                    region.set_block(featureBlock,x,yObj,z)
                                                    numberOfBlocks += 1
                                            else:
                                                featureBool = False
                                        else:
                                            featureBool = False
                                        if random.randrange(forestFreq) == 0 and forest and classifierDict[Classifier.iloc[x,z]] == ('dirt' or 'grass_block' or 'podzol') and not featureBool:
                                            tree = random.choice(treeTypes).text()
                                            if (tree == 'dark_oak' or ((tree == 'jungle' or tree == 'spruce') and random.randrange(largeTreesFreq) == 0 and largeTrees)) and (x != (0 or 511) and z != (0 or 511)):
                                                if x+1 < x_len and z+1 < z_len:
                                                    sqRD = (Data.iloc[x+1,z] and Data.iloc[x,z+1] and Data.iloc[x+1,z+1]) == Data.iloc[x,z]
                                                else:
                                                    sqRD = False
                                                if x+1 < x_len:
                                                    sqRU = (Data.iloc[x+1,z] and Data.iloc[x,z-1] and Data.iloc[x+1,z-1]) == Data.iloc[x,z]
                                                else:
                                                    sqRU = False
                                                if z+1 < z_len:
                                                    sqLD = (Data.iloc[x-1,z] and Data.iloc[x,z+1] and Data.iloc[x-1,z+1]) == Data.iloc[x,z]
                                                else:
                                                    sqLD = False

                                                sqLU = (Data.iloc[x-1,z] and Data.iloc[x,z-1] and Data.iloc[x-1,z-1]) == Data.iloc[x,z]


                                                if sqRD:
                                                    for x,z in zip([x,x,x+1,x+1],[z,z+1,z,z+1]):
                                                        region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                                        numberOfBlocks += 1
                                                        #logging.info(tree+' large')
                                                elif sqLD:
                                                    for x,z in zip([x,x,x-1,x-1],[z,z+1,z,z+1]):
                                                        region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                                        numberOfBlocks += 1
                                                        #logging.info(tree+' large')
                                                elif sqLU:
                                                    for x,z in zip([x,x,x-1,x-1],[z,z-1,z,z-1]):
                                                        region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                                        numberOfBlocks += 1
                                                        #logging.info(tree+' large')
                                                elif sqRU:
                                                    for x,z in zip([x,x,x+1,x+1],[z,z-1,z,z-1]):
                                                        region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                                        numberOfBlocks += 1
                                                        #logging.info(tree+' large')
                                                elif tree == 'dark_oak':
                                                    region.set_block(anvil.Block('minecraft','oak_sapling'),x,y+1,z)
                                                    numberOfBlocks += 1
                                                    #logging.info('dark oak failed: {} {} {} {}'.format(y,Data.iloc[x+1,z],Data.iloc[x,z+1],Data.iloc[x+1,z+1]))
                                                else:
                                                    region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                                    numberOfBlocks += 1
                                                    #logging.info('large tree failed: {} {} {} {}'.format(y,Data.iloc[x+1,z],Data.iloc[x,z+1],Data.iloc[x+1,z+1]))
                                            else:
                                                region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                                numberOfBlocks += 1
                                                #logging.info(tree)
                            else:
                                for y in range(yRange):
                                    if y == 0:
                                        region.set_block(bedrock, x, y, z)
                                        numberOfBlocks += 1
                                    elif y != yRange - 1:
                                        region.set_block(block, x, y, z)
                                        numberOfBlocks += 1
                                    else:
                                        region.set_block(block, x, y, z)
                                        numberOfBlocks += 1
                                        region.set_block(halfBlock, x, yRange, z)
                                        numberOfBlocks += 1
                    #if xRegion == xRegions - 1 or zRegion == zRegions - 1:
                    #    if x_len%512 != 0:
                    #        for x in range(x_len,xRegions*512):
                    #            for z in range((zRegion)*512,(zRegion+1)*512):
                    #                if (x%16 == 0 and z%16 == 0):
                    #                    logging.info('Current Chunk: {},~,{}'.format(int(x/16),int(z/16)))
                    #                region.set_block(bedrock, x, 0, z)
                    #                numberOfBlocks += 1
                    #                for y in range(1,waterHeight):
                    #                    region.set_block(water, x, y, z)
                    #                    numberOfBlocks += 1
                    #    if z_len%512 !=0:
                    #        for z in range(z_len,zRegions*512):
                    #            for x in range((xRegion)*512,(xRegion+1)*512):
                    #                if (x%16 == 0 and z%16 == 0):
                    #                    logging.info('Current Chunk: {},~,{}'.format(int(x/16),int(z/16)))
                    #                region.set_block(bedrock, x, 0, z)
                    #                numberOfBlocks += 1
                    #                for y in range(1,waterHeight):
                    #                    region.set_block(water, x, y, z)
                    #                    numberOfBlocks += 1

                    logging.info("Saving Minecraft Region: {}, {}: {}/r.{}.{}.mca".format(xRegion,zRegion,directory,xRegion,zRegion))
                    region.save('{}/r.{}.{}.mca'.format(directory,xRegion,zRegion))
                    del region
        except:
            logging.exception("There was an error in processing at point {}, ~, {}. The Data value is {}".format(x,z,Data[x,z]))
        finish = time.perf_counter()
        logging.info("Done. Wrote {} blocks, taking {}s".format(numberOfBlocks,finish-start))
        self.run.setEnabled(True)

        del Data
        if 'Classifier' in globals():
            del Classifier
        if 'classifierDict' in globals():
            del classifierDict
        if 'featuresDict' in globals():
            del featuresDict
        if 'Features' in globals():
            del Features
        if 'FeaturesHeights' in globals():
            del FeaturesHeights


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = win()
    widget.show()

    sys.exit(app.exec_())
