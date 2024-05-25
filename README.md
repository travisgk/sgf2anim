![](https://github.com/travisgk/sgf2anim/blob/main/_demo_res/demo_a_res/capturing-race_output.gif)

# sgf2anim
A Python script that can turn an .sgf file for the game of Go into a diagram, static or animated.

<br>
<br>

# Installation
```
pip install pillow imageio
```
[pillow](https://github.com/python-pillow/Pillow) is used for graphics rendering.

[imageio](https://github.com/imageio/imageio) is used for building animated GIF files.

<br>
<br>

# Creating a Diagram
![](https://github.com/travisgk/sgf2anim/blob/main/_demo_res/demo_b_res/surrounded_output.png)
```
import sgf2anim
sgf_path = "my-sgf.sgf"
sgf2anim.save_diagram(sgf_path, save_as_static=True, path_addon="_output")
```
This will create a static diagram and save it as "my-sgf_output.png" in the same directory.
