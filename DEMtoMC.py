# -*- coding: utf-8 -*-
'''
Created on Tue Jun  2 17:55:53 2020

@author: Toby
'''

# Data import and manipulation
import numpy as np
import pandas as pd


# logging
import sys
import logging
import logging.handlers

# miscellaneous file functions
import os

# GUI
from PySide2 import QtCore, QtWidgets

# Minecraft world editing
import anvil

# Random number generation
import random

# Execution Timing
import time

# Config/argument parsing
import configparser
import argparse

# Threading Support
import threading

# Geoprocessing
from osgeo import gdal
gdal.AllRegister()

arg_parser = argparse.ArgumentParser(
                        description='Generate a minecraft world from GeoData.'
                        )
arg_parser.add_argument('--nogui',
                        help='Run without the GUI',
                        action='store_false'
                        )
arg_parser.add_argument('--config',
                        help='Select the config section. Default:DEFAULT',
                        default='DEFAULT'
                        )
arg_parser.add_argument('--debug',
                        help='Run in debug mode',
                        action='store_true'
                        )

args = arg_parser.parse_args()

config_settings_section = vars(args)['config']
gui = vars(args)['nogui']
term_debug = vars(args)['debug']

if gui:
    start_up_start = time.perf_counter()

config = configparser.ConfigParser()

settings = {}

trues = ['true', 'yes', '1', 'y', 't']
gdal_formats = 'GDAL Raster Formats (*.asc *.tif *.tiff *.adf *.ACE2 *.gen'\
               '*.thf *.arg *.bsb *.bt *.ctg *.dds *.dimap *.doq1 *.doq2'\
               '*.e00grid *.hdr *.eir *.fits *.grd *.gxf *.ida *.mpr *.isce'\
               '*.mem *.kro *.gis *.lan *.mff *.ndf *.gmt *.aux *.png *.pgm'\
               '*.slc *.int *.gri *.sdat *.sdts *.sgi *.snodas *.hgt *.xpm'\
               '*.gff *.zmap);;All Files (*.*)'


def loadFromConfig(section):
    config.read('DEMtoMC.ini')
    settings = dict(config[section])
    settings['water_level'] = float(config[section]['water_level'])
    settings['baseline_height'] = int(config[section]['baseline_height'])
    settings['scale_h'] = int(config[section]['scale_h'])
    settings['scale_v'] = float(config[section]['scale_v'])
    settings['auto_scale'] = config[section]['auto_scale'].lower() in trues
    settings['use_half_blocks'] = \
        config[section]['use_half_blocks'].lower() in trues
    settings['use_forest'] = \
        config[section]['use_forest'].lower() in trues
    settings['forest_period'] = int(config[section]['forest_period'])
    settings['tree_types'] = config[section]['tree_types'].split(', ')
    settings['use_large_trees'] = \
        config[section]['use_large_trees'].lower() in trues
    settings['large_trees_period'] = int(config[section]['large_trees_period'])
    settings['debug_mode'] = \
        True if term_debug else config[section]['debug_mode'].lower() in trues
    return settings


def saveToConfig(section, settings):
    for setting in settings:
        settings[setting] = str(settings[setting])
    config[section] = settings
    config_file = open('DEMtoMC.ini', 'w')
    config.write(config_file)
    config_file.close()


if os.path.isfile('DEMtoMC.ini'):
    settings = loadFromConfig(config_settings_section)
else:
    default_ini_setup = {}
    default_ini_setup['file'] = ''
    default_ini_setup['directory'] = ''
    default_ini_setup['classifier_file'] = ''
    default_ini_setup['features_file'] = ''
    default_ini_setup['features_heights_file'] = ''
    default_ini_setup['forest_period_file'] = ''
    default_ini_setup['classifier_dict_file'] = ''
    default_ini_setup['features_dict_file'] = ''
    default_ini_setup['water_level'] = '0.0'
    default_ini_setup['baseline_height'] = '5'
    default_ini_setup['scale_h'] = '1'
    default_ini_setup['scale_v'] = '1.0'
    default_ini_setup['auto_scale'] = 'True'
    default_ini_setup['block_name'] = ''
    default_ini_setup['top_block_name'] = ''
    default_ini_setup['half_block_name'] = ''
    default_ini_setup['use_half_blocks'] = ''
    default_ini_setup['use_forest'] = 'True'
    default_ini_setup['forest_period'] = '50'
    default_ini_setup['tree_types'] = ''
    default_ini_setup['use_large_trees'] = 'False'
    default_ini_setup['large_trees_period'] = '25'
    default_ini_setup['debug_mode'] = 'False'
    settings = default_ini_setup
    saveToConfig('DEFAULT', default_ini_setup)


def flex_round(number):
    return round(number*(2))/(2)


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

tree_surfaces = ['dirt', 'grass_block', 'podzol']

all_blocks_df = pd.read_csv('.\\minecraft.blocks.blocks')
all_blocks = list(all_blocks_df['block'])

half_blockList = [
    'stone_slab',
    'oak_slab',
    'sandstone_slab',
    'brick_slab',
]

all_half_blocks_df = pd.read_csv('.\\minecraft.half_blocks.blocks')
all_half_blocks = list(all_half_blocks_df['block'])

tree_list_df = pd.read_csv('.\\minecraft.trees.blocks')
tree_list = list(tree_list_df['block'])


log_format = '%(asctime)s - %(levelname)s: %(message)s'

log_to_file = logging.handlers.RotatingFileHandler('DEMtoMC.log',
                                                   mode='a',
                                                   maxBytes=5*1024*1024,
                                                   backupCount=3
                                                   )
log_to_file.setLevel(logging.DEBUG)

log_to_console = logging.StreamHandler(sys.stdout)
log_to_console.setLevel(logging.INFO)


logging.basicConfig(level=logging.DEBUG,
                    format=log_format,
                    handlers=[log_to_file, log_to_console])

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
        self.setGeometry(300, 200, 500, 300)

        self.createGridLayout()
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.io_box)
        vbox.addWidget(self.settings_box)
        vbox.addWidget(self.button_box)
        # vbox.addWidget(self.logBox)
        self.setLayout(vbox)

    def createGridLayout(self):
        self.button_box = QtWidgets.QGroupBox('')
        self.settings_box = QtWidgets.QGroupBox('Settings')
        self.io_box = QtWidgets.QGroupBox('Input/Output')
        self.use_forest_box = QtWidgets.QGroupBox('Forest')
        self.classifier_box = QtWidgets.QGroupBox('Classifier Dictionary')
        self.features_box = QtWidgets.QGroupBox('Features Dictionary')
        # self.logBox = QtWidgets.QGroupBox('Execution Log')

        self.button_layout = QtWidgets.QHBoxLayout()
        self.settings_layout = QtWidgets.QGridLayout()
        self.io_layout = QtWidgets.QVBoxLayout()
        self.file_layout = QtWidgets.QHBoxLayout()
        self.out_layout = QtWidgets.QHBoxLayout()
        self.classifier_in_layout = QtWidgets.QHBoxLayout()
        self.features_in_layout = QtWidgets.QHBoxLayout()
        self.features_heights_in_layout = QtWidgets.QHBoxLayout()
        self.forest_layout = QtWidgets.QGridLayout()
        self.classifier_layout = QtWidgets.QGridLayout()
        self.features_layout = QtWidgets.QGridLayout()
        # self.logLayout = QtWidgets.QVBoxLayout()

        # self.executeLog = QTextEditLogger(self)
        # self.executeLog.setFormatter(log_format)
        # logger.getLogger().addHandler(self.executeLog)
        # logger.getLogger().setLevel(logging.DEBUG)

        self.file_label = QtWidgets.QLabel('Choose a DEM file.')
        self.out_label = QtWidgets.QLabel('Choose an output directory.')
        self.open_classifier_label = \
            QtWidgets.QLabel('Choose a classifier raster. [optional]')
        self.open_features_label = \
            QtWidgets.QLabel('Choose a features raster. [optional]')
        self.open_features_heights_label = \
            QtWidgets.QLabel('Choose a feature heights raster. [optional]')
        self.open_forest_raster_label = \
            QtWidgets.QLabel('Choose a forest density raster. [optional]')

        global scale_h_in
        scale_h_in = QtWidgets.QSpinBox()
        scale_h_label = QtWidgets.QLabel('Horizontal Scale:')
        scale_h_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
        scale_h_in.setRange(1, 9999)
        scale_h_in.setPrefix('1:')

        global scale_v_in
        scale_v_in = QtWidgets.QDoubleSpinBox()
        scale_v_label = QtWidgets.QLabel('Vertical Scale:')
        scale_v_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
        scale_v_in.setRange(-1024, 1024)
        scale_v_in.setStepType(
            QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType
            )
        scale_v_in.setPrefix('1:')

        global auto_scale_in
        auto_scale_in = QtWidgets.QCheckBox()
        auto_scale_label = QtWidgets.QLabel('Vertical AutoScale:')
        auto_scale_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )

        global water_level_in
        water_level_in = QtWidgets.QDoubleSpinBox()
        water_label = QtWidgets.QLabel('Water Level:')
        water_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
        water_level_in.setRange(-10000, 10000)
        water_level_in.setStepType(
            QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType
            )

        global baseline_height_in
        baseline_height_in = QtWidgets.QSpinBox()
        baseline_height_label = QtWidgets.QLabel('Baseline Height:')
        baseline_height_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
        baseline_height_in.setRange(-9000, 256)

        global block_in
        block_in = QtWidgets.QComboBox()
        block_in.setEditable(True)
        block_label = QtWidgets.QLabel('Main Block:')
        block_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
        block_in.addItems(blockList)

        global top_block_in
        top_block_in = QtWidgets.QComboBox()
        top_block_in.setEditable(True)
        top_block_label = QtWidgets.QLabel('Top Block:')
        top_block_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
        top_block_in.addItems(blockList)

        global use_half_blocks_in
        use_half_blocks_in = QtWidgets.QCheckBox()
        use_half_blocks_label = QtWidgets.QLabel('Use half blocks:')
        use_half_blocks_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )

        global half_blockType_in
        half_blockType_in = QtWidgets.QComboBox()
        half_blockType_in.setEditable(True)
        half_blockType_label = QtWidgets.QLabel('Half Block:')
        half_blockType_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
        half_blockType_in.addItems(half_blockList)

        global use_forestCheck_in
        use_forestCheck_in = QtWidgets.QCheckBox()
        use_forestCheck_label = QtWidgets.QLabel('Add Forest:')
        use_forestCheck_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )

        global forest_period_in
        forest_period_in = QtWidgets.QSpinBox()
        forest_period_label = QtWidgets.QLabel('Forest Frequency:')
        forest_period_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
        forest_period_in.setRange(4, 9999)
        forest_period_in.setPrefix('1/')

        global tree_types_in
        tree_types_in = QtWidgets.QListWidget()
        tree_types_label = QtWidgets.QLabel('Tree Type(s)')
        tree_types_label.setAlignment(QtCore.Qt.AlignVCenter)
        tree_types_in.addItems(tree_list)
        tree_types_in.setSelectionMode(QtWidgets.QListWidget.MultiSelection)

        global use_large_trees_in
        use_large_trees_in = QtWidgets.QCheckBox()
        use_large_trees_label = QtWidgets.QLabel('Use Large Trees:')
        use_large_trees_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )

        global large_trees_period_in
        large_trees_period_in = QtWidgets.QSpinBox()
        large_trees_period_label = QtWidgets.QLabel('Large Trees Frequency:')
        large_trees_period_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
        large_trees_period_in.setMinimum(1)
        large_trees_period_in.setPrefix('1/')

        global classifier_dict_in
        classifier_dict_in = QtWidgets.QTableWidget(1, 2)
        table_headers = ['Id', 'Block']
        classifier_dict_in.setHorizontalHeaderLabels(table_headers)

        global features_dict_in
        features_dict_in = QtWidgets.QTableWidget(1, 2)
        table_headers = ['Id', 'Block']
        features_dict_in.setHorizontalHeaderLabels(table_headers)

        self.open = QtWidgets.QPushButton('Open File')
        self.out = QtWidgets.QPushButton('Select Output Directory')
        self.open_classifier = QtWidgets.QPushButton('Open Classifier Raster')
        self.open_classifier_dict = \
            QtWidgets.QPushButton('Load Classifier Dictionary from File')
        self.save_classifier_dict = \
            QtWidgets.QPushButton('Save Classifier Dictionary to File')
        self.open_features = QtWidgets.QPushButton('Open Features Raster')
        self.open_features_heights = \
            QtWidgets.QPushButton('Open Feature Heights Raster')
        self.open_features_dict = \
            QtWidgets.QPushButton('Load Features Dictionary from File')
        self.save_features_dict = \
            QtWidgets.QPushButton('Save Features Dictionary to File')
        self.open_forest_raster = \
            QtWidgets.QPushButton('Open Forest Period Raster')
        self.debug_check_label = QtWidgets.QLabel('Run in debug mode:')
        self.debug_check = QtWidgets.QCheckBox()
        self.save_config = QtWidgets.QPushButton('Save Settings')
        self.load_config = QtWidgets.QPushButton('Load Settings')
        self.run = QtWidgets.QPushButton('Run')
        self.run.setEnabled(False)
        self.close_win = QtWidgets.QPushButton('Close')

        self.file_layout.addWidget(self.file_label)
        self.file_layout.addWidget(self.open)
        self.out_layout.addWidget(self.out_label)
        self.out_layout.addWidget(self.out)
        self.classifier_in_layout.addWidget(self.open_classifier_label)
        self.classifier_in_layout.addWidget(self.open_classifier)
        self.features_in_layout.addWidget(self.open_features_label)
        self.features_in_layout.addWidget(self.open_features)
        self.features_heights_in_layout.addWidget(
            self.open_features_heights_label
            )
        self.features_heights_in_layout.addWidget(self.open_features_heights)

        self.io_layout.addItem(self.file_layout)
        self.io_layout.addItem(self.out_layout)
        self.io_layout.addItem(self.classifier_in_layout)
        self.io_layout.addItem(self.features_in_layout)
        self.io_layout.addItem(self.features_heights_in_layout)
        self.io_box.setLayout(self.io_layout)

        self.settings_layout.addWidget(scale_h_label, 0, 0)
        self.settings_layout.addWidget(scale_h_in, 0, 1)
        self.settings_layout.addWidget(scale_v_label, 1, 0)
        self.settings_layout.addWidget(scale_v_in, 1, 1)
        self.settings_layout.addWidget(auto_scale_label, 2, 0)
        self.settings_layout.addWidget(auto_scale_in, 2, 1)

        self.settings_layout.addWidget(water_label, 0, 2)
        self.settings_layout.addWidget(water_level_in, 0, 3)
        self.settings_layout.addWidget(baseline_height_label, 1, 2)
        self.settings_layout.addWidget(baseline_height_in, 1, 3)

        self.settings_layout.addWidget(block_label, 3, 0)
        self.settings_layout.addWidget(block_in, 3, 1)
        self.settings_layout.addWidget(top_block_label, 3, 2)
        self.settings_layout.addWidget(top_block_in, 3, 3)
        self.settings_layout.addWidget(use_half_blocks_label, 4, 0)
        self.settings_layout.addWidget(use_half_blocks_in, 4, 1)
        self.settings_layout.addWidget(half_blockType_label, 4, 2)
        self.settings_layout.addWidget(half_blockType_in, 4, 3)

        self.forest_layout.addWidget(use_forestCheck_label, 0, 0)
        self.forest_layout.addWidget(use_forestCheck_in, 0, 1)
        self.forest_layout.addWidget(forest_period_label, 0, 2)
        self.forest_layout.addWidget(forest_period_in, 0, 3)
        self.forest_layout.addWidget(use_large_trees_label, 1, 0)
        self.forest_layout.addWidget(use_large_trees_in, 1, 1)
        self.forest_layout.addWidget(large_trees_period_label, 1, 2)
        self.forest_layout.addWidget(large_trees_period_in, 1, 3)
        self.forest_layout.addWidget(tree_types_label, 2, 0)
        self.forest_layout.addWidget(tree_types_in, 3, 0, 1, 4)
        self.forest_layout.addWidget(self.open_forest_raster_label, 4, 0, 2, 1)
        self.forest_layout.addWidget(self.open_forest_raster, 4, 3, 2, 1)

        self.use_forest_box.setLayout(self.forest_layout)
        self.settings_layout.addWidget(self.use_forest_box, 5, 0, 1, 4)

        self.classifier_layout.addWidget(classifier_dict_in, 0, 0, 1, 2)
        self.classifier_layout.addWidget(self.open_classifier_dict, 1, 0)
        self.classifier_layout.addWidget(self.save_classifier_dict, 1, 1)
        self.classifier_box.setLayout(self.classifier_layout)

        self.features_layout.addWidget(features_dict_in, 0, 0, 1, 2)
        self.features_layout.addWidget(self.open_features_dict, 1, 0)
        self.features_layout.addWidget(self.save_features_dict, 1, 1)
        self.features_box.setLayout(self.features_layout)

        self.settings_layout.addWidget(self.classifier_box, 6, 0, 1, 4)
        self.settings_layout.addWidget(self.features_box, 7, 0, 1, 4)

        self.settings_box.setLayout(self.settings_layout)

        self.button_layout.addWidget(self.debug_check_label)
        self.button_layout.addWidget(self.debug_check)
        self.button_layout.addWidget(self.save_config)
        self.button_layout.addWidget(self.load_config)
        self.button_layout.addWidget(self.run)
        self.button_layout.addWidget(self.close_win)

        self.button_box.setLayout(self.button_layout)

        # self.logLayout.addWidget(self.executeLog.logger)
        # self.logBox.setLayout(self.logLayout)

        self.fileSelected = False
        self.directorySelected = False

        self.close_win.clicked.connect(self.close)
        self.run.clicked.connect(self.executeFromGui)
        self.open.clicked.connect(self.openFile)
        self.out.clicked.connect(self.selectDirectory)
        self.open_classifier.clicked.connect(self.openClassifierFile)
        self.open_features.clicked.connect(self.openFeaturesFile)
        self.open_features_heights.clicked.connect(
            self.openFeaturesHeightsFile
            )
        self.open_forest_raster.clicked.connect(self.openForestFile)
        self.open_classifier_dict.clicked.connect(
            self.openClassifierDictFileDialog
            )
        self.save_classifier_dict.clicked.connect(self.saveClassifierDictFile)
        self.open_features_dict.clicked.connect(
            self.openFeaturesDictFileDialog
            )
        self.save_features_dict.clicked.connect(self.saveFeaturesDictFile)
        self.debug_check.stateChanged.connect(self.setDebugModeGUI)
        self.save_config.clicked.connect(self.saveSettingsDialog)
        self.load_config.clicked.connect(self.loadSettingsDialog)
        features_dict_in.cellChanged.connect(self.addRow)
        classifier_dict_in.cellChanged.connect(self.addRow)

        global config_settings_section
        self.setFromConfig(config_settings_section)

    def executeFromGui(self):
        thread_run = threading.Thread(target=execute)
        self.run.setEnabled(False)
        thread_run.start()
        self.run.setEnabled(True)

    def setFromConfig(self, section):
        global settings
        settings = loadFromConfig(section)

        if settings['file'] != '':
            self.file_label.setText('DEM: {}'.format(settings['file']))
            self.fileSelected = True

        if settings['directory'] != '':
            self.out_label.setText(
                'Output Directory: {}'.format(settings['directory']))
            self.directorySelected = True
            if self.fileSelected:
                self.run.setEnabled(True)

        if settings['classifier_file'] != '':
            self.open_classifier_label.setText(
                'Classifier Raster: {}'
                .format(settings['classifier_file']))

        if settings['features_file'] != '':
            self.open_features_label.setText(
                'Features Raster: {}'
                .format(settings['features_file']))

        if settings['features_heights_file'] != '':
            self.open_features_heights_label.setText(
                'Feature Heights Raster: {}'
                .format(settings['features_heights_file']))

        if settings['forest_period_file'] != '':
            self.open_forest_raster_label.setText(
                'Forest  Raster: {}'
                .format(settings['forest_period_file']))

        scale_h_in.setValue(settings['scale_h'])
        scale_v_in.setValue(settings['scale_v'])
        auto_scale_in.setChecked(settings['auto_scale'])
        water_level_in.setValue(settings['water_level'])
        baseline_height_in.setValue(settings['baseline_height'])

        block_in.setCurrentText(settings['block_name'])
        top_block_in.setCurrentText(settings['top_block_name'])
        use_half_blocks_in.setChecked(settings['use_half_blocks'])
        half_blockType_in.setCurrentText(settings['half_block_name'])

        use_forestCheck_in.setChecked(settings['use_forest'])
        forest_period_in.setValue(settings['forest_period'])

        for tree in settings['tree_types']:
            matching_items = tree_types_in.findItems(tree,
                                                     QtCore.Qt.MatchExactly
                                                     )
            for item in matching_items:
                item.setSelected(True)

        use_large_trees_in.setChecked(settings['use_large_trees'])
        large_trees_period_in.setValue(settings['large_trees_period'])

        classifier_dict_from_file = \
            openDictFile(settings['classifier_dict_file'])
        if classifier_dict_from_file is not None:
            for i in range(len(classifier_dict_from_file)):
                classifier_id = QtWidgets.QTableWidgetItem(
                    str(classifier_dict_from_file.iloc[i, 0]))

                classifier_block = QtWidgets.QTableWidgetItem(
                    classifier_dict_from_file.iloc[i, 1])

                classifier_dict_in.setItem(i, 0, classifier_id)
                classifier_dict_in.setItem(i, 1, classifier_block)

        features_dict_from_file = openDictFile(settings['features_dict_file'])
        if features_dict_from_file is not None:
            for i in range(len(features_dict_from_file)):
                features_id = QtWidgets.QTableWidgetItem(
                    str(features_dict_from_file.iloc[i, 0])
                    )
                features_block = QtWidgets.QTableWidgetItem(
                    features_dict_from_file.iloc[i, 1]
                    )
                features_dict_in.setItem(i, 0, features_id)
                features_dict_in.setItem(i, 1, features_block)
        self.debug_check.setChecked(settings['debug_mode'])

    def saveSettingsDialog(self):
        config_sections = config.sections()
        config_section, success = \
            QtWidgets.QInputDialog().getItem(self, 'Choose Settings Name',
                                             'Settings Section Name:',
                                             config_sections
                                             )
        global settings
        settings['water_level'] = water_level_in.value()
        settings['baseline_height'] = baseline_height_in.value()
        settings['scale_h'] = scale_h_in.value()
        settings['scale_v'] = scale_v_in.value()
        settings['block_name'] = block_in.currentText()
        settings['top_block_name'] = top_block_in.currentText()
        settings['half_block_name'] = half_blockType_in.currentText()
        settings['use_half_blocks'] = use_half_blocks_in.isChecked()
        settings['use_forest'] = use_forestCheck_in.isChecked()
        settings['forest_period'] = forest_period_in.value()
        settings['tree_types'] = ', '\
            .join([item.text() for item in tree_types_in.selectedItems()])
        settings['use_large_trees'] = use_large_trees_in.isChecked()
        settings['large_trees_period'] = large_trees_period_in.value()
        settings['auto_scale'] = auto_scale_in.isChecked()
        settings['debug_mode'] = self.debug_check.isChecked()
        if success and bool(config_section):
            saveToConfig(config_section, settings)

    def loadSettingsDialog(self):
        config_sections = config.sections()
        config_section, success = \
            QtWidgets.QInputDialog().getItem(self, 'Choose Settings Name',
                                             'Settings Section Name:',
                                             config_sections
                                             )
        if success and bool(config_section):
            self.setFromConfig(config_section)

    def addRow(self):
        if self.sender().item(self.sender().rowCount()-1, 0) is not None:
            if self.sender().item(self.sender().rowCount()-1, 0).text() != '':
                self.sender().insertRow(self.sender().rowCount())
        if self.sender().item(self.sender().rowCount()-1, 1) is not None:
            if self.sender().item(self.sender().rowCount()-1, 1).text() != '':
                self.sender().insertRow(self.sender().rowCount())
        for i in range(self.sender().rowCount()-1):
            if self.sender().item(i, 0) is not None:
                if self.sender().item(i, 1) is not None:
                    if self.sender().item(i, 1).text() == '' \
                       and self.sender().item(i, 0) == '':
                        self.sender().removeRow(i)
                elif self.sender().item(i, 0).text() == '':
                    self.sender().removeRow(i)
            elif self.sender().item(i, 1) is not None:
                if self.sender().item(i, 1).text() == '':
                    self.sender().removeRow(i)
            else:
                self.sender().removeRow(i)

    def close(self):
        QtWidgets.QWidget.close(self)

    def openFile(self):
        global settings
        file_open_dialog = QtWidgets.QFileDialog(self)
        settings['file'] = file_open_dialog.getOpenFileName(self,
                                                            'Open File', '',
                                                            gdal_formats
                                                            )[0]
        if settings['file'] == '':
            logger.info('No File Chosen. Please Choose a File')
        else:
            logger.info('DEM: {}'.format(settings['file']))
            if not self.directorySelected:
                settings['directory'] = os.path.dirname(settings['file'])
                self.out_label.setText('Output Directory: {}'
                                       .format(settings['directory'])
                                       )
                logger.info('Output Directory: {}'
                            .format(settings['directory'])
                            )
            self.run.setEnabled(True)
            self.fileSelected = True
            self.file_label.setText('DEM: {}'.format(settings['file']))

    def selectDirectory(self):
        global settings
        file_direct_dialog = QtWidgets.QFileDialog(self)
        settings['directory'] = file_direct_dialog.getExistingDirectory(
            self, 'Select Output Directory'
            )
        if settings['directory'] == '':
            logger.info('No Directory Chosen. Please Choose a Directory')
        else:
            if self.fileSelected:
                self.run.setEnabled(True)
            self.directorySelected = True
            self.out_label.setText('Output Directory: {}'
                                   .format(settings['directory'])
                                   )
            logger.info('Output Directory: {}'.format(settings['directory']))

    def openClassifierFile(self):
        global settings
        file_open_dialog = QtWidgets.QFileDialog(self)
        settings['classifier_file'] = \
            file_open_dialog.getOpenFileName(self, 'Open File', '',
                                             gdal_formats
                                             )[0]
        if settings['classifier_file'] == '':
            logger.info('No File Chosen. Please Choose a File')
        else:
            self.rasterSelected = True
            self.open_classifier_label.setText(
                'Classifier Raster: {}'.format(settings['classifier_file'])
                )
            logger.info('Classifier Raster: {}'
                        .format(settings['classifier_file'])
                        )

    def openClassifierDictFileDialog(self):
        global settings
        classifier_dict_file_dialog = QtWidgets.QFileDialog(self)
        settings['classifier_dict_file'] = \
            classifier_dict_file_dialog.getOpenFileName(self, 'Open File', '',
                                                        'CSV File (*.csv);;'
                                                        'Any File (*)'
                                                        )[0]
        classifier_dict_from_file = \
            openDictFile(settings['classifier_dict_file'])
        for i in range(len(classifier_dict_from_file)):
            classifier_id = QtWidgets.QTableWidgetItem(
                    str(classifier_dict_from_file.iloc[i, 0])
                    )
            classifier_block = QtWidgets.QTableWidgetItem(
                    classifier_dict_from_file.iloc[i, 1]
                    )
            classifier_dict_in.setItem(i, 0, classifier_id)
            classifier_dict_in.setItem(i, 1, classifier_block)

    def saveClassifierDictFile(self):
        global settings
        classifier_dict_file_dialog = QtWidgets.QFileDialog(self)
        settings['classifier_dict_file'] = \
            classifier_dict_file_dialog.getSaveFileName(self, 'Save File', '',
                                                        'CSV File (*.csv)'
                                                        ';;Any File (*)'
                                                        )[0]
        classifier_dict_out = tableWidgetToDF(classifier_dict_in)
        classifier_dict_out.to_csv(settings['classifier_dict_file'],
                                   index=False, header=False
                                   )

    def openFeaturesFile(self):
        global settings
        file_open_dialog = QtWidgets.QFileDialog(self)
        settings['features_file'] = \
            file_open_dialog.getOpenFileName(self, 'Open File', '',
                                             gdal_formats
                                             )[0]
        if settings['features_file'] == '':
            logger.info('No File Chosen. Please Choose a File')
        else:
            self.rasterSelected = True
            self.open_features_label.setText('Features Raster: {}'
                                             .format(settings['features_file'])
                                             )
            logger.info('Features Raster: {}'
                        .format(settings['features_file'])
                        )

    def openFeaturesHeightsFile(self):
        global settings
        file_open_dialog = QtWidgets.QFileDialog(self)
        settings['features_heights_file'] = \
            file_open_dialog.getOpenFileName(self, 'Open File', '',
                                             gdal_formats
                                             )[0]
        if settings['features_heights_file'] == '':
            logger.info('No File Chosen. Please Choose a File')
        else:
            self.rasterSelected = True
            self.open_features_heights_label.setText(
                'Feature Heights Raster: {}'
                .format(settings['features_heights_file']))
            logger.info('Feature Heights Raster: {}'
                        .format(settings['features_heights_file']))

    def openForestFile(self):
        global settings
        file_open_dialog = QtWidgets.QFileDialog(self)
        settings['forest_period_file'] = \
            file_open_dialog.getOpenFileName(self, 'Open File', '',
                                             gdal_formats
                                             )[0]
        if settings['forest_period_file'] == '':
            logger.info('No File Chosen. Please Choose a File')
        else:
            self.rasterSelected = True
            self.open_forest_raster_label.setText(
                'Forest Raster: {}'.format(settings['forest_period_file'])
                )
            logger.info('Forest Raster: {}'
                        .format(settings['forest_period_file'])
                        )

    def openFeaturesDictFileDialog(self):
        global settings
        features_dict_file_dialog = QtWidgets.QFileDialog(self)
        settings['features_dict_file'] = \
            features_dict_file_dialog.getOpenFileName(self,
                                                      'Open File', '',
                                                      'CSV File (*.csv);;'
                                                      'Any File (*)')[0]
        features_dict_from_file = openDictFile(settings['features_dict_file'])
        if features_dict_from_file is not None:
            for i in range(len(features_dict_from_file)):
                features_id = QtWidgets.QTableWidgetItem(
                    str(features_dict_from_file.iloc[i, 0]))
                features_block = QtWidgets.QTableWidgetItem(
                    features_dict_from_file.iloc[i, 1])
                features_dict_in.setItem(i, 0, features_id)
                features_dict_in.setItem(i, 1, features_block)

    def saveFeaturesDictFile(self):
        features_dict_file_dialog = QtWidgets.QFileDialog(self)
        settings['features_dict_file'] = \
            features_dict_file_dialog.getSaveFileName(self,
                                                      'Save File', '',
                                                      'CSV File (*.csv);;'
                                                      'Any File (*)')[0]
        features_dict_out = tableWidgetToDF(features_dict_in)
        features_dict_out.to_csv(settings['features_dict_file'],
                                 index=False, header=False)

    def setDebugModeGUI(self):
        if self.sender().isChecked():
            log_to_console.setLevel(logging.DEBUG)
            logger.info('Running in Debug Mode')
        else:
            logger.info('Running in Normal Mode')
            log_to_console.setLevel(logging.INFO)


def setDebugMode(debug_mode):
    if debug_mode:
        logger.info('Running in Debug Mode')
        log_to_console.setLevel(logging.DEBUG)
    else:
        log_to_console.setLevel(logging.INFO)


def openDictFile(dict_file):
    if dict_file != '' and dict_file is not None:
        dict_from_file = pd.read_csv(dict_file, header=None)
        return dict_from_file


def tableWidgetToDF(dict_in):
    dict = []
    for i in range(dict_in.rowCount()):
        item_key = dict_in.item(i, 0)
        item_block = dict_in.item(i, 1)
        if item_key is not None:
            if item_block is not None:
                dict.append([int(item_key.text()), item_block.text()])
    dict_out = pd.DataFrame(dict)
    return dict_out


def addBlock(region, block: str, position: list):
    global number_of_blocks
    x, y, z = position
    region.set_block(anvil.Block('minecraft', str(block)), x, y, z)
    number_of_blocks += 1


def addFeature(region, position,
               features_dict, Features, Features_heights
               ):
    x, y, z = position
    if str(features_dict[Features.iloc[x, z]]).lower() not in ['0', 'none']:
        logger.debug('Feature at position ({}, {}): {}'
                     .format(x, z, features_dict[Features.iloc[x, z]]))
        feature_block_name = features_dict[Features.iloc[x, z]]
        if str(features_dict[Features.iloc[x, z]]).lower() \
           not in ('0', 'none'):
            if Features_heights.iloc[x, z] % 1 == 0:
                for h in np.arange(0, Features_heights.iloc[x, z], 1):
                    yObj = y + 1 + h
                    pos = [x, yObj, z]
                    addBlock(region, feature_block_name, pos)
            elif feature_block_name in all_half_blocks:
                for h in np.arange(0, Features_heights.iloc[x, z], 0.5):
                    yObj = y + 0.5 + h
                    pos = [x, yObj, z]
                    addBlock(region, feature_block_name, pos)
            else:
                for h in np.arange(0, Features_heights.iloc[x, z], 1):
                    yObj = y + 1 + h
                    pos = [x, yObj, z]
                    addBlock(region, feature_block_name, pos)


def checkSquareHeights(x, z, Data, x_len, z_len, z_dir='d', x_dir='r'):
    if z_dir == 'u':
        z_list = [z-1, z-1, z]
    else:
        z_list = [z+1, z+1, z]

    if x_dir == 'l':
        x_list = [x-1, x-1, x]
    else:
        x_list = [x+1, x+1, x]

    lists = zip(x_list, z_list)

    less_than_length = max(x_list) < x_len and max(z_list) < z_len

    all_within_region = max(*x_list, *z_list) % 512 != 0

    if less_than_length and all_within_region:
        sq_list = []
        for x, z in lists:
            sq_list.append(Data.iloc[x, z] == Data.iloc[x, z])
        sq = all(sq_list)
    else:
        sq = False
    return sq


def addLargeTree(region, x, y, z, Data, x_len, z_len, tree):
    if checkSquareHeights(x, z, Data, x_len, z_len):
        for x, z in zip([x, x, x+1, x+1], [z, z+1, z, z+1]):
            pos = [z, y+1, z]
            addBlock(region, str(tree+'_sapling'), pos)

    elif checkSquareHeights(x, z, Data, x_len, z_len, x_dir='l'):
        for x, z in zip([x, x, x-1, x-1], [z, z+1, z, z+1]):
            pos = [z, y+1, z]
            addBlock(region, str(tree+'_sapling'), pos)

    elif checkSquareHeights(x, z, Data, x_len, z_len,
                            z_dir='u', x_dir='l'):
        for x, z in zip([x, x, x-1, x-1], [z, z-1, z, z-1]):
            pos = [z, y+1, z]
            addBlock(region, str(tree+'_sapling'), pos)

    elif checkSquareHeights(x, z, Data, x_len, z_len, z_dir='u'):
        for x, z in zip([x, x, x+1, x+1], [z, z-1, z, z-1]):
            pos = [z, y+1, z]
            addBlock(region, str(tree+'_sapling'), pos)

    elif tree == 'dark_oak':
        pos = [z, y+1, z]
        addBlock(region, str('oak_sapling'), pos)
    else:
        addBlock(region, str(tree+'_sapling'), pos)


def addForest(region, position, x_len, z_len, Data,
              top_block_name, Forest_period_raster = '', ):
    global settings
    x, y, z = position
    add_tree = False
    if settings['forest_period_file'] != '':
        if Forest_period_raster.iloc[x, z] > 0:
            forest_period_block = Forest_period_raster.iloc[x, z]
            surface_check = top_block_name in tree_surfaces
            add_tree = surface_check
    elif settings['use_forest']:
        surface_check = top_block_name in tree_surfaces
        add_tree = surface_check
        forest_period_block = settings['forest_period']

    if add_tree:
        random_choice = random.random() < 1/forest_period_block
        large_tree_random = random.random() < 1/settings['large_trees_period']
        height_check = y < 254
        if random_choice and surface_check and height_check:
            tree = random.choice(settings['tree_types'])
            if (tree == 'dark_oak' or ((tree == 'jungle' or tree == 'spruce')
               and large_tree_random and settings['use_large_trees'])):
                addLargeTree(region, x, y, z, Data, x_len, z_len, tree)
            else:
                pos = [x, y+1, z]
                addBlock(region, str(tree+'_sapling'), pos)


def autoScale(data):
    global settings
    demHeight = max(data.max()) - min(data.min())
    auto_scaleV = demHeight/253
    settings['scale_v'] = max(auto_scaleV, settings['scale_v'])
    settings['baseline_height'] =\
        np.floor(1-min(data.min())/settings['scale_v'] + 1)
    logger.info('Vertical Scale: {}, Baseline Height: {}'
                .format(settings['scale_v'], settings['baseline_height'])
                )


def vert_scale(number, scale=settings['scale_v']):
    return number/scale

def h_scale(data, scale):
    data_lists = []
    if scale != 1:
        for n in range(int(len(data[:, 0])/scale)):
            row = []
            for m in range(int(len(data[0, :])/scale)):
                row.append(data[n * scale:n * scale + scale,
                                m * scale:m * scale + scale].max())
            data_lists.append(row)
    else:
        data_lists = data
    return data_lists

def execute():
    global gui
    global settings
    global classifier_dict_in
    global features_dict_in
    # self.executeLog = QTextEditLogger(self)
    # self.executeLog.setFormatter(log_format)
    # logging.getLogger().addHandler(self.executeLog)
    # logging.getLogger().setLevel(logging.DEBUG)

    if settings['file'] == '' or settings['file'] is None:
        logger.critical('No DEM File Set. Please Set a File.')

    start = time.perf_counter()

    logger.info('Setting Parameters')

    if gui:
        settings['water_level'] = water_level_in.value()
        settings['baseline_height'] = baseline_height_in.value()
        settings['scale_h'] = scale_h_in.value()
        settings['scale_v'] = scale_v_in.value()
        settings['block_name'] = block_in.currentText()
        settings['top_block_name'] = top_block_in.currentText()
        settings['half_block_name'] = half_blockType_in.currentText()
        settings['use_half_blocks'] = use_half_blocks_in.isChecked()
        settings['use_forest'] = use_forestCheck_in.isChecked()
        settings['forest_period'] = forest_period_in.value()
        settings['tree_types'] = \
            [item.text() for item in tree_types_in.selectedItems()]
        settings['use_large_trees'] = use_large_trees_in.isChecked()
        settings['large_trees_period'] = large_trees_period_in.value()
        settings['auto_scale'] = auto_scale_in.isChecked()

    if not gui:
        setDebugMode(settings['debug_mode'])

    water_level_scaled = vert_scale(settings['water_level'])
    water_height = int(water_level_scaled) + settings['baseline_height']

    if settings['tree_types'] == []:
        settings['tree_types'] = ['oak']

    if settings['scale_v'] == 0:
        logger.warning('Vertical scale cannot be 0,'
                       'please use a different value.'
                       'Continuing with AutoScale.')
        settings['auto_scale'] = True

    for block in [settings['block_name'], settings['top_block_name']]:
        if block not in all_blocks:
            logger.warning('A block name used ({}), is not recognised as a'
                           'valid block or fluid. I will try anyway,'
                           'but may not succeed.'.format(block))
    if settings['half_block_name'] not in all_blocks:
        logger.warning('The half block name used ({}), is not recognised as a'
                       'valid block. I will try anyway, but may not succeed.'
                       .format(settings['half_block_name']))
    elif settings['half_block_name'] not in all_half_blocks:
        logger.warning('The half block name used ({}), is not recognised as a'
                       'valid half block. I will still succeed,'
                       'but you may not achieve your desired result.'
                       .format(settings['half_block_name']))

    logger.info('Horizontal Scale: {}\n'
                '\t\t\t\tVertical Scale: {}\n'
                '\t\t\t\tWater Level: {}\n'
                '\t\t\t\tBaseline Height: {}\n'
                '\t\t\t\tMain Block: {}\n'
                '\t\t\t\tTop Block: {}\n'
                '\t\t\t\tHalf Block: {}\n'
                '\t\t\t\tUsing Half Blocks? {}\n'
                '\t\t\t\tOutput Directory: {}'
                .format(settings['scale_h'], settings['scale_v'],
                        settings['water_level'], settings['baseline_height'],
                        settings['block_name'], settings['top_block_name'],
                        settings['half_block_name'],
                        settings['use_half_blocks'], settings['directory']
                        )
                )

    logger.info('Importing Data')

    dem_in = gdal.Open(settings['file'])
    dem = np.rot90(np.flip(dem_in.ReadAsArray(), 1))

    if settings['classifier_file'] != '':
        logger.debug('Classifier file found')
        classifier_in = gdal.Open(settings['classifier_file'])
        classifier = np.rot90(np.flip(classifier_in.ReadAsArray(), 1))

    if settings['features_file'] != '':
        features_in = gdal.Open(settings['features_file'])
        features = np.rot90(np.flip(features_in.ReadAsArray(), 1))

    if settings['features_heights_file'] != '':
        features_heights_in = gdal.Open(settings['features_heights_file'])
        features_heights = np.rot90(
            np.flip(features_heights_in.ReadAsArray(), 1))

    if settings['forest_period_file'] != '':
        forest_period_file_in = gdal.Open(settings['forest_period_file'])
        forest_period_raster = np.rot90(
            np.flip(forest_period_file_in.ReadAsArray(), 1))

    del dem_in
    del classifier_in
    del features_in
    del features_heights_in
    del forest_period_file_in

    logger.info('Scaling Horizontally')

    data = pd.DataFrame(h_scale(dem, settings['scale_h']))

    if settings['classifier_file'] != '':
        Classifier = pd.DataFrame(h_scale(classifier, settings['scale_h']))

    if settings['features_file'] != '':
        Features = pd.DataFrame(h_scale(features, settings['scale_h']))

    if settings['features_heights_file'] != '':
        features_heights_unrounded = pd.DataFrame(h_scale(features_heights,
                                                  settings['scale_h']))

    if settings['forest_period_file'] != '':
        Forest_period_raster = pd.DataFrame(h_scale(forest_period_raster,
                                                    settings['scale_h']))

    logger.info('Scaling Vertically')

    del dem

    if settings['auto_scale']:
        logger.info('Autoscaling')
        autoScale(data)

    if settings['scale_v'] != 1:
        data_v_scaled = data.applymap(vert_scale)
    else:
        data_v_scaled = data

    logger.info('Rounding elevations to nearest half metre')

    del data

    Data = data_v_scaled.applymap(flex_round)
    Features_heights = features_heights_unrounded.applymap(flex_round)

    del data_v_scaled

    if max(Data.max())/settings['scale_v'] + settings['baseline_height'] > 255:
        over_tall = max(Data.max()) - 255
        logger.warning('Data {} blocks too tall,'
                       'try increasing the vertical scale,'
                       'or reducing the baseline height'
                       '(even making it negative if necessary),'
                       'or use the AutoScale option.'
                       'I will truncate any too tall stacks.'
                       .format(over_tall))

    if bool(settings['classifier_file']):
        classifier_dict = {}
        if gui:
            classifier_dict_df = tableWidgetToDF(classifier_dict_in)
        else:
            classifier_dict_df = openDictFile(settings['classifier_dict_file'])
        for i in range(len(classifier_dict_df)):
            item_key = classifier_dict_df.iloc[i, 0]
            item_block = classifier_dict_df.iloc[i, 1]
            if item_key is not None:
                if item_block is not None:
                    classifier_dict[int(item_key)] = item_block
        if bool(classifier_dict):
            classified = True
        else:
            classified = False
    else:
        classified = False

    logger.debug('Classified: {}'.format(classified))

    if settings['features_file'] != '':
        features_dict = {}
        if gui:
            features_dict_df = tableWidgetToDF(features_dict_in)
        else:
            features_dict_df = openDictFile(settings['features_dict_file'])
        for i in range(len(features_dict_df)):
            item_key = features_dict_df.iloc[i, 0]
            item_block = features_dict_df.iloc[i, 1]
            if item_key is not None:
                if item_block is not None:
                    features_dict[int(item_key)] = item_block
        if bool(features_dict):
            use_features = True
        else:
            use_features = False
    else:
        use_features = False

    logger.debug('Using Features: {}'.format(use_features))

    logger.debug('Data:\n{}'.format(Data))

    logger.info('Finding DEM Size')

    x_len = len(Data.iloc[:, 0])
    z_len = len(Data.iloc[0, :])

    logger.info('x size: {}, z size: {}'.format(x_len, z_len))

    logger.info('Calculating number of regions required')

    x_regions = int(np.ceil(x_len/512))
    z_regions = int(np.ceil(z_len/512))

    logger.info('Regions: {} ({} \N{Multiplication Sign} {})'
                .format(x_regions * z_regions, x_regions, z_regions)
                )

    global number_of_blocks
    number_of_blocks = 0

    region_index = 0

    for x_region in range(x_regions):
        for z_region in range(z_regions):
            region_index += 1
            logger.info('Creating Region: {} of {} ({}, {})'
                        .format(region_index, x_region * z_region,
                                x_region, z_region
                                )
                        )

            region = anvil.EmptyRegion(x_region, z_region)

            logger.info('Region: {} of {} ({}, {})'
                        .format(region_index,  x_region * z_region,
                                x_region, z_region
                                )
                        )

            for region_x in range(min(512, x_len-(x_region)*512)):
                for region_z in range(min(512, z_len-(z_region)*512)):
                    x = region_x + x_region*512
                    z = region_z + z_region*512
                    if classified:
                        top_block_name = \
                            str(classifier_dict[Classifier.iloc[x, z]])
                    else:
                        top_block_name = settings['top_block_name']
                    if Data.iloc[x, z] + settings['baseline_height'] < 255:
                        y_range = \
                            int(Data.iloc[x, z]+settings['baseline_height'])
                    else:
                        y_range = 255
                    if z % 512 == 0 and x % 64 == 0:
                        logger.info('Current Rows: {} to {} of {}\n'
                                    '\t\t\t\tColumns: {} to {} of {}\n'
                                    '\t\t\t\tBlocks before now: {}\n'
                                    '\t\t\t\tRegion: {} of {} ({}, {})\n'
                                    '\t\t\t\tTime: {}'
                                    .format(z, min(z+511, z_len), z_len, x,
                                            min(x+63, x_len), x_len,
                                            number_of_blocks, region_index,
                                            x_regions * z_regions,
                                            x_region, z_region,
                                            time.perf_counter()-start))
                    if z % 512 == 0 and x % 64 != 0:
                        logger.debug('Current Rows: {} to {} of {}\n'
                                     '\t\t\t\t Columns: {} of {}\n'
                                     '\t\t\t\t Blocks before now: {}\n'
                                     '\t\t\t\t Region: {} of {} ({}, {})\n'
                                     '\t\t\t\t Time: {}'
                                     .format(z, min(z+511, z_len), z_len, x,
                                             x_len, number_of_blocks,
                                             region_index,
                                             x_regions * z_regions,
                                             x_region, z_region,
                                             time.perf_counter()-start))
                    if Data.iloc[x, z] == -9999:
                        pass
                    elif Data.iloc[x, z] <=  water_level_scaled:
                        pos = [x, 0, z]
                        addBlock(region, 'bedrock', pos)
                        for y in range(1, water_height):
                            pos = [x, y, z]
                            addBlock(region, 'water', pos)
                    elif not settings['use_half_blocks']\
                     or Data.iloc[x, z] % 1 == 0:
                        for y in range(y_range):
                            pos = [x, y, z]
                            if y == 0:
                                addBlock(region, 'bedrock', pos)
                            elif y != y_range - 1:
                                addBlock(region, settings['block_name'], pos)
                            else:
                                pos = [x, y, z]
                                addBlock(region, top_block_name, pos)
                                if settings['use_forest'] and settings['forest_period_file'] != '':
                                    addForest(region, pos, x_len, z_len, Data, top_block_name,
                                              Forest_period_raster = Forest_period_raster
                                              )
                                elif settings['use_forest']:
                                    addForest(region, pos, x_len, z_len, Data, top_block_name)
                                if use_features:
                                    addFeature(region, pos,
                                               features_dict, Features,
                                               Features_heights
                                               )
                    else:
                        for y in range(y_range):
                            pos = [x, y, z]
                            if y == 0:
                                addBlock(region, 'bedrock', pos)
                            elif y != y_range - 1:
                                addBlock(region, settings['block_name'], pos)
                            else:
                                pos = [x, y_range, z]
                                addBlock(region,
                                         settings['half_block_name'], pos
                                         )

            # Previous code for completing the region
            # to avoid having large gaps at the edges.
            # if x_region == x_regions - 1 or z_region == z_regions - 1:
            #    if x_len%512 != 0:
            #        for x in range(x_len, x_regions*512):
            #            for z in range((z_region)*512, (z_region+1)*512):
            #                if (x%16 == 0 and z%16 == 0):
            #                    logger.info('Current Chunk: {}, ~, {}'
            #                                .format(int(x/16), int(z/16)))
            #                region.set_block(bedrock, x, 0, z)
            #                number_of_blocks += 1
            #                for y in range(1, water_height):
            #                    region.set_block(water, x, y, z)
            #                    number_of_blocks += 1
            #    if z_len%512 !=0:
            #        for z in range(z_len, z_regions*512):
            #            for x in range((x_region)*512, (x_region+1)*512):
            #                if (x%16 == 0 and z%16 == 0):
            #                    logger.info('Current Chunk: {}, ~, {}'
            #                                .format(int(x/16), int(z/16)))
            #                region.set_block(bedrock, x, 0, z)
            #                number_of_blocks += 1
            #                for y in range(1, water_height):
            #                    region.set_block(water, x, y, z)
            #                    number_of_blocks += 1

            logger.info('Saving Minecraft Region: {0}, {1}: {2}/r.{0}.{1}.mca'
                        .format(x_region, z_region, settings['directory'])
                        )
            region.save('{}/r.{}.{}.mca'.format(settings['directory'],
                                                x_region, z_region
                                                )
                        )

    finish = time.perf_counter()
    logger.info('Done. Wrote {} blocks, taking {:.2f}s'
                .format(number_of_blocks, finish-start))


if gui:
    if __name__ == '__main__':
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])

        widget = win()
        widget.show()

        start_up_finish = time.perf_counter()
        logger.info('GUI Startup time: {:.2f}'.format(start_up_finish-start_up_start))
        
        sys.exit(app.exec_())
else:
    execute()
