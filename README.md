# DEMtoMinecraft
Scripts to Convert a DEM to a Minecraft world


## Requirements
Requires Python 3 (tested on Python 3.8.3)

Python Packages
	anvil (pip install anvil-parser)
	numpy (pip install numpy)
	pandas (pip install pandas)
	matplotlib (pip install matplotlib)
	sys (pip install sys)
	PySide2 (pip install PySide2)

## Usage
This script generates Minecraft anvil files, that can be copied into the "region" folder of any Minecraft world. It is suggested to generate a new world before starting. Suggested world options are super flat with preset settings: "minecraft:bedrock,5*minecraft:water", replacing the 5 by your the sum of your desired skirt height and your desired water height, less 1.

The script accepts any GDAL recognised raster format.

## Settings
Horizontal Scale (default: 1): reduction factor in x and z directions. For example, with a horizontal scale of 4, for every 4 cells in the input DEM, the output Minecraft world will have 1 block.
Vertical Scale (default: 1): as for horizontal scale, but in the vertical direction.
Water Level (default: 1): DEM value below which to add water instead of solid blocks.
Skirt Height (default: 5): height above the bottom of the Minecraft World to make the zero point of the DEM

Main Block: the block used for all blocks, with the exception of the top block, in a stack.
Top Block: the block used as the top block in a stack, except where that stack is a half integer tall.
Use Half Blocks: determines whether the nearest half integer or nearest integer is used as the stack height.
Half Block Type: the block to be used as the half block, when "Use half blocks" is checked.

Add Forest: Whether trees should be added to the DEM
Forest Frequency: how often a tree should be added. On average there will be one tree in this many blocks.
Tree Type(s): the tree types available. Multiple types can be selected. If no type is selected, oak will be used. The trees are randomly selected with equal probability from the available types. If a dark_oak tree is selected, but the location is not valid for a dark_oak tree (i.e. there is a four block square with the same y value), an oak tree will be used instead.
