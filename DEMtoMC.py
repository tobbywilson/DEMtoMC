# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 17:55:53 2020

@author: Toby
"""

import pip

#Data import and manipulation
import numpy as np
import pandas as pd

#Data visualisation
import matplotlib.pyplot as plt

#logging
import sys
import logging

#GUI
from PySide2 import QtCore, QtWidgets, QtGui

#Geoprocessing
from osgeo import gdal
gdal.AllRegister()

#Minecraft world editing
import anvil

#Random number generation
import random

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

logFormat = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

logToConsole = logging.StreamHandler(sys.stdout)
logToConsole.setFormatter(logFormat)
logging.getLogger().addHandler(logToConsole)
logging.getLogger().setLevel(logging.DEBUG)


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
        #self.logBox = QtWidgets.QGroupBox("Execution Log")

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.settingsLayout = QtWidgets.QGridLayout()
        self.ioLayout = QtWidgets.QVBoxLayout()
        self.fileLayout = QtWidgets.QHBoxLayout()
        self.outLayout = QtWidgets.QHBoxLayout()
        self.forestLayout = QtWidgets.QGridLayout()
        #self.logLayout = QtWidgets.QVBoxLayout()

        #self.executeLog = QTextEditLogger(self)
        #self.executeLog.setFormatter(logFormat)
        #logging.getLogger().addHandler(self.executeLog)
        #logging.getLogger().setLevel(logging.DEBUG)

        self.fileText = QtWidgets.QLabel("Choose a DEM file.")
        self.outLabel = QtWidgets.QLabel("Choose an output directory.")

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

        self.open = QtWidgets.QPushButton("Open File")
        self.out = QtWidgets.QPushButton("Select Output Directory")
        self.run = QtWidgets.QPushButton("Run")
        self.run.setEnabled(False)
        self.closeWin = QtWidgets.QPushButton("Close")


        self.fileLayout.addWidget(self.fileText)
        self.fileLayout.addWidget(self.open)
        self.outLayout.addWidget(self.outLabel)
        self.outLayout.addWidget(self.out)

        self.ioLayout.addItem(self.fileLayout)
        self.ioLayout.addItem(self.outLayout)
        self.ioBox.setLayout(self.ioLayout)


        self.settingsLayout.addWidget(scaleHLabel,0,0)
        self.settingsLayout.addWidget(scaleHIn,0,1)
        self.settingsLayout.addWidget(scaleVLabel,1,0)
        self.settingsLayout.addWidget(scaleVIn,1,1)

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

        self.settingsBox.setLayout(self.settingsLayout)


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

    def close(self):
        QtWidgets.QWidget.close(self)

    def openFile(self):
        global file
        fileOpenDialog = QtWidgets.QFileDialog(self)
        file = fileOpenDialog.getOpenFileName(self,"Open File","","GDAL Raster Formats (*.asc *.tif *.tiff *.adf *.ACE2 *.gen *.thf *.arg *.bsb *.bt *.ctg *.dds *.dimap *.doq1 *.doq2 *.e00grid *.hdr *.eir *.fits *.grd *.gxf *.ida *.mpr *.isce *.mem *.kro *.gis *.lan *.mff *.ndf *.gmt *.aux *.png *.pgm *.slc *.int *.gri *.sdat *.sdts *.sgi *.snodas *.hgt *.xpm *.gff *.zmap);;Any File (*)")[0]
        if file == "":
            logging.info("No File Chosen. Please Choose a File")
        else:
            logging.info(self.fileSelected)
            if self.directorySelected:
                self.run.setEnabled(True)
            self.fileSelected = True
            self.fileText.setText("{}".format(file))
            logging.info("File Chosen: {}".format(file))

    def selDirect(self):
        global directory
        fileDirectDialog = QtWidgets.QFileDialog(self)
        directory = fileDirectDialog.getExistingDirectory(self,"Select Output Directory")
        if directory == "":
            logging.info("No Directory Chosen. Please Choose a Directory")
        else:
            logging.info(self.fileSelected)
            if self.fileSelected:
                self.run.setEnabled(True)
            self.directorySelected = True
            self.outLabel.setText("{}".format(directory))
            logging.info("Output Directory: {}".format(directory))

    def execute(self):

        #self.executeLog = QTextEditLogger(self)
        #self.executeLog.setFormatter(logFormat)
        #logging.getLogger().addHandler(self.executeLog)
        #logging.getLogger().setLevel(logging.DEBUG)

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

        del demIn

        logging.info("Scaling Horizontally")


        dataLists = []
        if scaleH != 1:
            for n in range(int(len(dem[:,0])/scaleH)):
                row=[]
                for m in range(int(len(dem[0,:])/scaleH)):
                    row.append(dem[n*scaleH:n*scaleH+scaleH,m*scaleH:m*scaleH+scaleH].max())
                dataLists.append(row)
        else:
            dataLists = dem

        del dem

        data = pd.DataFrame(dataLists)

        logging.info("Scaling Vertically")


        def vert_scale(number,scale=scaleV):
            return number/scale

        if scaleV != 1:
            dataVScaled = data.applymap(vert_scale)
        else:
            dataVScaled = data

        logging.info("Rounding elevations to nearest half metre")

        del data

        global Data
        Data = dataVScaled.applymap(flex_round)

        del dataVScaled

        logging.info("Data:\n{}".format(Data))

        logging.info("Finding DEM Size")

        x_len = len(Data.iloc[:,0])
        z_len = len(Data.iloc[0,:])

        logging.info("x size:{}\n \
                        z size:{}".format(x_len,z_len))

        logging.info("Calculating number of regions required")

        xRegions = int(np.ceil(x_len/512))
        zRegions = int(np.ceil(z_len/512))

        logging.info("Regions: {}, {}".format(xRegions, zRegions))

        for zRegion in range(zRegions):
            for xRegion in range(xRegions):

                logging.info("Creating Minecraft Region: {}, {}".format(xRegion,zRegion))

                region = anvil.EmptyRegion(xRegion,zRegion)

                logging.info("Region: {}, {}".format(xRegion,zRegion))

                for Regionx in range(min(512,x_len-(xRegion)*512)):
                    for Regionz in range(min(512,z_len-(zRegion)*512)):
                        x = Regionx + xRegion*512
                        z = Regionz + zRegion*512
                        yRange = int(Data.iloc[x,z]+baselineHeight)
                        if z%256 == 0:
                            logging.info('Current Rows: {} to {} of {}, Column: {} of {}, Region: {}, {}'.format(z,min(z+255,z_len),z_len,x,x_len,xRegion,zRegion))
                        if Data.iloc[x,z] == -9999:
                            pass
                        elif Data.iloc[x,z] <= waterLevel:
                            region.set_block(bedrock, x, 0, z)
                            for y in range(1,waterHeight):
                                region.set_block(water, x, y, z)
                        elif Data.iloc[x,z]%1 == 0 or half_blocks == False:
                            for y in range(yRange):
                                if y == 0:
                                    region.set_block(bedrock, x, y, z)
                                elif y != yRange - 1:
                                    region.set_block(block, x, y, z)
                                else:
                                    region.set_block(topBlock, x, y, z)
                                    if random.randrange(forestFreq) == 0 and forest:
                                        tree = random.choice(treeTypes).text()
                                        if tree == 'dark_oak' or ((tree == 'jungle' or tree == 'spruce') and random.randrange(largeTreesFreq) == 0 and largeTrees):
                                            if Data.iloc[x+1,z] == Data.iloc[x,z] and Data.iloc[x,z+1] == Data.iloc[x,z] and Data.iloc[x+1,z+1] == Data.iloc[x,z]:
                                                for x,z in zip([x,x,x+1,x+1],[z,z+1,z,z+1]):
                                                    region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                                    #logging.info(tree+' large')
                                            elif Data.iloc[x-1,z] == Data.iloc[x,z] and Data.iloc[x,z+1] == Data.iloc[x,z] and Data.iloc[x-1,z+1] == Data.iloc[x,z]:
                                                for x,z in zip([x,x,x-1,x-1],[z,z+1,z,z+1]):
                                                    region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                                    #logging.info(tree+' large')
                                            elif Data.iloc[x-1,z] == Data.iloc[x,z] and Data.iloc[x,z-1] == Data.iloc[x,z] and Data.iloc[x-1,z-1] == Data.iloc[x,z]:
                                                for x,z in zip([x,x,x-1,x-1],[z,z-1,z,z-1]):
                                                    region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                                    #logging.info(tree+' large')
                                            elif Data.iloc[x+1,z] == Data.iloc[x,z] and Data.iloc[x,z-1] == Data.iloc[x,z] and Data.iloc[x+1,z-1] == Data.iloc[x,z]:
                                                for x,z in zip([x,x,x+1,x+1],[z,z-1,z,z-1]):
                                                    region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                                    #logging.info(tree+' large')
                                            elif tree == 'dark_oak':
                                                region.set_block(anvil.Block('minecraft','oak_sapling'),x,y+1,z)
                                                #logging.info('dark oak failed: {} {} {} {}'.format(y,Data.iloc[x+1,z],Data.iloc[x,z+1],Data.iloc[x+1,z+1]))
                                            else:
                                                region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                                #logging.info('large tree failed: {} {} {} {}'.format(y,Data.iloc[x+1,z],Data.iloc[x,z+1],Data.iloc[x+1,z+1]))
                                        else:
                                            region.set_block(anvil.Block('minecraft',tree+'_sapling'),x,y+1,z)
                                            #logging.info(tree)
                        else:
                            for y in range(yRange):
                                if y == 0:
                                    region.set_block(bedrock, x, y, z)
                                elif y != yRange - 1:
                                    region.set_block(block, x, y, z)
                                else:
                                    region.set_block(block, x, y, z)
                                    region.set_block(halfBlock, x, yRange, z)
                #if xRegion == xRegions - 1 or zRegion == zRegions - 1:
                #    if x_len%512 != 0:
                #        for x in range(x_len,xRegions*512):
                #            for z in range((zRegion)*512,(zRegion+1)*512):
                #                if (x%16 == 0 and z%16 == 0):
                #                    logging.info('Current Chunk: {},~,{}'.format(int(x/16),int(z/16)))
                #                region.set_block(bedrock, x, 0, z)
                #                for y in range(1,waterHeight):
                #                    region.set_block(water, x, y, z)
                #    if z_len%512 !=0:
                #        for z in range(z_len,zRegions*512):
                #            for x in range((xRegion)*512,(xRegion+1)*512):
                #                if (x%16 == 0 and z%16 == 0):
                #                    logging.info('Current Chunk: {},~,{}'.format(int(x/16),int(z/16)))
                #                region.set_block(bedrock, x, 0, z)
                #                for y in range(1,waterHeight):
                #                    region.set_block(water, x, y, z)

                logging.info("Saving Minecraft Region: {}, {}".format(xRegion,zRegion))
                region.save('{}/r.{}.{}.mca'.format(directory,xRegion,zRegion))
                del region

        logging.info("Done")

        del Data

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = win()
    widget.show()

    sys.exit(app.exec_())
