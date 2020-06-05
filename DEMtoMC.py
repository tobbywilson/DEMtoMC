# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 17:55:53 2020

@author: Toby
"""

import pip

def check_import(package):
    try:
        import package as name
    except ImportError:
        install(package)
        import  package

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

def flex_round(number,quantisation=0.5):
    return round(number*(1/quantisation))/(1/quantisation)



blockList = [
'stone',
'grass',
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
'water'
]

half_blockList = [
'stone_slab',
'oak_slab',
'sandstone_slab',
'brick_slab',
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

        self.setWindowTitle('DEM to Minecraft')
        self.setGeometry(300,200,500,300)

        self.createGridLayout()
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.messagesBox)
        vbox.addWidget(self.settingsBox)
        vbox.addWidget(self.buttonBox)
        vbox.addWidget(self.logBox)
        self.setLayout(vbox)

    def createGridLayout(self):
        self.buttonBox = QtWidgets.QGroupBox("")
        self.settingsBox = QtWidgets.QGroupBox("Settings")
        self.messagesBox = QtWidgets.QGroupBox("File")
        self.logBox = QtWidgets.QGroupBox("Execution Log")

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.settingsLayout = QtWidgets.QGridLayout()
        self.messagesLayout = QtWidgets.QVBoxLayout()
        self.logLayout = QtWidgets.QVBoxLayout()

        self.executeLog = QTextEditLogger(self)
        self.executeLog.setFormatter(logFormat)
        logging.getLogger().addHandler(self.executeLog)
        logging.getLogger().setLevel(logging.DEBUG)

        self.fileText = QtWidgets.QLabel("Choose a DEM file. Accepted formats: .asc")


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

        global skirtHeightIn
        skirtHeightIn = QtWidgets.QSpinBox()
        skirtHeightLabel = QtWidgets.QLabel("Skirt Height")
        skirtHeightIn.setValue(5)
        skirtHeightIn.setRange(-9000,256)

        self.open = QtWidgets.QPushButton("Open File")
        self.run = QtWidgets.QPushButton("Run")
        self.run.setEnabled(False)
        self.closeWin = QtWidgets.QPushButton("Close")


        self.messagesLayout.addWidget(self.fileText)
        self.messagesBox.setLayout(self.messagesLayout)


        self.settingsLayout.addWidget(scaleHLabel,0,0)
        self.settingsLayout.addWidget(scaleHIn,0,1)
        self.settingsLayout.addWidget(scaleVLabel,1,0)
        self.settingsLayout.addWidget(scaleVIn,1,1)

        self.settingsLayout.addWidget(waterLabel,0,2)
        self.settingsLayout.addWidget(waterLevelIn,0,3)
        self.settingsLayout.addWidget(skirtHeightLabel,1,2)
        self.settingsLayout.addWidget(skirtHeightIn,1,3)

        self.settingsLayout.addWidget(blockLabel,3,0)
        self.settingsLayout.addWidget(blockIn,3,1)
        self.settingsLayout.addWidget(topBlockLabel,3,2)
        self.settingsLayout.addWidget(topBlockIn,3,3)
        self.settingsLayout.addWidget(half_blocksLabel,4,0)
        self.settingsLayout.addWidget(half_blocksIn,4,1)
        self.settingsLayout.addWidget(halfBlockTypeLabel,4,2)
        self.settingsLayout.addWidget(halfBlockTypeIn,4,3)

        self.settingsBox.setLayout(self.settingsLayout)


        self.buttonLayout.addWidget(self.open)
        self.buttonLayout.addWidget(self.run)
        self.buttonLayout.addWidget(self.closeWin)

        self.buttonBox.setLayout(self.buttonLayout)

        self.logLayout.addWidget(self.executeLog.logger)
        self.logBox.setLayout(self.logLayout)

        self.closeWin.clicked.connect(self.close)
        self.run.clicked.connect(self.execute)
        self.open.clicked.connect(self.openFile)

    def close(self):
        QtWidgets.QWidget.close(self)

    def openFile(self):
        global file
        fileOpenDialog = QtWidgets.QFileDialog(self)
        file = fileOpenDialog.getOpenFileName(self,"Open File","","ASCII Grid Files (*.asc);;Any File (*)")[0]
        if file == "":
            logging.info("No File Chosen. Please Choose a File")
        else:
            self.run.setEnabled(True)
            self.fileText.setText("{}".format(file))
            logging.info("File Chosen: {}".format(file))

    def execute(self):

        self.executeLog = QTextEditLogger(self)
        self.executeLog.setFormatter(logFormat)
        logging.getLogger().addHandler(self.executeLog)
        logging.getLogger().setLevel(logging.DEBUG)

        logging.info("Setting Parameters")

        waterLevel = waterLevelIn.value()
        skirtHeight = skirtHeightIn.value()
        waterHeight = waterLevel + skirtHeight
        scaleH = scaleHIn.value()
        scaleV = scaleVIn.value()
        blockName = blockIn.currentText()
        topBlockName = topBlockIn.currentText()
        halfBlockTypeName = halfBlockTypeIn.currentText()
        half_blocks = half_blocksIn.isChecked()

        block = anvil.Block('minecraft',blockName)
        halfBlock = anvil.Block('minecraft',halfBlockTypeName)
        topBlock = anvil.Block('minecraft',topBlockName)

        logging.info("Horizontal Scale: {}\n \
        Vertical Scale: {}\n \
        Water Level: {}\n \
        Skirt Height: {}\n \
        Main Block: {}\n \
        Top Block: {}\n \
        Half Block: {}\n \
        Using Half Blocks? {}".format(scaleH,scaleV,waterLevel,skirtHeight,blockName,topBlockName,halfBlockTypeName,half_blocks))

        logging.info("Importing Data")
        temp = open("temp.asc", "w")
        temp.write("ncols        1\nnrows        1\nxllcorner    0\nyllcorner    0\ncellsize     1.000000000000\nNODATA_value  -9999\n0")
        temp.close()
        global dem
        demIn = gdal.Open(file)
        dem = demIn.ReadAsArray()

        logging.info("dem:\n{}".format(dem))

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

        global data
        data = pd.DataFrame(dataLists)

        logging.info("Scaling Vertically")


        def vert_scale(number,scale=scaleV):
            return number/scale

        if scaleV != 1:
            dataVScaled = data.applymap(vert_scale)
        else:
            dataVScaled = data

        logging.info("Rounding elevations to nearest half metre")


        global Data
        Data = dataVScaled.applymap(flex_round)


        logging.info("Finding DEM Size")

        x_len = len(Data)
        z_len = len(Data.iloc[0,])

        logging.info("x size:\n \
                        z size:".format(x_len,z_len))

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
                        yRange = int(Data.iloc[x,z]+skirtHeight)
                        if (x%16 == 0 and z%16 == 0):
                            logging.info('Current Chunk: {},~,{}'.format(int(x/16),int(z/16)))
                        if Data.iloc[x,z] <= waterLevel:
                            region.set_block(bedrock, x, 0, z)
                            for y in range(1,waterHeight):
                                region.set_block(water, x, y, z)
                        elif Data.iloc[x,z]%1 == 0:
                            for y in range(yRange):
                                if y == 0:
                                    region.set_block(bedrock, x, y, z)
                                elif y != yRange - 1:
                                    region.set_block(block, x, y, z)
                                else:
                                    region.set_block(topBlock, x, y, z)
                        else:
                            for y in range(yRange):
                                if y == 0:
                                    region.set_block(bedrock, x, y, z)
                                elif y != yRange - 1:
                                    region.set_block(block, x, y, z)
                                elif half_blocks == False:
                                    region.set_block(topBlock, x, y, z)
                                else:
                                    region.set_block(block, x, y, z)
                                    region.set_block(halfBlock, x, yRange, z)
                if xRegion == xRegions - 1 or zRegion == zRegions - 1:
                    if x_len%512 != 0:
                        for x in range(x_len,xRegions*512):
                            for z in range((zRegion)*512,(zRegion+1)*512):
                                if (x%16 == 0 and z%16 == 0):
                                    logging.info('Current Chunk: {},~,{}'.format(int(x/16),int(z/16)))
                                region.set_block(bedrock, x, 0, z)
                                for y in range(1,waterHeight):
                                    region.set_block(water, x, y, z)
                    if z_len%512 !=0:
                        for z in range(z_len,zRegions*512):
                            for x in range((xRegion)*512,(xRegion+1*512)):
                                if (x%16 == 0 and z%16 == 0):
                                    logging.info('Current Chunk: {},~,{}'.format(int(x/16),int(z/16)))
                                region.set_block(bedrock, x, 0, z)
                                for y in range(1,waterHeight):
                                    region.set_block(water, x, y, z)

                logging.info("Saving Minecraft Region: {}, {}".format(xRegion,zRegion))
                region.save('r.{}.{}.mca'.format(xRegion,zRegion))

        logging.info("Done")

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = win()
    widget.show()

    sys.exit(app.exec_())
