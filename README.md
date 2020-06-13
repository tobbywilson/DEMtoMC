# DEMtoMC
Scripts to Convert a DEM to a Minecraft world

This script generates Minecraft anvil files, that can be copied into the "region" folder of any Minecraft world. It is suggested to generate a new world before starting. Suggested world options are super flat with preset settings: "minecraft:bedrock,5*minecraft:water", replacing the 5 by your the sum of your desired skirt height and your desired water height, less 1.

The script accepts any GDAL recognised raster format.

## Requirements
See `requiremens.txt`

Note: `GDAL` is not always possible to install with `pip` without a pre-downloaded `.whl` file.

#[QuickStart Guide][1]

## License
This software is made available under the GNU LGPL 3.0 License.


[1]: https://github.com/tobbywilson/DEMtoMC/wiki/Quick-Start-Guide
