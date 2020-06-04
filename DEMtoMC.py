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


#GUI
import sys
from PySide2 import QtCore, QtWidgets, QtGui
import logging

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
    try:
        def __init__(self):
            super().__init__()

            self.setWindowTitle('DEM to Minecraft')
            self.setGeometry(300,200,500,300)

            self.createGridLayout()
            vbox = QtWidgets.QVBoxLayout()
            vbox.addWidget(self.messagesBox)
            vbox.addWidget(self.settingsBox)
            vbox.addWidget(self.buttonBox)
            vbox.addWidget(self.logBox)
            self.setLayout(vbox)
    except Exception:
        logging.error("There was a fatal error")

    def createGridLayout(self):
        self.buttonBox = QtWidgets.QGroupBox("")
        self.settingsBox = QtWidgets.QGroupBox("Settings")
        self.messagesBox = QtWidgets.QGroupBox("")
        self.logBox = QtWidgets.QGroupBox("Execution Log")

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.settingsLayout = QtWidgets.QGridLayout()
        self.messagesLayout = QtWidgets.QVBoxLayout()
        self.logLayout = QtWidgets.QVBoxLayout()

        self.executeLog = QTextEditLogger(self)
        self.executeLog.setFormatter(logFormat)
        logging.getLogger().addHandler(self.executeLog)
        logging.getLogger().setLevel(logging.DEBUG)

        self.fileText = QtWidgets.QLabel("Choose a DEM file")


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
        skirtHeightIn.setRange(1,256)

        self.open = QtWidgets.QPushButton("Open File")
        self.run = QtWidgets.QPushButton("Execute")
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
        file = QtWidgets.QFileDialog.getOpenFileName(self)[0]
        self.fileText.setText("File Chosen: {}".format(file))
        logging.info("File Chosen: {}".format(file))

    def execute(self):
        logging.info("Importing Data")



        waterLevel = waterLevelIn.value()
        skirtHeight = skirtHeightIn.value()
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





        dem = pd.read_csv(file,delim_whitespace=True,header=None,skiprows=6)

        logging.info("Scaling Horizontally")


        dataLists = []

        for n in range(int(len(dem.iloc[:,0])/scaleH)):
            row=[]
            for m in range(int(len(dem.iloc[0,:])/scaleH)):
                row.append(max(dem.iloc[n*scaleH:n*scaleH+scaleH,m*scaleH:m*scaleH+scaleH].max()))
            dataLists.append(row)

        data = pd.DataFrame(dataLists)

        logging.info("Scalling Vertically")


        def vert_scale(number,scale=scaleV):
            return number/scale

        dataVScaled = data.applymap(vert_scale)

        logging.info("Rounding elevations to nearest half metre")



        Data = dataVScaled.applymap(flex_round)


        logging.info("Finding DEM Size")



        x_len = len(Data)
        z_len = len(Data.iloc[0,])

        logging.info("x size:".format(x_len))
        logging.info("z size:".format(z_len))

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
                        yRange = int(Data.iloc[x,z]+skirtHeight+1)
                        if (x%16 == 0 and z == 0) or (x == x_len-1 and z == z_len-1):
                            logging.info('{},~,{}'.format(x,z))
                        if Data.iloc[x,z] <= waterLevel+skirtHeight:
                            region.set_block(bedrock, x, 0, z)
                            for y in range(1,skirtHeight+waterLevel):
                                region.set_block(water, x, y, z)
                        elif Data.iloc[x,z]%1 == 0:
                            for y in range(yRange):
                                if y == 0:
                                    region.set_block(bedrock, x, y, z)
                                elif y != yRange - 1:
                                    region.set_block(block, x, y, z)
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

                logging.info("Saving Minecraft Region: {}, {}".format(xRegion,zRegion))


                region.save('r.{}.{}.mca'.format(xRegion,zRegion))

        logging.info("Done")



if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = win()
    widget.show()

    sys.exit(app.exec_())

plt.imshow(data)
plt.savefig('dem.png')

plt.imshow(Data)
plt.savefig('dem_rounded.png')
