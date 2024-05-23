import re
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ._settings import get_settings

_fonts = {}
_char_images = {}
_nums_for_black_images = []
_nums_for_white_images = []
_MAX_MOVE_NUM_IMG = 500


def load_font(style_name):
    # loads fonts for various sizes.
    global _fonts, _char_images, _max_char_dim
    current_directory = os.path.dirname(os.path.abspath(__file__))
    res_dir = os.path.join(current_directory, "_res")
    font_path = os.path.join(res_dir, style_name, "font.ttf")
    for font_size in range(
        get_settings().MIN_CELL_SIZE, get_settings().MAX_CELL_SIZE + 1
    ):
        _fonts[font_size] = ImageFont.truetype(font_path, font_size)
    for i in range(ord("a"), ord("z") + 1):
        _char_images[chr(i)] = _render_cropped_text(256, chr(i), (0, 0, 0, 255))

    # initializes stone numbers and the placement symbol.
    color_for_black = get_settings().NUMBER_COLOR_FOR_BLACK
    color_for_white = get_settings().NUMBER_COLOR_FOR_WHITE
    color_for_marker = get_settings().PLACEMENT_MARKER_COLOR
    image_path = os.path.join(res_dir, style_name, "placement.png")
    placement_image = Image.open(image_path)
    _nums_for_black_images.append(make_color_copy(placement_image, color_for_marker))
    _nums_for_white_images.append(make_color_copy(placement_image, color_for_marker))
    for i in range(1, _MAX_MOVE_NUM_IMG + 1):
        _nums_for_black_images.append(
            _render_cropped_text(256, str(i), color_for_black)
        )
        _nums_for_white_images.append(
            _render_cropped_text(256, str(i), color_for_white)
        )


# returns a copy of the given <image> with all of its pixels
# changed to the given <color> while maintaining the original alpha channel.
def make_color_copy(image, color):
    data = np.array(image)
    new_color = np.array(color + (255,), dtype=np.uint8)
    alpha_strengths = data[..., 3:] / 255.0
    data = new_color * alpha_strengths
    new_image = Image.fromarray(data.astype(np.uint8))
    return new_image


# returns the result of rendering text and cropped it by its bounding box.
def _render_cropped_text(cell_size, text, color):
    PADDING_BOTTOM_PX = 15
    render_plane = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(render_plane)
    font = _fonts[cell_size]
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((0, 0), text, fill=color, font=font)

    if len(text) == 1:
        if ord("a") <= ord(text[0]) <= ord("z"):
            max_bbox = draw.textbbox((0, 0), "b", font=font)
        else:
            max_bbox = draw.textbbox((0, 0), "0", font=font)
        max_bbox_width = max_bbox[2] - max_bbox[0]
        bbox_width = bbox[2] - bbox[0]
        padding_x = (max_bbox_width - bbox_width) / 2
        start_x = int(bbox[0] - padding_x)
        end_x = int(start_x + bbox_width + padding_x * 2)

        max_bbox_height = max_bbox[3] - max_bbox[1]
        if get_settings().CENTER_LABELS_VERTICALLY:
            bbox_height = bbox[3] - bbox[1]
            padding_y = (max_bbox_height - bbox_height) / 2
            start_y = int(bbox[1] - padding_y)
            end_y = int(start_y + bbox_height + padding_y * 2) + PADDING_BOTTOM_PX
        else:
            start_y = bbox[3] - max_bbox_height
            end_y = bbox[3] + PADDING_BOTTOM_PX

        crop = render_plane.crop((start_x, start_y, end_x, end_y))
    else:
        crop = render_plane.crop(bbox)

    return crop


# returns an image of <cell_size> that contains the given <text>.
def create_cell_text(cell_size, text, color, scale):
    render_plane = Image.new("RGBA", (cell_size, cell_size), (0, 0, 0, 0))
    if len(text) == 0:
        return render_plane

    render_as_placement_marker = False
    if len(text) == 1 and ord("a") <= ord(text[0]) <= ord("z"):
        image = _char_images[text[0]]
    elif re.fullmatch(r"\d+", text):
        move_num = int(text)
        if move_num == 0:
            render_as_placement_marker = True
        if move_num <= _MAX_MOVE_NUM_IMG:
            if color == get_settings().NUMBER_COLOR_FOR_BLACK:
                image = _nums_for_black_images[move_num]
            else:
                image = _nums_for_white_images[move_num]
        else:
            image = _render_cropped_text(cell_size, text, color)
    else:
        image = _render_cropped_text(cell_size, text, color)

    if render_as_placement_marker:
        new_width = int(cell_size)
        new_height = int(cell_size)
    else:
        if image.size[0] > image.size[1]:
            new_width = int(cell_size * scale)
            new_height = int(image.size[1] * (cell_size / image.size[0]) * scale)
        elif image.size[1] > image.size[0]:
            new_width = int(image.size[0] * (cell_size / image.size[1]) * scale)
            new_height = int(cell_size * scale)
        else:
            new_width = int(cell_size * scale)
            new_height = int(cell_size * scale)

    image = image.resize((new_width, new_height), resample=Image.LANCZOS)

    center_x = int(cell_size / 2 - new_width / 2)
    center_y = int(cell_size / 2 - new_height / 2)
    render_plane.paste(image, (center_x, center_y))

    return render_plane
