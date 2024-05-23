import os
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ._settings import get_settings

_MAX_MOVE_NUM_IMG = 500
_fonts = {}
_char_images = {}
_num_images_for_black = []
_num_images_for_white = []


# loads the style's font and creates image resources to speed up processing time.
def load_font(style_name):
    global _fonts, _char_images, _nums_for_black_images, _nums_for_white_images

    # loads the style's font in multiple sizes.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    load_dir = os.path.join(current_dir, "_res", get_settings().STYLE_NAME)
    path = os.path.join(load_dir, "font.ttf")
    for font_size in range(
        get_settings().MIN_CELL_SIZE, get_settings().MAX_CELL_SIZE + 1
    ):
        _fonts[font_size] = ImageFont.truetype(path, font_size)

    # creates raw images for every letter A-Z that will be scaled down later.
    for i in range(ord("a"), ord("z") + 1):
        _char_images[chr(i)] = _render_cropped_text(
            256, chr(i), get_settings().LABEL_COLOR
        )

    # creates the placement symbol and the raw graphics for numbers.
    path = os.path.join(load_dir, "placement.png")
    placement_image = make_color_copy(
        Image.open(path), get_settings().PLACEMENT_MARKER_COLOR
    )
    _num_images_for_black.append(placement_image)
    _num_images_for_white.append(placement_image)
    COLOR_FOR_BLACK = get_settings().NUMBER_COLOR_FOR_BLACK
    COLOR_FOR_WHITE = get_settings().NUMBER_COLOR_FOR_WHITE
    for i in range(1, _MAX_MOVE_NUM_IMG + 1):
        _num_images_for_black.append(_render_cropped_text(256, str(i), COLOR_FOR_BLACK))
        _num_images_for_white.append(_render_cropped_text(256, str(i), COLOR_FOR_WHITE))


# returns a copy of the given <image> with all of its pixels
# changed to the given <color> while maintaining the original alpha channel.
def make_color_copy(image, color):
    data = np.array(image)
    new_color = np.array(color + (255,), dtype=np.uint8)
    alpha_strengths = data[..., 3:] / 255.0
    data = new_color * alpha_strengths
    new_image = Image.fromarray(data.astype(np.uint8))
    return new_image


# returns an image of <cell_size> that contains the given <text>.
# the text inside the result will be relatively scaled by <scale>.
def create_cell_text(cell_size, text, color, scale):
    image = Image.new("RGBA", (cell_size, cell_size), (0, 0, 0, 0))
    if len(text) == 0:
        return image

    # determines what image graphic will be scaled down to fit inside <image>.
    render_as_placement_marker = False
    if len(text) == 1 and ord("a") <= ord(text[0]) <= ord("z"):
        graphic = _char_images[text[0]]
    elif re.fullmatch(r"\d+", text):
        # the <text> only contains digits.
        move_num = int(text)
        if move_num == 0:
            render_as_placement_marker = True
        if move_num <= _MAX_MOVE_NUM_IMG:
            if color == get_settings().NUMBER_COLOR_FOR_BLACK:
                graphic = _num_images_for_black[move_num]
            else:
                graphic = _num_images_for_white[move_num]
        else:
            graphic = _render_cropped_text(cell_size, text, color)
    else:
        graphic = _render_cropped_text(cell_size, text, color)

    # determines the scaling factors for the graphic.
    if render_as_placement_marker:
        new_width = int(cell_size)
        new_height = int(cell_size)
    else:
        w, h = graphic.size
        if w > h:
            # width is fit to the <image>.
            new_width = int(cell_size * scale)
            new_height = int(h * (cell_size / w) * scale)
        elif h > w:
            # height is fit to the <image>.
            new_width = int(w * (cell_size / h) * scale)
            new_height = int(cell_size * scale)
        else:
            new_width = int(cell_size * scale)
            new_height = int(cell_size * scale)

    # scales and then pastes the graphic onto the blank image.
    graphic = graphic.resize((new_width, new_height), resample=Image.LANCZOS)
    center_x = int(cell_size / 2 - new_width / 2)
    center_y = int(cell_size / 2 - new_height / 2)
    image.paste(graphic, (center_x, center_y))
    return image


# returns the resulting image of rendering text
# and cropping it by its bounding box.
def _render_cropped_text(cell_size, text, color):
    PADDING_BOTTOM_PERCENT = 0.03
    LEFTWARD_ONE_CLIP = int(cell_size * 0.06)

    # draws the text onto a blank transparent image.
    image = Image.new("RGBA", (1200, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = _fonts[cell_size]
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((0, 0), text, fill=color, font=font)

    # the text will be centered in some larger bounding box.
    # this bounding box is determined using large chars.
    if ord("a") <= ord(text[0]) <= ord("z"):
        max_bbox = draw.textbbox((0, 0), "b" * len(text), font=font)
    else:
        max_bbox = draw.textbbox((0, 0), "0" * len(text), font=font)

    # determines the cropping box for the drawn text.
    max_bbox_width = max_bbox[2] - max_bbox[0]
    bbox_width = bbox[2] - bbox[0]
    padding_x = (max_bbox_width - bbox_width) / 2
    start_x = int(bbox[0] - padding_x)
    end_x = int(start_x + bbox_width + padding_x * 2)

    if len(text) > 1 and text[0] == "1":
        start_x += LEFTWARD_ONE_CLIP

    max_bbox_height = max_bbox[3] - max_bbox[1]
    if get_settings().CENTER_LABELS_VERTICALLY:
        bbox_height = bbox[3] - bbox[1]
        padding_y = (max_bbox_height - bbox_height) / 2
        start_y = int(bbox[1] - padding_y)
        end_y = int(start_y + bbox_height + padding_y * 2)
    else:
        start_y = bbox[3] - max_bbox_height
        end_y = int(bbox[3] * (1 + PADDING_BOTTOM_PERCENT))

    crop = image.crop((start_x, start_y, end_x, end_y))
    return crop
