# Example: Falnash
This example is an [area near Lithgow in NSW, Australia][1]. The world has been generated at 1 block to every 6 horizontal metres and 1 block to every 3 vertical metres. The example is not complete, but can give an idea about what the generator is capable of, and maybe what to look out for when building data to be used. An orienteering map of the area is available [here][2].

Some notes:
- due to an error by the author in creating data, some of the surface and feature blocks are not generated ideally.
- any feature that relies on awareness of neighbouring features to look correct will need some interaction to achieve the desired look due to how Minecraft deals with things like iron bars and fences. This is noticeable in this example.
- trees are generated as saplings, hence will need time to grow. This time can be reduced to practically nothing (for those trees within a certain radius), by using the minecraft command /gamerule randomTickSpeed 1000. The default random tick speed is 3, so this represents a significant speed up.
- the generated world does not quite cover the entirety of the orienteering map, missing some to the south and west, and a few metres in the north.

[1]: https://goo.gl/maps/WkiwqQjg5odA93uJA
[2]: https://routegadget.bigfootorienteers.com/cgi-bin/reitti.cgi?act=map&id=48&kieli=