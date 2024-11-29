import os
from PIL import Image, ImageDraw
from .weiqi_board import WeiqiBoard
from ._decode_coords import decode_lines, decode_labels, decode_letter_coords
from ._image_text import load_font, make_color_copy
from ._settings import get_settings


_STONE_IMAGE_PATHS = {
    "B": "black.png",
    "W": "white.png",
    "CR": "circle.png",
    "DD": "dim.png",
    "MA": "x.png",
    "SL": "select.png",
    "SQ": "square.png",
    "TR": "triangle.png",
}
_last_loaded_style = None
_STONE_IMAGES = {}
_CORNER_CIRCLE_IMAGES = {}
_STAR_POINT_IMAGES = {}
_BOARD_TEXTURE = None
_BOARD_IMAGE = None
_BOARD_IMAGE_NO_LINES = None

_MAX_BOARD_LINE_WIDTH = None
_start_x = None
_start_y = None
_show_width = None
_show_height = None
_scaled_margin = None
_board_line_width = None
_cell_size = None
_draw_cell_size = None


def get_stone_images():
    return _STONE_IMAGES


def get_board_image():
    return _BOARD_IMAGE


def get_board_image_no_lines():
    return _BOARD_IMAGE_NO_LINES


# returns the board point where the viewport begins.
def get_board_start_point():
    return (_start_x, _start_y)


def get_show_width():
    return _show_width


def get_show_height():
    return _show_height


def get_cell_size():
    return _cell_size


def get_scaled_margin():
    return _scaled_margin


def get_board_line_width():
    return _board_line_width


def get_draw_cell_size():
    return _draw_cell_size


# loads and creates image resources.
def _load_images():
    global _last_loaded_style, _STONE_IMAGES, _CORNER_CIRCLE_IMAGES, _STAR_POINT_IMAGES, _BOARD_TEXTURE, _MAX_BOARD_LINE_WIDTH
    if len(_STONE_IMAGES) > 0 and _last_loaded_style == get_settings().STYLE_NAME:
        return

    _last_loaded_style = get_settings().STYLE_NAME
    print(
        f'\nloading the "{get_settings().STYLE_NAME}" style resources... ',
        end="",
        flush=True,
    )
    thickness = get_settings().LINE_THICKNESS
    _MAX_BOARD_LINE_WIDTH = max(
        1, int(thickness * get_settings().MAX_CELL_SIZE * (1 / 23))
    )

    load_font(get_settings().STYLE_NAME)

    # creates a raw corner circle image that will be scaled down later.
    corner_circle_image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(corner_circle_image)
    draw.ellipse((0, 0, 256, 256), fill=get_settings().LINE_COLOR)

    # creates the raw star point image that will be scaled down later.
    star_point_image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(star_point_image)
    radius = 50  # determines the size of the star point.
    bbox = (256 - radius, 256 - radius, 256 + radius, 256 + radius)
    draw.ellipse(bbox, fill=get_settings().LINE_COLOR)

    # loads the image resources from file.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    load_dir = os.path.join(current_dir, "_res", get_settings().STYLE_NAME)
    board_path = os.path.join(load_dir, "board.png")
    if not os.path.exists(board_path):
        board_path = os.path.join(load_dir, "board.jpg")
    _BOARD_TEXTURE = Image.open(board_path)

    loaded_images = {}
    for key, value in _STONE_IMAGE_PATHS.items():
        path = os.path.join(load_dir, value)
        loaded_images[key] = Image.open(path)
        if key not in ["B", "W", "DD"]:
            # most annotative images are colored to match specified styling.
            loaded_images[key] = make_color_copy(
                loaded_images[key], get_settings().MARKER_COLOR
            )

    # creates scaled copies of the loaded resources and stores
    # them in memory in order to save on processing time.
    for cell_size in range(
        get_settings().MIN_CELL_SIZE, get_settings().MAX_CELL_SIZE + 1
    ):
        _STONE_IMAGES[cell_size] = {}
        for key, value in _STONE_IMAGE_PATHS.items():
            _STONE_IMAGES[cell_size][key] = loaded_images[key].resize(
                (cell_size, cell_size), resample=Image.LANCZOS
            )

        _STAR_POINT_IMAGES[cell_size] = star_point_image.resize(
            (cell_size, cell_size), resample=Image.LANCZOS
        )

    for line_width in range(3, _MAX_BOARD_LINE_WIDTH + 5):
        _CORNER_CIRCLE_IMAGES[line_width] = corner_circle_image.resize(
            (line_width, line_width), resample=Image.LANCZOS
        )

    print("done.")


# returns a Weiqi board object after determining viewport and cell size.
def setup_board(sgf_path, commands_lists):
    global _start_x, _start_y, _show_width, _show_height, _cell_size, _scaled_margin, _board_line_width, _draw_cell_size
    _load_images()

    # 1) determines the coord ranges that every played point finds itself in.
    min_x = 99
    min_y = 99
    max_x = 0
    max_y = 0
    for command_list in commands_lists:
        for command in command_list:
            function_name, parameters = command
            if function_name == "LN":
                lines = decode_lines(parameters)
                points = []
                for line in lines:
                    points.extend([line[0], line[1]])
            elif function_name == "LB":
                points, _ = decode_labels(parameters)
            else:
                points = decode_letter_coords(parameters)
            for point in points:
                min_x = min(min_x, point[0])
                min_y = min(min_y, point[1])
                max_x = max(max_x, point[0])
                max_y = max(max_y, point[1])

    # 2) determines the size of the board from a single "SZ" command.
    board = None
    for command in commands_lists[0]:
        function_name, parameters = command
        if function_name == "SZ":
            parameters = parameters[0].split(":")
            if len(parameters) == 1:
                width = int(parameters[0])
                height = int(parameters[0])
            else:
                width = int(parameters[0])
                height = int(parameters[1])
            board = WeiqiBoard(width, height, n_players=2)
            break

    # 3) determines the viewport's beginning and ending points.
    n_found_cells_wide = max_x - min_x + 1
    n_found_cells_high = max_y - min_y + 1

    original_img_name = sgf_path[:-4] + ".png"
    if get_settings().DOING_SENSEIS_FORMAT and os.path.exists(original_img_name):
        # determines viewport size from a pre-existing accompanying image.
        image = Image.open(original_img_name)
        n_cells_wide = int((image.size[0] - 4) / 23)
        n_cells_high = int((image.size[1] - 4) / 23)
        image.close()
        padding_x = (n_cells_wide - n_found_cells_wide) // 2
        padding_y = (n_cells_high - n_found_cells_high) // 2

        _start_x = _clip_value(min_x - padding_x, 0, board.get_width() - n_cells_wide)
        _start_y = _clip_value(min_y - padding_y, 0, board.get_height() - n_cells_high)
        end_x = _start_x + n_cells_wide - 1
        end_y = _start_y + n_cells_high - 1

        # viewport will be pushed to the edge if close enough.
        if _start_x <= 2 and (n_cells_wide - 1) >= max_x:
            _start_x = 0
            end_x = n_cells_wide - 1
        elif (
            end_x >= board.get_width() - 3 and board.get_width() - n_cells_wide <= min_x
        ):
            _start_x = board.get_width() - n_cells_wide
            end_x = _start_x + n_cells_wide - 1

        if _start_y <= 2 and (n_cells_high - 1) >= max_y:
            _start_y = 0
            end_y = n_cells_high - 1
        elif (
            end_y >= board.get_height() - 3
            and board.get_height() - n_cells_high <= min_x
        ):
            _start_y = board.get_height() - n_cells_high
            end_y = _start_y + n_cells_high - 1

    else:
        # viewport will go around all activated cells with added padding.
        padding_x = get_settings().DISPLAY_PADDING
        padding_y = get_settings().DISPLAY_PADDING

        _start_x = _clip_value(min_x - padding_x, 0, board.get_width() - 1)
        _start_y = _clip_value(min_y - padding_y, 0, board.get_height() - 1)
        end_x = _clip_value(max_x + padding_x, 0, board.get_width() - 1)
        end_y = _clip_value(max_y + padding_y, 0, board.get_height() - 1)

        n_cells_wide = min((end_x - _start_x) + 1, board.get_width())
        n_cells_high = min((end_y - _start_y) + 1, board.get_height())

        # viewport will be extended to the edge if close enough.
        if _start_x <= 2 and n_cells_wide >= max_x:
            _start_x = 0
        if end_x >= board.get_width() - 3:
            end_x = board.get_width() - 1

        if _start_y <= 2 and n_cells_high >= max_y:
            _start_y = 0
        if end_y >= board.get_height() - 3:
            end_y = board.get_height() - 1

    _show_width = end_x - _start_x + 1
    _show_height = end_y - _start_y + 1

    # 6) determines the size of the image margin.
    longest_show_dim = max(_show_width, _show_height)
    longest_image_dim = max(get_settings().MAX_WIDTH, get_settings().MAX_HEIGHT)
    _scaled_margin = round(
        longest_image_dim / longest_show_dim * (get_settings().IMAGE_MARGIN / 23)
    )

    # 7) determines how large (in pixels) each cell graphic should be.
    width_no_margin = get_settings().MAX_WIDTH - _scaled_margin * 2
    height_no_margin = get_settings().MAX_HEIGHT - _scaled_margin * 2
    _cell_size = _clip_value(
        min(width_no_margin // _show_width, height_no_margin // _show_height),
        get_settings().MIN_CELL_SIZE,
        get_settings().MAX_CELL_SIZE,
    )

    # 8) determines the sizes (in pixels) of output components.
    thickness = get_settings().LINE_THICKNESS
    _board_line_width = max(1, int(thickness * _cell_size * (1 / 23)))
    if get_settings().FORCE_STONES_CENTER:
        if _board_line_width % 2 == 1:
            _draw_cell_size = _cell_size - (1 - (_cell_size % 2))
        else:
            _draw_cell_size = _cell_size - (_cell_size % 2)
    else:
        _draw_cell_size = _cell_size

    # 9) creates the board images.
    _draw_board_images(board)

    return board


def _clip_value(value, min_value, max_value):
    if value > max_value:
        return max_value
    if value < min_value:
        return min_value
    return value


# returns two images of the board: one with lines and one without.
def _draw_board_images(board):
    global _BOARD_IMAGE, _BOARD_IMAGE_NO_LINES
    image_size = (
        _scaled_margin * 2 + _cell_size * _show_width,
        _scaled_margin * 2 + _cell_size * _show_height,
    )
    _BOARD_IMAGE = Image.new("RGBA", image_size, (243, 176, 109, 255))
    smallest_dim = min(board.get_width(), board.get_height())
    dim = _scaled_margin * 2 + _cell_size * smallest_dim
    board_texture = _BOARD_TEXTURE.resize((dim, dim), Image.LANCZOS)
    texture_begin = (-1 * _start_x * _cell_size, -1 * _start_y * _cell_size)
    _BOARD_IMAGE.paste(board_texture, texture_begin)
    _BOARD_IMAGE_NO_LINES = _BOARD_IMAGE.copy()

    draw = ImageDraw.Draw(_BOARD_IMAGE)
    px_offset = _scaled_margin + _cell_size // 2
    line_color = get_settings().LINE_COLOR

    # 1) draws the vertical lines.
    min_y = -10 if _start_y > 0 else px_offset
    if _start_y + _show_height < board.get_height():
        max_y = image_size[1] + 10
    else:
        max_y = _cell_size * (_show_height - 1) + px_offset
    for x in range(_show_width):
        pixel_x = x * _cell_size + px_offset
        start = (pixel_x, min_y)
        end = (pixel_x, max_y)
        draw.line([start, end], fill=line_color, width=_board_line_width)

    # 2) draws the horizontal lines.
    min_x = -10 if _start_x > 0 else px_offset
    if _start_x + _show_width < board.get_width():
        max_x = image_size[0] + 10
    else:
        max_x = _cell_size * (_show_width - 1) + px_offset
    for y in range(_show_height):
        pixel_y = y * _cell_size + px_offset
        start = (min_x, pixel_y)
        end = (max_x, pixel_y)
        draw.line([start, end], fill=line_color, width=_board_line_width)

    # 3) draws circles to make corner intersections have a smooth transition.
    if _board_line_width >= 3:
        inc = 1
        circle = _CORNER_CIRCLE_IMAGES[_board_line_width + inc]
        corner_comp = Image.new("RGBA", image_size, (0, 0, 0, 0))
        off = _board_line_width // 2 - (1 - (_board_line_width % 2))

        if min_x >= 0:
            if min_y >= 0:
                corner_comp.paste(circle, (min_x - off, min_y - off))
            if max_y < image_size[1]:
                corner_comp.paste(circle, (min_x - off, max_y - off - inc))

        if max_x < image_size[0]:
            if min_y >= 0:
                corner_comp.paste(circle, (max_x - off - inc, min_y - off))
            if max_y < image_size[1]:
                corner_comp.paste(circle, (max_x - off - inc, max_y - off - inc))
        _BOARD_IMAGE.alpha_composite(corner_comp)

    # 4) determines the positions of star points on the board.
    star_points = set()
    w, h = board.get_width(), board.get_height()
    if w > 10 and h > 10:
        star_points.update([(3, 3), (3, h - 4), (w - 4, 3), (w - 4, h - 4)])

    if board.get_width() > 13 and board.get_width() % 2 == 1:
        star_points.update([(w // 2, 3), (w // 2, h - 4)])

    if board.get_height() > 13 and board.get_height() % 2 == 1:
        star_points.update([(3, h // 2), (w - 4, h // 2)])

    if board.get_width() % 2 == 1 and board.get_height() % 2 == 1:
        star_points.add((w // 2, h // 2))

    if len(star_points) == 0:
        return

    # 5) draws the star points onto the board image.
    if _board_line_width % 2 == 1:
        star_point_size = _cell_size + (1 - (_cell_size % 2))
        off = 0
    else:
        star_point_size = _cell_size + (_cell_size % 2)
        off = 1 - _cell_size % 2

    star_point_graphic = _STAR_POINT_IMAGES[star_point_size]
    comp = Image.new("RGBA", image_size, (0, 0, 0, 0))
    for point in star_points:
        show_x = point[0] - _start_x
        show_y = point[1] - _start_y
        draw_x = _scaled_margin + show_x * _cell_size + off
        draw_y = _scaled_margin + show_y * _cell_size + off
        comp.paste(star_point_graphic, (draw_x, draw_y))

    _BOARD_IMAGE.alpha_composite(comp)
