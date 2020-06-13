# -*- coding: utf-8 -*-
'''
Created on Tue Jun  2 17:55:53 2020

@author: Toby
'''

#Data import and manipulation
import numpy as np
import pandas as pd


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

#Config/argument parsing
import configparser
import argparse

arg_parser = argparse.ArgumentParser(description='Generate a minecraft world from GeoData.')
arg_parser.add_argument('--nogui',help = 'run without the GUI',action='store_false')
arg_parser.add_argument('--config',help = 'select the config section. Default:DEFAULT',default='DEFAULT')
args = arg_parser.parse_args()

config_settings_section = vars(args)['config']
gui = vars(args)['nogui']

config = configparser.ConfigParser()

settings = {}

def loadFromConfig(section):
    config.read('DEMtoMC.ini')
    settings = dict(config[section])
    settings['water_level'] = float(config[section]['water_level'])
    settings['baseline_height'] = int(config[section]['baseline_height'])
    settings['scale_h'] = int(config[section]['scale_h'])
    settings['scale_v'] = float(config[section]['scale_v'])
    settings['auto_scale'] = config[section]['auto_scale'].lower() in ['true','yes','1','y','t']
    settings['use_half_blocks'] = config[section]['use_half_blocks'].lower() in ['true','yes','1','y','t']
    settings['use_forest'] = config[section]['use_forest'].lower() in ['true','yes','1','y','t']
    settings['forest_freq'] = int(config[section]['forest_freq'])
    settings['tree_types'] = config[section]['tree_types'].split(',')
    settings['use_large_trees'] = config[section]['use_large_trees'].lower() in ['true','yes','1','y','t']
    settings['large_trees_freq'] = int(config[section]['large_trees_freq'])
    settings['debug_mode'] = config[section]['debug_mode'].lower() in ['true','yes','1','y','t']
    return settings


def saveToConfig(section,settings):
    for setting in settings:
        settings[setting] = str(settings[setting])
    config[section] = settings
    config_file = open('DEMtoMC.ini','w')
    config.write(config_file)
    config_file.close()

if os.path.isfile('DEMtoMC.ini'):
    settings = loadFromConfig(config_settings_section)
    config_file_bool = True
else:
    config_file_bool = False

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

all_blocks = [
'acacia_button','acacia_door','acacia_fence_gate','acacia_fence','acacia_leaves','acacia_log','acacia_planks','acacia_pressure_plate','acacia_sapling','acacia_sign','acacia_slab','acacia_stairs','acacia_trapdoor','acacia_wall_sign','acacia_wood','activator_rail','air','allium','andesite','andesite_slab','andesite_stairs','andesite_wall','anvil','attached_melon_stem','attached_pumpkin_stem','azure_bluet','bamboo','bamboo_sapling','barrel','barrier','beacon','bedrock','beehive','bee_nest','beetroots','bell','birch_button','birch_door','birch_fence_gate','birch_fence','birch_leaves','birch_log','birch_planks','birch_pressure_plate','birch_sapling','birch_sign','birch_slab','birch_stairs','birch_trapdoor','birch_wall_sign','birch_wood','black_banner','black_bed','black_carpet','black_concrete_powder','black_concrete','black_glazed_terracotta','black_shulker_box','black_stained_glass','black_stained_glass_pane','black_terracotta','black_wall_banner','black_wool','blast_furnace','blue_banner','blue_bed','blue_carpet','blue_concrete_powder','blue_concrete','blue_glazed_terracotta','blue_ice','blue_orchid','blue_shulker_box','blue_stained_glass','blue_stained_glass_pane','blue_terracotta','blue_wall_banner','blue_wool','bone_block','bookshelf','brain_coral','brain_coral_block','brain_coral_fan','brain_coral_wall_fan','brewing_stand','brick_slab','brick_stairs','brick_wall','bricks','brown_banner','brown_bed','brown_carpet','brown_concrete_powder','brown_concrete','brown_glazed_terracotta','brown_mushroom_block','brown_mushroom','brown_shulker_box','brown_stained_glass','brown_stained_glass_pane','brown_terracotta','brown_wall_banner','brown_wool','bubble_column','bubble_coral','bubble_coral_block','bubble_coral_fan','bubble_coral_wall_fan','cactus','cake','campfire','carrots','cartography_table','carved_pumpkin','cauldron','cave_air','chain_command_block','chest','chipped_anvil','chiseled_quartz_block','chiseled_red_sandstone','chiseled_sandstone','chiseled_stone_bricks','chorus_flower','chorus_plant','clay','coal_block','coal_ore','coarse_dirt','cobblestone','cobblestone_slab','cobblestone_stairs','cobblestone_wall','cobweb','cocoa','command_block','comparator','composter','conduit','cornflower','cracked_stone_bricks','crafting_table','creeper_head','creeper_wall_head','cut_red_sandstone','cut_red_sandstone_slab','cut_sandstone','cut_sandstone_slab','cyan_banner','cyan_bed','cyan_carpet','cyan_concrete_powder','cyan_concrete','cyan_glazed_terracotta','cyan_shulker_box','cyan_stained_glass','cyan_stained_glass_pane','cyan_terracotta','cyan_wall_banner','cyan_wool','damaged_anvil','dandelion','dark_oak_button','dark_oak_door','dark_oak_fence_gate','dark_oak_fence','dark_oak_leaves','dark_oak_log','dark_oak_planks','dark_oak_pressure_plate','dark_oak_sapling','dark_oak_sign','dark_oak_slab','dark_oak_stairs','dark_oak_trapdoor','dark_oak_wall_sign','dark_oak_wood','dark_prismarine','dark_prismarine_slab','dark_prismarine_stairs','daylight_detector','dead_brain_coral','dead_brain_coral_block','dead_brain_coral_fan','dead_brain_coral_wall_fan','dead_bubble_coral','dead_bubble_coral_block','dead_bubble_coral_fan','dead_bubble_coral_wall_fan','dead_bush','dead_fire_coral','dead_fire_coral_block','dead_fire_coral_fan','dead_fire_coral_wall_fan','dead_horn_coral','dead_horn_coral_block','dead_horn_coral_fan','dead_horn_coral_wall_fan','dead_tube_coral','dead_tube_coral_block','dead_tube_coral_fan','dead_tube_coral_wall_fan','detector_rail','diamond_block','diamond_ore','diorite','diorite_slab','diorite_stairs','diorite_wall','dirt','dispenser','dragon_egg','dragon_head','dragon_wall_head','dried_kelp_block','dropper','emerald_block','emerald_ore','enchanting_table','end_gateway','end_portal_frame','end_portal','end_rod','end_stone','end_stone_brick_slab','end_stone_brick_stairs','end_stone_brick_wall','end_stone_bricks','ender_chest','farmland','fern','fire','fire_coral','fire_coral_block','fire_coral_fan','fire_coral_wall_fan','fletching_table','flower_pot','frosted_ice','furnace','glass','glass_pane','glowstone','gold_block','gold_ore','granite','granite_slab','granite_stairs','granite_wall','grass_block','grass_path','grass','gravel','gray_banner','gray_bed','gray_carpet','gray_concrete_powder','gray_concrete','gray_glazed_terracotta','gray_shulker_box','gray_stained_glass','gray_stained_glass_pane','gray_terracotta','gray_wall_banner','gray_wool','green_banner','green_bed','green_carpet','green_concrete_powder','green_concrete','green_glazed_terracotta','green_shulker_box','green_stained_glass','green_stained_glass_pane','green_terracotta','green_wall_banner','green_wool','grindstone','hay_block','heavy_weighted_pressure_plate','hopper','honey_block','honeycomb_block','horn_coral','horn_coral_block','horn_coral_fan','horn_coral_wall_fan','ice','infested_chiseled_stone_bricks','infested_cobblestone','infested_cracked_stone_bricks','infested_mossy_stone_bricks','infested_stone','infested_stone_bricks','iron_bars','iron_door','iron_block','iron_ore','iron_trapdoor','jack_o_lantern','jigsaw','jukebox','jungle_button','jungle_door','jungle_fence_gate','jungle_fence','jungle_leaves','jungle_log','jungle_planks','jungle_pressure_plate','jungle_sapling','jungle_sign','jungle_slab','jungle_stairs','jungle_trapdoor','jungle_wall_sign','jungle_wood','kelp','kelp_plant','ladder','lantern','lapis_block','lapis_ore','large_fern','lava','lectern','lever','light_blue_banner','light_blue_bed','light_blue_carpet','light_blue_concrete_powder','light_blue_concrete','light_blue_glazed_terracotta','light_blue_shulker_box','light_blue_stained_glass','light_blue_stained_glass_pane','light_blue_terracotta','light_blue_wall_banner','light_blue_wool','light_gray_banner','light_gray_bed','light_gray_carpet','light_gray_concrete_powder','light_gray_concrete','light_gray_glazed_terracotta','light_gray_shulker_box','light_gray_stained_glass','light_gray_stained_glass_pane','light_gray_terracotta','light_gray_wall_banner','light_gray_wool','light_weighted_pressure_plate','lilac','lily_pad','lily_of_the_valley','lime_banner','lime_bed','lime_carpet','lime_concrete_powder','lime_concrete','lime_glazed_terracotta','lime_shulker_box','lime_stained_glass','lime_stained_glass_pane','lime_terracotta','lime_wall_banner','lime_wool','loom','magenta_banner','magenta_bed','magenta_carpet','magenta_concrete_powder','magenta_concrete','magenta_glazed_terracotta','magenta_shulker_box','magenta_stained_glass','magenta_stained_glass_pane','magenta_terracotta','magenta_wall_banner','magenta_wool','magma_block','melon','melon_stem','mossy_cobblestone','mossy_cobblestone_slab','mossy_cobblestone_stairs','mossy_cobblestone_wall','mossy_stone_brick_slab','mossy_stone_brick_stairs','mossy_stone_brick_wall','mossy_stone_bricks','moving_piston','mushroom_stem','mycelium','nether_brick_fence','nether_brick_slab','nether_brick_stairs','nether_brick_wall','nether_bricks','nether_portal','nether_quartz_ore','nether_wart_block','nether_wart','netherrack','note_block','oak_button','oak_door','oak_fence_gate','oak_fence','oak_leaves','oak_log','oak_planks','oak_pressure_plate','oak_sapling','oak_sign','oak_slab','oak_stairs','oak_trapdoor','oak_wall_sign','oak_wood','observer','obsidian','orange_banner','orange_bed','orange_carpet','orange_concrete_powder','orange_concrete','orange_glazed_terracotta','orange_shulker_box','orange_stained_glass','orange_stained_glass_pane','orange_terracotta','orange_tulip','orange_wall_banner','orange_wool','oxeye_daisy','packed_ice','peony','petrified_oak_slab','pink_banner','pink_bed','pink_carpet','pink_concrete_powder','pink_concrete','pink_glazed_terracotta','pink_shulker_box','pink_stained_glass','pink_stained_glass_pane','pink_terracotta','pink_tulip','pink_wall_banner','pink_wool','piston_head','piston','player_head','player_wall_head','podzol','polished_andesite','polished_andesite_slab','polished_andesite_stairs','polished_diorite','polished_diorite_slab','polished_diorite_stairs','polished_granite','polished_granite_slab','polished_granite_stairs','poppy','potatoes','potted_acacia_sapling','potted_allium','potted_azure_bluet','potted_bamboo','potted_birch_sapling','potted_blue_orchid','potted_brown_mushroom','potted_cactus','potted_cornflower','potted_dandelion','potted_dark_oak_sapling','potted_dead_bush','potted_fern','potted_jungle_sapling','potted_lily_of_the_valley','potted_oak_sapling','potted_orange_tulip','potted_oxeye_daisy','potted_pink_tulip','potted_poppy','potted_red_mushroom','potted_red_tulip','potted_spruce_sapling','potted_white_tulip','potted_wither_rose','powered_rail','prismarine','prismarine_brick_slab','prismarine_brick_stairs','prismarine_bricks','prismarine_slab','prismarine_stairs','prismarine_wall','pumpkin','pumpkin_stem','purple_banner','purple_bed','purple_carpet','purple_concrete_powder','purple_concrete','purple_glazed_terracotta','purple_shulker_box','purple_stained_glass','purple_stained_glass_pane','purple_terracotta','purple_wall_banner','purple_wool','purpur_block','purpur_pillar','purpur_slab','purpur_stairs','quartz_block','quartz_pillar','quartz_slab','quartz_stairs','rail','red_banner','red_bed','red_carpet','red_concrete_powder','red_concrete','red_glazed_terracotta','red_mushroom_block','red_mushroom','red_nether_brick_slab','red_nether_brick_stairs','red_nether_brick_wall','red_nether_bricks','red_sand','red_sandstone','red_sandstone_slab','red_sandstone_stairs','red_sandstone_wall','red_shulker_box','red_stained_glass','red_stained_glass_pane','red_terracotta','red_tulip','red_wall_banner','red_wool','redstone_block','redstone_lamp','redstone_ore','redstone_torch','redstone_wall_torch','redstone_wire','repeater','repeating_command_block','rose_bush','sand','sandstone','sandstone_slab','sandstone_stairs','sandstone_wall','scaffolding','sea_lantern','sea_pickle','seagrass','shulker_box','skeleton_skull','skeleton_wall_skull','slime_block','smithing_table','smoker','smooth_quartz','smooth_quartz_slab','smooth_quartz_stairs','smooth_red_sandstone','smooth_red_sandstone_slab','smooth_red_sandstone_stairs','smooth_sandstone','smooth_sandstone_slab','smooth_sandstone_stairs','smooth_stone','smooth_stone_slab','snow_block','snow','soul_sand','spawner','sponge','spruce_button','spruce_door','spruce_fence_gate','spruce_fence','spruce_leaves','spruce_log','spruce_planks','spruce_pressure_plate','spruce_sapling','spruce_sign','spruce_slab','spruce_stairs','spruce_trapdoor','spruce_wall_sign','spruce_wood','sticky_piston','stone','stone_brick_slab','stone_brick_stairs','stone_brick_wall','stone_bricks','stone_button','stone_pressure_plate','stone_slab','stone_stairs','stonecutter','stripped_acacia_log','stripped_acacia_wood','stripped_birch_log','stripped_birch_wood','stripped_dark_oak_log','stripped_dark_oak_wood','stripped_jungle_log','stripped_jungle_wood','stripped_oak_log','stripped_oak_wood','stripped_spruce_log','stripped_spruce_wood','structure_block','structure_void','sugar_cane','sunflower','sweet_berry_bush','tnt','tall_grass','tall_seagrass','terracotta','torch','trapped_chest','tripwire_hook','tripwire','tube_coral','tube_coral_block','tube_coral_fan','tube_coral_wall_fan','turtle_egg','vine','void_air','wall_torch','water','wet_sponge','wheat','white_banner','white_bed','white_carpet','white_concrete_powder','white_concrete','white_glazed_terracotta','white_shulker_box','white_stained_glass','white_stained_glass_pane','white_terracotta','white_tulip','white_wall_banner','white_wool','wither_rose','wither_skeleton_skull','wither_skeleton_wall_skull','yellow_banner','yellow_bed','yellow_carpet','yellow_concrete_powder','yellow_concrete','yellow_glazed_terracotta','yellow_shulker_box','yellow_stained_glass','yellow_stained_glass_pane','yellow_terracotta','yellow_wall_banner','yellow_wool','zombie_head','zombie_wall_head','empty','flowing_lava','flowing_water','lava','water'
]

half_blockList = [
'stone_slab',
'oak_slab',
'sandstone_slab',
'brick_slab',
]

all_half_blocks = ['oak_slab','spruce_slab','birch_slab','jungle_slab','acacia_slab','dark_oak_slab','crimson_slab','warped_slab','stone_slab','smooth_stone_slab','granite_slab','polished_granite_slab','diorite_slab','polished_diorite_slab','andesite_slab','polished_andesite_slab','cobblestone_slab','mossy_cobblestone_slab','stone_brick_slab','mossy_stone_brick_slab','brick_slab','end_stone_brick_slab','nether_brick_slab','red_nether_brick_slab','sandstone_slab','cut_sandstone_slab','smooth_sandstone_slab','red_sandstone_slab','cut_red_sandstone_slab','smooth_red_sandstone_slab','quartz_slab','smooth_quartz_slab','purpur_slab','prismarine_slab','prismarine_brick_slab','dark_prismarine_slab','petrified_oak_slab','blackstone_slab','polished_blackstone_slab','polished_blackstone_brick_slab']

treeList = [
'oak',
'birch',
'spruce',
'acacia',
'dark_oak',
'jungle'
]

bedrock = anvil.Block('minecraft','bedrock')
water = anvil.Block('minecraft','water')


log_format = '%(asctime)s - %(levelname)s: %(message)s'

log_to_file = logging.handlers.RotatingFileHandler('DEMtoMC.log',mode='a',maxBytes=5*1024*1024,backupCount=3)
log_to_file.setLevel(logging.DEBUG)

log_to_console = logging.StreamHandler(sys.stdout)
log_to_console.setLevel(logging.INFO)


logging.basicConfig(level=logging.DEBUG,
                    format=log_format,
                    handlers=[log_to_file,log_to_console])

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
        vbox.addWidget(self.io_box)
        vbox.addWidget(self.settings_box)
        vbox.addWidget(self.button_box)
        #vbox.addWidget(self.logBox)
        self.setLayout(vbox)

    def createGridLayout(self):
        self.button_box = QtWidgets.QGroupBox('')
        self.settings_box = QtWidgets.QGroupBox('Settings')
        self.io_box = QtWidgets.QGroupBox('Input/Output')
        self.use_forest_box = QtWidgets.QGroupBox('Forest')
        self.classifier_box = QtWidgets.QGroupBox('Classifier Raster Dictionary')
        self.features_box = QtWidgets.QGroupBox('Features Raster Dictionary')
        #self.logBox = QtWidgets.QGroupBox('Execution Log')

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
        #self.logLayout = QtWidgets.QVBoxLayout()

        #self.executeLog = QTextEditLogger(self)
        #self.executeLog.setFormatter(log_format)
        #logger.getLogger().addHandler(self.executeLog)
        #logger.getLogger().setLevel(logging.DEBUG)

        self.file_label = QtWidgets.QLabel('Choose a DEM file.')
        self.out_label = QtWidgets.QLabel('Choose an output directory.')
        self.open_classifier_label = QtWidgets.QLabel('Choose a classifier raster. [optional]')
        self.open_features_label = QtWidgets.QLabel('Choose a features raster. [optional]')
        self.open_features_heights_label = QtWidgets.QLabel('Choose a feature heights raster. [optional]')

        global scale_h_in
        scale_h_in = QtWidgets.QSpinBox()
        scale_h_label = QtWidgets.QLabel('Horizontal Scale:')
        scale_h_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        scale_h_in.setValue(1)
        scale_h_in.setMinimum(1)
        scale_h_in.setPrefix('1:')

        global scale_v_in
        scale_v_in = QtWidgets.QDoubleSpinBox()
        scale_v_label = QtWidgets.QLabel('Vertical Scale:')
        scale_v_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        scale_v_in.setValue(1)
        scale_v_in.setRange(-1024,1024)
        scale_v_in.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        scale_v_in.setPrefix('1:')

        global auto_scale_in
        auto_scale_in = QtWidgets.QCheckBox()
        auto_scale_label = QtWidgets.QLabel('Vertical AutoScale:')
        auto_scale_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        global water_level_in
        water_level_in = QtWidgets.QDoubleSpinBox()
        water_label = QtWidgets.QLabel('Water Level:')
        water_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        water_level_in.setValue(1)
        water_level_in.setRange(-10000,10000)
        water_level_in.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)

        global baseline_height_in
        baseline_height_in = QtWidgets.QSpinBox()
        baseline_height_label = QtWidgets.QLabel('Baseline Height:')
        baseline_height_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        baseline_height_in.setValue(5)
        baseline_height_in.setRange(-9000,256)

        global block_in
        block_in = QtWidgets.QComboBox()
        block_in.setEditable(True)
        block_label = QtWidgets.QLabel('Main Block:')
        block_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        block_in.addItems(blockList)

        global top_block_in
        top_block_in = QtWidgets.QComboBox()
        top_block_in.setEditable(True)
        top_block_label = QtWidgets.QLabel('Top Block:')
        top_block_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        top_block_in.addItems(blockList)

        global use_half_blocks_in
        use_half_blocks_in = QtWidgets.QCheckBox()
        use_half_blocks_label = QtWidgets.QLabel('Use half blocks:')
        use_half_blocks_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        global half_blockType_in
        half_blockType_in = QtWidgets.QComboBox()
        half_blockType_in.setEditable(True)
        half_blockType_label = QtWidgets.QLabel('Half Block:')
        half_blockType_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        half_blockType_in.addItems(half_blockList)

        global use_forestCheck_in
        use_forestCheck_in = QtWidgets.QCheckBox()
        use_forestCheck_label = QtWidgets.QLabel('Add Forest:')
        use_forestCheck_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        global forest_freq_in
        forest_freq_in = QtWidgets.QSpinBox()
        forest_freq_label = QtWidgets.QLabel('Forest Frequency:')
        forest_freq_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        forest_freq_in.setValue(25)
        forest_freq_in.setMinimum(4)
        forest_freq_in.setPrefix('1/')

        global tree_types_in
        tree_types_in = QtWidgets.QListWidget()
        tree_types_label = QtWidgets.QLabel('Tree Type(s)')
        tree_types_label.setAlignment(QtCore.Qt.AlignVCenter)
        tree_types_in.addItems(treeList)
        tree_types_in.setSelectionMode(QtWidgets.QListWidget.MultiSelection)

        global use_large_trees_in
        use_large_trees_in = QtWidgets.QCheckBox()
        use_large_trees_label = QtWidgets.QLabel('Use Large Trees:')
        use_large_trees_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        global large_trees_freq_in
        large_trees_freq_in = QtWidgets.QSpinBox()
        large_trees_freq_label = QtWidgets.QLabel('Large Trees Frequency:')
        large_trees_freq_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        large_trees_freq_in.setValue(25)
        large_trees_freq_in.setMinimum(1)
        large_trees_freq_in.setPrefix('1/')

        global classifier_dict_in
        classifier_dict_in = QtWidgets.QTableWidget(1,2)
        classifier_dict_label = QtWidgets.QLabel('Classifier Raster Classes')
        table_headers = ['Id','Block']
        classifier_dict_in.setHorizontalHeaderLabels(table_headers)

        global features_dict_in
        features_dict_in = QtWidgets.QTableWidget(1,2)
        features_dict_label = QtWidgets.QLabel('Features Raster Classes')
        table_headers = ['Id','Block']
        features_dict_in.setHorizontalHeaderLabels(table_headers)

        self.open = QtWidgets.QPushButton('Open File')
        self.out = QtWidgets.QPushButton('Select Output Directory')
        self.open_classifier = QtWidgets.QPushButton('Open Classifier Raster')
        self.open_classifier_dict = QtWidgets.QPushButton('Load Classifier Dictionary from File')
        self.save_classifier_dict = QtWidgets.QPushButton('Save Classifier Dictionary to File')
        self.open_features = QtWidgets.QPushButton('Open Features Raster')
        self.open_features_heights = QtWidgets.QPushButton('Open Feature Heights Raster')
        self.open_features_dict = QtWidgets.QPushButton('Load Features Dictionary from File')
        self.save_features_dict = QtWidgets.QPushButton('Save Features Dictionary to File')
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
        self.features_heights_in_layout.addWidget(self.open_features_heights_label)
        self.features_heights_in_layout.addWidget(self.open_features_heights)

        self.io_layout.addItem(self.file_layout)
        self.io_layout.addItem(self.out_layout)
        self.io_layout.addItem(self.classifier_in_layout)
        self.io_layout.addItem(self.features_in_layout)
        self.io_layout.addItem(self.features_heights_in_layout)
        self.io_box.setLayout(self.io_layout)


        self.settings_layout.addWidget(scale_h_label,0,0)
        self.settings_layout.addWidget(scale_h_in,0,1)
        self.settings_layout.addWidget(scale_v_label,1,0)
        self.settings_layout.addWidget(scale_v_in,1,1)
        self.settings_layout.addWidget(auto_scale_label,2,0)
        self.settings_layout.addWidget(auto_scale_in,2,1)

        self.settings_layout.addWidget(water_label,0,2)
        self.settings_layout.addWidget(water_level_in,0,3)
        self.settings_layout.addWidget(baseline_height_label,1,2)
        self.settings_layout.addWidget(baseline_height_in,1,3)

        self.settings_layout.addWidget(block_label,3,0)
        self.settings_layout.addWidget(block_in,3,1)
        self.settings_layout.addWidget(top_block_label,3,2)
        self.settings_layout.addWidget(top_block_in,3,3)
        self.settings_layout.addWidget(use_half_blocks_label,4,0)
        self.settings_layout.addWidget(use_half_blocks_in,4,1)
        self.settings_layout.addWidget(half_blockType_label,4,2)
        self.settings_layout.addWidget(half_blockType_in,4,3)

        self.forest_layout.addWidget(use_forestCheck_label,0,0)
        self.forest_layout.addWidget(use_forestCheck_in,0,1)
        self.forest_layout.addWidget(forest_freq_label,0,2)
        self.forest_layout.addWidget(forest_freq_in,0,3)
        self.forest_layout.addWidget(use_large_trees_label,1,0)
        self.forest_layout.addWidget(use_large_trees_in,1,1)
        self.forest_layout.addWidget(large_trees_freq_label,1,2)
        self.forest_layout.addWidget(large_trees_freq_in,1,3)
        self.forest_layout.addWidget(tree_types_label,2,0)
        self.forest_layout.addWidget(tree_types_in,3,0,1,4)

        self.use_forest_box.setLayout(self.forest_layout)
        self.settings_layout.addWidget(self.use_forest_box,5,0,1,4)


        self.classifier_layout.addWidget(classifier_dict_in,0,0,1,2)
        self.classifier_layout.addWidget(self.open_classifier_dict,1,0)
        self.classifier_layout.addWidget(self.save_classifier_dict,1,1)
        self.classifier_box.setLayout(self.classifier_layout)

        self.features_layout.addWidget(features_dict_in,0,0,1,2)
        self.features_layout.addWidget(self.open_features_dict,1,0)
        self.features_layout.addWidget(self.save_features_dict,1,1)
        self.features_box.setLayout(self.features_layout)

        self.settings_layout.addWidget(self.classifier_box,6,0,1,4)
        self.settings_layout.addWidget(self.features_box,7,0,1,4)

        self.settings_box.setLayout(self.settings_layout)

        self.button_layout.addWidget(self.debug_check_label)
        self.button_layout.addWidget(self.debug_check)
        self.button_layout.addWidget(self.save_config)
        self.button_layout.addWidget(self.load_config)
        self.button_layout.addWidget(self.run)
        self.button_layout.addWidget(self.close_win)

        self.button_box.setLayout(self.button_layout)

        #self.logLayout.addWidget(self.executeLog.logger)
        #self.logBox.setLayout(self.logLayout)

        self.fileSelected = False
        self.directorySelected = False

        self.close_win.clicked.connect(self.close)
        self.run.clicked.connect(self.executeFromGui)
        self.open.clicked.connect(self.openFile)
        self.out.clicked.connect(self.selectDirectory)
        self.open_classifier.clicked.connect(self.openClassifierFile)
        self.open_features.clicked.connect(self.openFeaturesFile)
        self.open_features_heights.clicked.connect(self.openFeaturesHeightsFile)
        self.open_classifier_dict.clicked.connect(self.openClassifierDictFileDialog)
        self.save_classifier_dict.clicked.connect(self.saveClassifierDictFile)
        self.open_features_dict.clicked.connect(self.openFeaturesDictFileDialog)
        self.save_features_dict.clicked.connect(self.saveFeaturesDictFile)
        self.debug_check.stateChanged.connect(self.setDebugModeGUI)
        self.save_config.clicked.connect(self.saveSettingsDialog)
        self.load_config.clicked.connect(self.loadSettingsDialog)
        features_dict_in.cellChanged.connect(self.addRow)
        classifier_dict_in.cellChanged.connect(self.addRow)

        if config_file_bool:
            global config_settings_section
            self.setFromConfig(config_settings_section)

    def executeFromGui(self):
        self.run.setEnabled(False)
        execute()
        self.run.setEnabled(True)

    def setFromConfig(self,section):
        global settings
        settings = loadFromConfig(section)

        if settings['file'] != '' and settings['file'] is not None:
            self.file_label.setText('DEM: {}'.format(settings['file']))
            self.fileSelected = True

        if settings['directory'] != '' and  settings['directory'] is not None:
            self.out_label.setText('Output Directory: {}'.format(settings['directory']))
            self.directorySelected = True
            if self.fileSelected == True:
                self.run.setEnabled(True)

        if settings['classifier_file'] != '' and settings['classifier_file'] is not None:
            self.open_classifier_label.setText('Classifier Raster: {}'.format(settings['classifier_file']))

        if settings['features_file'] != '' and settings['features_file'] is not None:
            self.open_features_label.setText('Features Raster: {}'.format(settings['features_file']))

        if settings['features_heights_file'] != '' and settings['features_heights_file'] is not None:
            self.open_features_heights_label.setText('Feature Heights Raster: {}'.format(settings['features_heights_file']))

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
        forest_freq_in.setValue(settings['forest_freq'])

        for tree in settings['tree_types']:
            matching_items = tree_types_in.findItems(tree, QtCore.Qt.MatchExactly)
            for item in matching_items:
                item.setSelected(True)

        use_large_trees_in.setChecked(settings['use_large_trees'])
        large_trees_freq_in.setValue(settings['large_trees_freq'])

        classifier_dict_from_file = openDictFile(settings['classifier_dict_file'])
        if classifier_dict_from_file is not None:
            for i in range(len(classifier_dict_from_file)):
                classifier_id = QtWidgets.QTableWidgetItem(str(classifier_dict_from_file.iloc[i,0]))
                classifier_block = QtWidgets.QTableWidgetItem(classifier_dict_from_file.iloc[i,1])
                classifier_dict_in.setItem(i,0,classifier_id)
                classifier_dict_in.setItem(i,1,classifier_block)

        features_dict_from_file = openDictFile(settings['features_dict_file'])
        if features_dict_from_file is not None:
            for i in range(len(features_dict_from_file)):
                features_id = QtWidgets.QTableWidgetItem(str(features_dict_from_file.iloc[i,0]))
                features_block = QtWidgets.QTableWidgetItem(features_dict_from_file.iloc[i,1])
                features_dict_in.setItem(i,0,features_id)
                features_dict_in.setItem(i,1,features_block)
        self.debug_check.setChecked(settings['debug_mode'])

    def saveSettingsDialog(self):
        config_sections = config.sections()
        config_section, success = QtWidgets.QInputDialog().getItem(self,'Choose Settings Name','Settings Section Name:',config_sections)
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
        settings['forest_freq'] = forest_freq_in.value()
        settings['tree_types'] = ','.join([item.text() for item in tree_types_in.selectedItems()])
        settings['use_large_trees'] = use_large_trees_in.isChecked()
        settings['large_trees_freq'] = large_trees_freq_in.value()
        settings['auto_scale'] = auto_scale_in.isChecked()
        settings['debug_mode'] = self.debug_check.isChecked()
        if success and bool(config_section):
            saveToConfig(config_section,settings)

    def loadSettingsDialog(self):
        config_sections = config.sections()
        config_section, success = QtWidgets.QInputDialog().getItem(self,'Choose Settings Name','Settings Section Name:',config_sections)
        if success and bool(config_section):
            self.setFromConfig(config_section)

    def addRow(self):
        if self.sender().item(self.sender().rowCount()-1,0) is not None:
            if self.sender().item(self.sender().rowCount()-1,0).text() != '':
                self.sender().insertRow(self.sender().rowCount())
        if self.sender().item(self.sender().rowCount()-1,1) is not None:
            if self.sender().item(self.sender().rowCount()-1,1).text() != '':
                self.sender().insertRow(self.sender().rowCount())
        for i in range(self.sender().rowCount()-1):
            if self.sender().item(i,0) is not None:
                if self.sender().item(i,1) is not None:
                    if self.sender().item(i,1).text() == '' and self.sender().item(i,0) == '':
                        self.sender().removeRow(i)
                elif self.sender().item(i,0).text() == '':
                    self.sender().removeRow(i)
            elif self.sender().item(i,1) is not None:
                if self.sender().item(i,1).text() == '':
                    self.sender().removeRow(i)
            else:
                self.sender().removeRow(i)

    def close(self):
        QtWidgets.QWidget.close(self)

    def openFile(self):
        global settings
        file_open_dialog = QtWidgets.QFileDialog(self)
        settings['file'] = file_open_dialog.getOpenFileName(self,'Open File','','GDAL Raster Formats (*.asc *.tif *.tiff *.adf *.ACE2 *.gen *.thf *.arg *.bsb *.bt *.ctg *.dds *.dimap *.doq1 *.doq2 *.e00grid *.hdr *.eir *.fits *.grd *.gxf *.ida *.mpr *.isce *.mem *.kro *.gis *.lan *.mff *.ndf *.gmt *.aux *.png *.pgm *.slc *.int *.gri *.sdat *.sdts *.sgi *.snodas *.hgt *.xpm *.gff *.zmap);;Any File (*)')[0]
        if settings['file'] == '':
            logger.info('No File Chosen. Please Choose a File')
        else:
            logger.info('DEM: {}'.format(settings['file']))
            if not self.directorySelected:
                settings['directory'] = os.path.dirname(settings['file'])
                self.out_label.setText('Output Directory: {}'.format(settings['directory']))
                logger.info('Output Directory: {}'.format(settings['directory']))
            self.run.setEnabled(True)
            self.fileSelected = True
            self.file_label.setText('DEM: {}'.format(settings['file']))

    def selectDirectory(self):
        global settings
        file_direct_dialog = QtWidgets.QFileDialog(self)
        settings['directory'] = file_direct_dialog.getExistingDirectory(self,'Select Output Directory')
        if settings['directory'] == '':
            logger.info('No Directory Chosen. Please Choose a Directory')
        else:
            if self.fileSelected:
                self.run.setEnabled(True)
            self.directorySelected = True
            self.out_label.setText('Output Directory: {}'.format(settings['directory']))
            logger.info('Output Directory: {}'.format(settings['directory']))

    def openClassifierFile(self):
        global settings
        file_open_dialog = QtWidgets.QFileDialog(self)
        settings['classifier_file'] = file_open_dialog.getOpenFileName(self,'Open File','','GDAL Raster Formats (*.asc *.tif *.tiff *.adf *.ACE2 *.gen *.thf *.arg *.bsb *.bt *.ctg *.dds *.dimap *.doq1 *.doq2 *.e00grid *.hdr *.eir *.fits *.grd *.gxf *.ida *.mpr *.isce *.mem *.kro *.gis *.lan *.mff *.ndf *.gmt *.aux *.png *.pgm *.slc *.int *.gri *.sdat *.sdts *.sgi *.snodas *.hgt *.xpm *.gff *.zmap);;Any File (*)')[0]
        if settings['classifier_file'] == '':
            logger.info('No File Chosen. Please Choose a File')
        else:
            self.rasterSelected = True
            self.open_classifier_label.setText('Classifier Raster: {}'.format(settings['classifier_file']))
            logger.info('Classifier Raster: {}'.format(settings['classifier_file']))

    def openClassifierDictFileDialog(self):
        global settings
        classifier_dict_file_dialog = QtWidgets.QFileDialog(self)
        settings['classifier_dict_file'] = classifier_dict_file_dialog.getOpenFileName(self,'Open File','','CSV File (*.csv);;Any File (*)')[0]
        classifier_dict_from_file = openDictFile(settings['classifier_dict_file'])
        for i in range(len(classifier_dict_from_file)):
            classifier_id = QtWidgets.QTableWidgetItem(str(classifier_dict_from_file.iloc[i,0]))
            classifier_block = QtWidgets.QTableWidgetItem(classifier_dict_from_file.iloc[i,1])
            classifier_dict_in.setItem(i,0,classifier_id)
            classifier_dict_in.setItem(i,1,classifier_block)

    def saveClassifierDictFile(self):
        global settings
        classifier_dict_file_dialog = QtWidgets.QFileDialog(self)
        settings['classifier_dict_file'] = classifier_dict_file_dialog.getSaveFileName(self,'Save File','','CSV File (*.csv);;Any File (*)')[0]
        classifier_dict_out = tableWidgetToDF(classifier_dict_in)
        classifier_dict_out.to_csv(settings['classifier_dict_file'],index=False,header=False)

    def openFeaturesFile(self):
        global settings
        file_open_dialog = QtWidgets.QFileDialog(self)
        settings['features_file'] = file_open_dialog.getOpenFileName(self,'Open File','','GDAL Raster Formats (*.asc *.tif *.tiff *.adf *.ACE2 *.gen *.thf *.arg *.bsb *.bt *.ctg *.dds *.dimap *.doq1 *.doq2 *.e00grid *.hdr *.eir *.fits *.grd *.gxf *.ida *.mpr *.isce *.mem *.kro *.gis *.lan *.mff *.ndf *.gmt *.aux *.png *.pgm *.slc *.int *.gri *.sdat *.sdts *.sgi *.snodas *.hgt *.xpm *.gff *.zmap);;Any File (*)')[0]
        if features_file == '':
            logger.info('No File Chosen. Please Choose a File')
        else:
            self.rasterSelected = True
            self.open_features_label.setText('Features Raster: {}'.format(settings['features_file']))
            logger.info('Features Raster: {}'.format(settings['features_file']))

    def openFeaturesHeightsFile(self):
        global settings
        file_open_dialog = QtWidgets.QFileDialog(self)
        settings['features_heights_file'] = file_open_dialog.getOpenFileName(self,'Open File','','GDAL Raster Formats (*.asc *.tif *.tiff *.adf *.ACE2 *.gen *.thf *.arg *.bsb *.bt *.ctg *.dds *.dimap *.doq1 *.doq2 *.e00grid *.hdr *.eir *.fits *.grd *.gxf *.ida *.mpr *.isce *.mem *.kro *.gis *.lan *.mff *.ndf *.gmt *.aux *.png *.pgm *.slc *.int *.gri *.sdat *.sdts *.sgi *.snodas *.hgt *.xpm *.gff *.zmap);;Any File (*)')[0]
        if features_heights_file == '':
            logger.info('No File Chosen. Please Choose a File')
        else:
            self.rasterSelected = True
            self.open_features_heights_label.setText('Feature Heights Raster: {}'.format(settings['features_heights_file']))
            logger.info('Feature Heights Raster: {}'.format(settings['features_heights_file']))

    def openFeaturesDictFileDialog(self):
        global settings
        features_dict_file_dialog = QtWidgets.QFileDialog(self)
        settings['features_dict_file'] = features_dict_file_dialog.getOpenFileName(self,'Open File','','CSV File (*.csv);;Any File (*)')[0]
        features_dict_from_file = openDictFile(settings['features_dict_file'])
        if features_dict_from_file is not None:
            for i in range(len(features_dict_from_file)):
                features_id = QtWidgets.QTableWidgetItem(str(features_dict_from_file.iloc[i,0]))
                features_block = QtWidgets.QTableWidgetItem(features_dict_from_file.iloc[i,1])
                features_dict_in.setItem(i,0,features_id)
                features_dict_in.setItem(i,1,features_block)

    def saveFeaturesDictFile(self):
        features_dict_file_dialog = QtWidgets.QFileDialog(self)
        settings['features_dict_file'] = features_dict_file_dialog.getSaveFileName(self,'Save File','','CSV File (*.csv);;Any File (*)')[0]
        features_dict_out = tableWidgetToDF(features_dict_in)
        features_dict_out.to_csv(settings['features_dict_file'],index=False,header=False)

    def setDebugModeGUI(self):
            if self.sender().isChecked():
                log_to_console.setLevel(logging.DEBUG)
                logger.info('Changing to Debug Mode')
            else:
                logger.info('Changing to Normal Mode')
                log_to_console.setLevel(logging.INFO)

def setDebugMode(debug_mode):
        if debug_mode:
            logger.info('Running in Debug Mode')
            log_to_console.setLevel(logging.DEBUG)
        else:
            log_to_console.setLevel(logging.INFO)


def openDictFile(dict_file):
    if dict_file != '' and dict_file is not None:
        dict_from_file = pd.read_csv(dict_file,header=None)
        return dict_from_file

def tableWidgetToDF(dict_in):
    dict = []
    for i in range(dict_in.rowCount()):
        item_key = dict_in.item(i,0)
        item_block = dict_in.item(i,1)
        if item_key is not None:
            if item_block is not None:
                dict.append([int(item_key.text()),item_block.text()])
    dict_out = pd.DataFrame(dict)
    return dict_out

def execute():
    global gui
    global settings
    global classifier_dict_in
    global features_dict_in
    #self.executeLog = QTextEditLogger(self)
    #self.executeLog.setFormatter(log_format)
    #logging.getLogger().addHandler(self.executeLog)
    #logging.getLogger().setLevel(logging.DEBUG)



    if settings['file'] == '' or settings['file'] is None:
        logger.critical('No DEM File Set. Please Set a File.')

    start = time.perf_counter()
    number_of_blocks = 0

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
        settings['forest_freq'] = forest_freq_in.value()
        settings['tree_types'] = [item.text() for item in tree_types_in.selectedItems()]
        settings['use_large_trees'] = use_large_trees_in.isChecked()
        settings['large_trees_freq'] = large_trees_freq_in.value()
        settings['auto_scale'] = auto_scale_in.isChecked()

    file = settings['file']
    directory = settings['directory']
    classifier_file = settings['classifier_file']
    features_file = settings['features_file']
    features_heights_file = settings['features_heights_file']
    classifier_dict_file = settings['classifier_dict_file']
    features_dict_file = settings['features_dict_file']
    water_level = settings['water_level']
    baseline_height = settings['baseline_height']
    scale_h = settings['scale_h']
    scale_v = settings['scale_v']
    block_name = settings['block_name']
    top_block_name = settings['top_block_name']
    half_block_name = settings['half_block_name']
    use_half_blocks = settings['use_half_blocks']
    use_forest = settings['use_forest']
    forest_freq = settings['forest_freq']
    tree_types = settings['tree_types']
    use_large_trees = settings['use_large_trees']
    large_trees_freq = settings['large_trees_freq']
    auto_scale = settings['auto_scale']
    debug_mode = settings['debug_mode']
    setDebugMode(debug_mode)

    water_height = water_level + baseline_height

    if tree_types == []:
        tree_types= ['oak']

    if use_half_blocks:
        quant = 0.5
    else:
        quant = 1

    if scale_v == 0:
        logger.warning('Vertical scale cannot be 0, please use a different value. Continuing with AutoScale.')
        auto_scale = True

    for block in [block_name,top_block_name]:
        if block not in all_blocks:
            logger.warning('A block name used ({}), is not recognised as a valid block or fluid. I will try anyway, but may not succeed.'.format(block))
    if half_block_name not in all_blocks:
        logger.warning('The half block name used ({}), is not recognised as a valid block. I will try anyway, but may not succeed.'.format(half_block_name))
    elif half_block_name not in all_half_blocks:
        logger.warning('The half block name used ({}), is not recognised as a valid half block. I will still succeed, but you may not achieve your desired result.'.format(half_block_name))


    block = anvil.Block('minecraft',str(str(block_name)))
    half_block = anvil.Block('minecraft',str(half_block_name))
    top_block = anvil.Block('minecraft',str(top_block_name))

    logger.info('Horizontal Scale: {}\n \
    Vertical Scale: {}\n \
    Water Level: {}\n \
    Baseline Height: {}\n \
    Main Block: {}\n \
    Top Block: {}\n \
    Half Block: {}\n \
    Using Half Blocks? {}\n\
    Output Directory: {}'.format(scale_h,scale_v,water_level,baseline_height,block_name,top_block_name,half_block_name,use_half_blocks,directory))

    logger.info('Importing Data')

    dem_in = gdal.Open(file)
    dem = np.rot90(np.flip(dem_in.ReadAsArray(),1))

    if classifier_file != '':
        logger.debug('Classifier file found')
        classifier_in = gdal.Open(classifier_file)
        classifier = np.rot90(np.flip(classifier_in.ReadAsArray(),1))

    if features_file != '':
        features_in = gdal.Open(features_file)
        features = np.rot90(np.flip(features_in.ReadAsArray(),1))

    if features_heights_file != '':
        features_heights_in = gdal.Open(features_heights_file)
        features_heights = np.rot90(np.flip(features_heights_in.ReadAsArray(),1))

    del dem_in

    logger.info('Scaling Horizontally')

    def h_scale(data,scale_h):
        data_lists = []
        if scale_h != 1:
            for n in range(int(len(data[:,0])/scale_h)):
                row=[]
                for m in range(int(len(data[0,:])/scale_h)):
                    row.append(data[n*scale_h:n*scale_h+scale_h,m*scale_h:m*scale_h+scale_h].max())
                data_lists.append(row)
        else:
            data_lists = data
        return data_lists

    data = pd.DataFrame(h_scale(dem,scale_h))

    if classifier_file != '':
        Classifier = pd.DataFrame(h_scale(classifier,scale_h))
    if features_file != '':
        Features = pd.DataFrame(h_scale(features,scale_h))
    if features_heights_file != '':
        Features_heights = pd.DataFrame(h_scale(features_heights,scale_h))

    logger.info('Scaling Vertically')

    del dem


    def vert_scale(number,scale=scale_v):
        return number/scale

    if auto_scale:
        logger.info('Autoscaling')
        demHeight = max(data.max()) - min(data.min())
        auto_scaleV = demHeight/254
        scale_v = max(auto_scaleV,scale_v)
        baseline_height = np.floor(1-min(data.min())/scale_v)
        logger.info('Vertical Scale: {}, Baseline Height: {}'.format(scale_v,baseline_height))

    if scale_v != 1:
        data_v_scaled = data.applymap(vert_scale)
    else:
        data_v_scaled = data

    logger.info('Rounding elevations to nearest half metre')

    del data

    Data = data_v_scaled.applymap(flex_round)

    del data_v_scaled

    if max(Data.max())/scale_v + baseline_height > 255:
        over_tall = max(Data.max()) - 255
        logger.warning('Data {} blocks too tall, try increasing the vertical scale, or reducing the baseline height (even making it negative if necessary), or use the AutoScale option. I will truncate any too tall stacks.'.format(over_tall))

    if bool(settings['classifier_file']):
        classifier_dict = {}
        if gui:
            classifier_dict_in = tableWidgetToDF(classifier_dict_in)
        else:
            classifier_dict_in = openDictFile(settings['classifier_dict_file'])
        for i in range(len(classifier_dict_in)):
            item_key = classifier_dict_in.iloc[i,0]
            item_block = classifier_dict_in.iloc[i,1]
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

    if bool(settings['features_file']):
        features_dict = {}
        if gui:
            features_dict_in = tableWidgetToDF(features_dict_in)
        else:
            features_dict_in = openDictFile(settings['features_dict_file'])
        for i in range(len(features_dict_in)):
            item_key = features_dict_in.iloc[i,0]
            item_block = features_dict_in.iloc[i,0]
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

    x_len = len(Data.iloc[:,0])
    z_len = len(Data.iloc[0,:])

    logger.info('x size:{}\n \
                    z size:{}'.format(x_len,z_len))

    logger.info('Calculating number of regions required')

    x_regions = int(np.ceil(x_len/512))
    z_regions = int(np.ceil(z_len/512))

    logger.info('Regions: {}, {}'.format(x_regions, z_regions))

    logger.debug('Local variables: {}\nGlobal Variables: {}'.format(locals(),globals()))

    for x_region in range(x_regions):
        for z_region in range(z_regions):

            logger.info('Creating Minecraft Region: {}, {}'.format(x_region,z_region))

            region = anvil.EmptyRegion(x_region,z_region)

            logger.info('Region: {}, {}'.format(x_region,z_region))

            for region_x in range(min(512,x_len-(x_region)*512)):
                for region_z in range(min(512,z_len-(z_region)*512)):
                    x = region_x + x_region*512
                    z = region_z + z_region*512
                    if classified:
                        top_block_name = str(classifier_dict[Classifier.iloc[x,z]])
                        top_block = anvil.Block('minecraft',str(top_block_name))
                    if Data.iloc[x,z] + baseline_height < 255:
                        y_range = int(Data.iloc[x,z]+baseline_height)
                    else:
                        y_range = 255
                    if z%512 == 0 and x%64 == 0:
                        logger.info('Current Rows: {} to {} of {}, Columns: {} to {} of {}, Blocks before now: {}, Region: {}, {}, Time: {}'.format(z,min(z+511,z_len),z_len,x,min(x+63,x_len),x_len,number_of_blocks,x_region,z_region,time.perf_counter()-start))
                    if z%512 == 0 and x%64 != 0:
                        logger.debug('Current Rows: {} to {} of {}, Column: {} of {}, Blocks before now: {}, Region: {}, {}, Time: {}'.format(z,min(z+511,z_len),z_len,x,x_len,number_of_blocks,x_region,z_region,time.perf_counter()-start)))
                    if Data.iloc[x,z] == -9999:
                        pass
                    elif Data.iloc[x,z] <= water_level:
                        region.set_block(bedrock, x, 0, z)
                        number_of_blocks += 1
                        for y in range(1,water_height):
                            region.set_block(water, x, y, z)
                            number_of_blocks += 1
                    elif Data.iloc[x,z]%1 == 0 or use_half_blocks == False:
                        for y in range(y_range):
                            if y == 0:
                                region.set_block(bedrock, x, y, z)
                                number_of_blocks += 1
                            elif y != y_range - 1:
                                region.set_block(block, x, y, z)
                                number_of_blocks += 1
                            else:
                                region.set_block(top_block, x, y, z)
                                number_of_blocks += 1
                                if random.randrange(forest_freq) == 0 and use_forest and top_block_name in ['dirt','grass_block','podzol'] and y < 254:
                                    tree = random.choice(tree_types)
                                    if (tree == 'dark_oak' or ((tree == 'jungle' or tree == 'spruce') and random.randrange(large_trees_freq) == 0 and use_large_trees)) and (x not in (0,511) and z not in (0,511)):
                                        if x+1 < x_len and z+1 < z_len:
                                            sq_rd = (Data.iloc[x+1,z] and Data.iloc[x,z+1] and Data.iloc[x+1,z+1]) == Data.iloc[x,z]
                                        else:
                                            sq_rd = False
                                        if x+1 < x_len:
                                            sq_ru = (Data.iloc[x+1,z] and Data.iloc[x,z-1] and Data.iloc[x+1,z-1]) == Data.iloc[x,z]
                                        else:
                                            sq_ru = False
                                        if z+1 < z_len:
                                            sq_ld = (Data.iloc[x-1,z] and Data.iloc[x,z+1] and Data.iloc[x-1,z+1]) == Data.iloc[x,z]
                                        else:
                                            sq_ld = False

                                        sq_lu = (Data.iloc[x-1,z] and Data.iloc[x,z-1] and Data.iloc[x-1,z-1]) == Data.iloc[x,z]


                                        if sq_rd:
                                            for x,z in zip([x,x,x+1,x+1],[z,z+1,z,z+1]):
                                                region.set_block(anvil.Block('minecraft',str(tree+'_sapling')),x,y+1,z)
                                                number_of_blocks += 1
                                                #logger.info(tree+' large')
                                        elif sq_ld:
                                            for x,z in zip([x,x,x-1,x-1],[z,z+1,z,z+1]):
                                                region.set_block(anvil.Block('minecraft',str(tree+'_sapling')),x,y+1,z)
                                                number_of_blocks += 1
                                                #logger.info(tree+' large')
                                        elif sq_lu:
                                            for x,z in zip([x,x,x-1,x-1],[z,z-1,z,z-1]):
                                                region.set_block(anvil.Block('minecraft',str(tree+'_sapling')),x,y+1,z)
                                                number_of_blocks += 1
                                                #logger.info(tree+' large')
                                        elif sq_ru:
                                            for x,z in zip([x,x,x+1,x+1],[z,z-1,z,z-1]):
                                                region.set_block(anvil.Block('minecraft',str(tree+'_sapling')),x,y+1,z)
                                                number_of_blocks += 1
                                                #logger.info(tree+' large')
                                        elif tree == 'dark_oak':
                                            region.set_block(anvil.Block('minecraft',str('oak_sapling')),x,y+1,z)
                                            number_of_blocks += 1
                                            #logger.info('dark oak failed: {} {} {} {}'.format(y,Data.iloc[x+1,z],Data.iloc[x,z+1],Data.iloc[x+1,z+1]))
                                        else:
                                            region.set_block(anvil.Block('minecraft',str(tree+'_sapling')),x,y+1,z)
                                            number_of_blocks += 1
                                            #logger.info('large tree failed: {} {} {} {}'.format(y,Data.iloc[x+1,z],Data.iloc[x,z+1],Data.iloc[x+1,z+1]))
                                    else:
                                        region.set_block(anvil.Block('minecraft',str(tree+'_sapling')),x,y+1,z)
                                        number_of_blocks += 1
                                        #logger.info(tree)
                                if use_features and features_dict[Features.iloc[x,z]] is not None:
                                    if str(features_dict[Features.iloc[x,z]]).lower() not in ('0','none'):
                                        feature_bool = True
                                        feature_block = anvil.Block(features_dict[Features.iloc[x,z]])
                                        for h in range(Features_heights.iloc[x,z]):
                                            yObj = y + 1 + h
                                            region.set_block(feature_block,x,yObj,z)
                                            number_of_blocks += 1
                    else:
                        for y in range(y_range):
                            if y == 0:
                                region.set_block(bedrock, x, y, z)
                                number_of_blocks += 1
                            elif y != y_range - 1:
                                region.set_block(block, x, y, z)
                                number_of_blocks += 1
                            else:
                                region.set_block(block, x, y, z)
                                number_of_blocks += 1
                                region.set_block(half_block, x, y_range, z)
                                number_of_blocks += 1
            #Previous code for completing the region to avoid having large gaps at the edges.
            #if x_region == x_regions - 1 or z_region == z_regions - 1:
            #    if x_len%512 != 0:
            #        for x in range(x_len,x_regions*512):
            #            for z in range((z_region)*512,(z_region+1)*512):
            #                if (x%16 == 0 and z%16 == 0):
            #                    logger.info('Current Chunk: {},~,{}'.format(int(x/16),int(z/16)))
            #                region.set_block(bedrock, x, 0, z)
            #                number_of_blocks += 1
            #                for y in range(1,water_height):
            #                    region.set_block(water, x, y, z)
            #                    number_of_blocks += 1
            #    if z_len%512 !=0:
            #        for z in range(z_len,z_regions*512):
            #            for x in range((x_region)*512,(x_region+1)*512):
            #                if (x%16 == 0 and z%16 == 0):
            #                    logger.info('Current Chunk: {},~,{}'.format(int(x/16),int(z/16)))
            #                region.set_block(bedrock, x, 0, z)
            #                number_of_blocks += 1
            #                for y in range(1,water_height):
            #                    region.set_block(water, x, y, z)
            #                    number_of_blocks += 1

            logger.info('Saving Minecraft Region: {}, {}: {}/r.{}.{}.mca'.format(x_region,z_region,directory,x_region,z_region))
            region.save('{}/r.{}.{}.mca'.format(directory,x_region,z_region))
    finish = time.perf_counter()
    logger.info('Done. Wrote {} blocks, taking {:.2f}s'.format(number_of_blocks,finish-start))

if gui:
    if __name__ == '__main__':
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])

        widget = win()
        widget.show()

        sys.exit(app.exec_())
else:
    execute()
