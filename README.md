# DEMtoMC
Script (with optional GUI) to Convert a DEM to a Minecraft world


## Requirements
Requires Python 3 (tested on Python 3.8.3)

Python Packages  
-	anvil (pip install anvil-parser)  
-	numpy (pip install numpy)  
-	pandas (pip install pandas)  
-	matplotlib (pip install matplotlib)  
-	PySide2 (pip install PySide2)  
- osgeo (pip install GDAL, this has been known to fail, an alternative is to download a wheel from here: https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal and use pip install [wheel file])

## Usage
This script generates Minecraft anvil files, that can be copied into the "region" folder of any Minecraft world. It is suggested to generate a new world before starting. Suggested world options are super flat with preset settings: "minecraft:bedrock,5*minecraft:water", replacing the 5 by your the sum of your desired skirt height and your desired water height, less 1.

The classification raster should be ***exactly*** the same size as the DEM, and should have only integer values.

The script accepts any GDAL recognised raster format.

## Settings
**Horizontal Scale (default: 1):** reduction factor in x and z directions. For example, with a horizontal scale of 4, for every 4 cells in the input DEM, the output Minecraft world will have 1 block.  
**Vertical Scale (default: 1):** as for horizontal scale, but in the vertical direction.  
**Water Level (default: 1):** DEM value below which to add water instead of solid blocks.  
**Baseline Height (default: 5):** height above the bottom of the Minecraft World to make the zero point of the DEM.  

**Main Block (default: stone):** the block used for all blocks, with the exception of the top block, in a stack.  
**Top Block (default: stone):** the block used as the top block in a stack, except where that stack is a half integer tall.  
**Use Half Blocks (default: False):** determines whether the nearest half integer or nearest integer is used as the stack height.  
**Half Block Type (default: stone_slab):** the block to be used as the half block, when "Use half blocks" is checked.  

**Add Forest (default: False):** Whether trees (as saplings) should be added to the DEM.  
**Forest Frequency (default: 25):** how often a tree should be added. On average there will be one tree in this many blocks (excluding slabs).  
**Use Large Trees (default: False):** whether large versions of trees should be used.  
**Large Tree Frequency (default: 25):** how often large trees should be used (e.g. if the value is 25, one in every 25 spruce and jungle trees will be attempt the be large). If the appropriate terrain is not available, the small version will be used.  
**Tree Type(s) (default: oak):** the tree types available. Multiple types can be selected. If no type is selected, oak will be used. The trees are randomly selected with equal probability from the available types. If a dark_oak tree is selected, but the location is not valid for a dark_oak tree (i.e. there is a four block square with the same y value), an oak tree will be used instead.

**Classifier Raster**: In the classifier raster box, each row should correspond to one Id, and it's associated Minecraft block. The Id should be an integer, while the Block should use the Minecraft [Namespaced Id](https://minecraft.gamepedia.com/Namespaced_ID).

## License
This software is made available under the GNU LGPL 3.0 License.
