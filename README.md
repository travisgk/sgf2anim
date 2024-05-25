![](https://github.com/travisgk/sgf2anim/blob/main/_demo_res/demo_c_res/false-eyes_frost.gif)

# sgf2anim
A Python script that can turn an .sgf file for the game of Go/Baduk/Weiqi into a diagram, static or animated.

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
### Static
![](https://github.com/travisgk/sgf2anim/blob/main/_demo_res/demo_b_res/surrounded_output.png)
```
import sgf2anim
sgf_path = "my-sgf.sgf"
sgf2anim.get_settings().set_for_static_diagram()
sgf2anim.save_diagram(sgf_path, save_as_static=True, path_addon="_output")
```
This will create a static diagram and save it as "my-sgf_output.png" in the same directory.

<br>

### Animated
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

### Multiple Files at Once
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

# Styling

### Default Profiles
![](https://github.com/travisgk/sgf2anim/blob/main/_demo_res/demo_a_res/fight_output.png)
```sgf2anim.get_settings().set_for_static_diagram()``` will change the settings to render all the move numbers and not remove captured stones from the diagram.

<br>

![](https://github.com/travisgk/sgf2anim/blob/main/_demo_res/demo_a_res/fight_output.gif)
```sgf2anim.get_settings().set_for_animated_diagram()``` will change the settings to render each placed stone with a temporary placement marker. Captures will be removed.

<br>

### Custom Theme
![](https://github.com/travisgk/sgf2anim/blob/main/_demo_res/demo_c_res/false-eyes_frost.png)
```
import sgf2anim

# defines the graphics directory under sgf2anim/_res to use and the styling properties.
sgf2anim.get_settings().STYLE_NAME = "frost"
sgf2anim.get_settings().DIGIT_TEXT_SCALE_FACTOR = 0.32
sgf2anim.get_settings().LEFTWARD_ONE_CLIP_FACTOR = -0.05
sgf2anim.get_settings().LINE_COLOR = (75, 107, 155)
sgf2anim.get_settings().LINE_THICKNESS = 1.2
sgf2anim.get_settings().MARKER_COLOR = (46, 84, 105)

sgf_path = "false-eyes"
sgf2anim.save_diagram(sgf_path, save_as_static=True, path_addon="_frost")
```

<br>

## Settings

```sgf2anim``` contains ```_settings.py```, which defines a ```Settings``` object whose member attributes determine how diagrams will be rendered. ```sgf2anim.get_settings()``` can be used to retrieve the ```Settings``` object and modify its properties before running rendering processes.

for the resolution of the output images:
- ```MAX_WIDTH``` provides the maximum width of an output diagram image.
- ```MAX_HEIGHT``` provides the maximum height of an output diagram image.
- ```IMAGE_MARGIN``` provides the relative margin around the displayed stones.
- ```MIN_CELL_SIZE``` provides the smallest size of a graphic that can be used.
- ```MAX_CELL_SIZE``` provides the largest size of a graphic that can be used.

<br>

for the appearance of move numbers on stones:
- ```SHOW_STONE_NUMBERS```, if True, will display a move number/placement marker on the last placed stone.
- ```MAINTAIN_STONE_NUMBERS```, if True, will permanently keep the move number/placement marker on the last placed stone.
- ```MAINTAIN_NUMBERS_AT_END```, if True, will permanently keep the move number/placement marker on the final placed stone.
- ```MARKER_INSTEAD_OF_NUMBERS```, if True, will show a placement marker graphic on the stone instead of the move number.
- ```LABEL_TEXT_SCALE``` is the scale of displayed label on an intersection.
- ```NUMBER_TEXT_SCALE``` is the scale of displayed move number on a stone.
- ```DIGIT_TEXT_SCALE_FACTOR``` is added to the ```NUMBER_TEXT_SCALE``` for every digit beyond the first digit.
- ```LEFTWARD_ONE_CLIP_FACTOR``` is the percentage of the move number text image that will be clipped off the left side if the left-most digit is "1" and the move number is not a single digit. This is for accomodating different fonts.
- ```CENTER_LABELS_VERTICALLY```, if True, will vertically center letter labels on their intersections.
- ```LETTERS_PADDING_BOTTOM_PERCENT``` is the percentage of the label text image's height that will be added to the bottom of the image for ideal alignment.
- ```NUMBERS_PADDING_BOTTOM_PERCENT``` is the percentage of the move number text image's height that will be added to the bottom of the image for ideal alignment.

<br>

for the color and line styling:
- ```STYLE_NAME``` is the name of the directory contained in ```sgf2anim/_res``` whose graphics will be loaded.
- ```LINE_COLOR``` is the RGB for the Go board's lines.
- ```LINE_THICKNESS``` is the relative thickness of the Go board's lines.
- ```MARKER_COLOR``` is the RGB for the annotation shapes.
- ```LABEL_COLOR``` is the RGB for the letter label annotations displayed on intersections.
- ```PLACEMENT_MARKER_COLOR``` is the RGB for the stone placement marker.
- ```NUMBER_COLOR_FOR_BLACK``` is the RGB for the move number text appearing on a black stone.
- ```NUMBER_COLOR_FOR_WHITE``` is the RGB for the move number text appearing on a white stone.
- ```ANNOTATE_LINE_COLOR``` is the RGB used for annotative lines.
- ```ANNOTATE_LINE_THICKNESS``` is the relative thickness of annotative lines.

<br>

for other rendering options:
- ```DISPLAY_PADDING``` specifies how many empty intersections should surround the displayed stones.
- ```FORCE_STONES_CENTER```, if True, will change the stone graphic size on a case-by-case basis in order to make them perfectly centered with the Go board's lines.
- ```RENDER_CAPTURES```, if True, will clear captured stones from the diagram.
