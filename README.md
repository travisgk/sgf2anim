![](https://github.com/travisgk/sgf2anim/blob/main/_demo_res/demo_c_res/false-eyes_frost.gif)

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
## Static
![](https://github.com/travisgk/sgf2anim/blob/main/_demo_res/demo_b_res/surrounded_output.png)
```
import sgf2anim
sgf_path = "my-sgf.sgf"
sgf2anim.get_settings().set_for_static_diagram()
sgf2anim.save_diagram(sgf_path, save_as_static=True, path_addon="_output")
```
This will create a static diagram and save it as "my-sgf_output.png" in the same directory.

<br>

## Animated
![](https://github.com/travisgk/sgf2anim/blob/main/_demo_res/demo_a_res/capturing-race_output.gif)
```
import sgf2anim
sgf_path = "capturing-race.sgf"

sgf2anim.save_diagram(
    sgf_path,
    save_as_static=False,
    frame_delay_ms=1500,
    start_freeze_ms=3000,
    end_freeze_ms=10000,
    number_display_ms=1000,
    path_addon="_output",
)
```
- ```sgf_path``` provides the path for the SGF file to process.
- ```frame_delay_ms``` is the duration that one node in the SGF will be shown.
- ```start_freeze_ms``` is the duration of the first frame.
- ```end_freeze_ms``` is the duration of the last frame.
- ```number_display_ms``` is the duration of the ```frame_delay_ms``` that will show the move number (or placement marker) on the stone.
- ```path_addon``` is a string that will be added to the output file name (which will be ```sgf_path``` with the extension stripped).

<br>

## Multiple Files at Once
```
import sgf2anim
sgf_dir = "directory"

sgf2anim.process_directory(
    sgf_dir,
    frame_delay_ms=1500,
    start_freeze_ms=3000,
    end_freeze_ms=10000,
    number_display_ms=1000,
    path_addon="_output",
)
```
The ```process_directory``` function will find any SGF files in the given directory and create both a static and animated diagram for all of them.
If an SGF file doesn't contain any played moves, then an animated diagram will not be created.

<br>
<br>

# Styling Settings
```sgf2anim``` contains ```_settings.py```, which defines a ```Settings``` object whose member attributes determine how diagrams will be rendered. ```sgf2anim.get_settings()``` can be used to retrieve the ```Settings``` object and modify its properties before running rendering processes.

- ```MAX_WIDTH``` provides the maximum width of an output diagram image.
- ```MAX_HEIGHT``` provides the maximum height of an output diagram image.
- ```IMAGE_MARGIN``` provides the relative margin around the displayed stones.
- 
<br>

- ```MIN_CELL_SIZE``` provides the smallest size of a graphic that can be used.
- ```MAX_CELL_SIZE``` provides the largest size of a graphic that can be used.

<br>

- ```SHOW_STONE_NUMBERS```, if True, will display a move number/placement marker on the last placed stone.
- ```MAINTAIN_STONE_NUMBERS```, if True, will permanently keep the move number/placement marker on the last placed stone.
- ```MAINTAIN_NUMBERS_AT_END```, if True, will permanently keep the move number/placement marker on the final placed stone.
- ```MARKER_INSTEAD_OF_NUMBERS```, if True, will show a placement marker graphic on the stone instead of the move number.
