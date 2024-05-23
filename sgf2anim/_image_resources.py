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
_STONE_IMAGES = {}
_STAR_POINT_IMAGES = {}
_BOARD_IMAGE = None
_BOARD_IMAGE_NO_LINES = None

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


def get_star_images():
    return _STAR_POINT_IMAGES


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


def _load_images():
    global _STONE_IMAGES, _STAR_POINT_IMAGES
    if len(_STONE_IMAGES) > 0:
        return

    load_font(get_settings().STYLE_NAME)

    # creates the raw star point image that will be scaled down later.
    star_point_image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(star_point_image)
    radius = 50  # determines the size of the star point.
    bbox = (256 - radius, 256 - radius, 256 + radius, 256 + radius)
    draw.ellipse(bbox, fill=get_settings().LINE_COLOR)

    # loads the image resources from file.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    load_dir = os.path.join(current_dir, "_res", get_settings().STYLE_NAME)
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
    if os.path.exists(original_img_name):
        # determines viewport size from a pre-existing accompanying image.
        image = Image.open(original_img_name)
        n_cells_wide = int((image.size[0] - 4) / 23)
        n_cells_high = int((image.size[1] - 4) / 23)
        image.close()
    else:
        n_cells_wide = min(board.get_width(), n_found_cells_wide + 1)
        n_cells_high = min(board.get_height(), n_found_cells_high + 1)

    padding_x = (n_cells_wide - n_found_cells_wide) // 2
    padding_y = (n_cells_high - n_found_cells_high) // 2
    _start_x = min_x - padding_x
    _start_y = min_y - padding_y

    # 4) ensures that the viewport stays within the board.
    _start_x = max(_start_x, 0)
    _start_x = min(_start_x, board.get_width() - n_cells_wide)
    _start_y = max(_start_y, 0)
    _start_y = min(_start_y, board.get_height() - n_cells_high)
    end_x = _start_x + n_cells_wide - 1
    end_y = _start_y + n_cells_high - 1

    # 5) the viewport will be extended to the board's edge if it's close enough.
    if _start_x <= 2 and (n_cells_wide - 1) >= max_x:
        _start_x = 0
        end_x = n_cells_wide - 1
    elif end_x >= board.get_width() - 3 and board.get_width() - n_cells_wide <= min_x:
        _start_x = board.get_width() - n_cells_wide
        end_x = _start_x + n_cells_wide - 1

    if _start_y <= 2 and (n_cells_high - 1) >= max_y:
        _start_y = 0
        end_y = n_cells_high - 1
    elif end_y >= board.get_height() - 3 and board.get_height() - n_cells_high <= min_x:
        _start_y = board.get_height() - n_cells_high
        end_y = _start_y + n_cells_high - 1

    _show_width = end_x - _start_x + 1
    _show_height = end_y - _start_y + 1

    # 6) determines the size of the image margin.
    longest_show_dim = max(_show_width, _show_height)
    longest_image_dim = max(get_settings().MAX_WIDTH, get_settings().MAX_HEIGHT)
    _scaled_margin = round(longest_image_dim / longest_show_dim * 0.0853)

    # 7) determines how large (in pixels) each cell graphic should be.
    width_no_margin = get_settings().MAX_WIDTH - _scaled_margin * 2
    height_no_margin = get_settings().MAX_HEIGHT - _scaled_margin * 2
    _cell_size = min(
        [
            width_no_margin // _show_width,
            height_no_margin // _show_height,
            get_settings().MAX_CELL_SIZE,
        ]
    )
    _cell_size = max(_cell_size, get_settings().MIN_CELL_SIZE)

    # 8) determines the sizes (in pixels) of output components.
    _board_line_width = int(get_settings().LINE_THICKNESS + _cell_size * 0.03)
    if get_settings().FORCE_STONES_CENTER and (
        (_board_line_width % 2 == 0 and cell_size % 2 == 1)
        or (_board_line_width % 2 == 1 and cell_size % 2 == 0)
    ):
        _draw_cell_size = _cell_size - 1
    else:
        _draw_cell_size = _cell_size

    # 9) creates the board images.
    _draw_board_images(board)

    return board


# returns two images of the board: one with lines and one without.
def _draw_board_images(board):
    global _BOARD_IMAGE, _BOARD_IMAGE_NO_LINES
    image_size = (
        _scaled_margin * 2 + _cell_size * _show_width,
        _scaled_margin * 2 + _cell_size * _show_height,
    )
    _BOARD_IMAGE = Image.new("RGBA", image_size, (243, 176, 109, 255))
    _BOARD_IMAGE_NO_LINES = _BOARD_IMAGE.copy()

    draw = ImageDraw.Draw(_BOARD_IMAGE)
    px_offset = _scaled_margin + _cell_size // 2
    line_width = int(get_settings().LINE_THICKNESS + _cell_size * 0.03)
    line_color = get_settings().LINE_COLOR

    # draws the vertical lines.
    min_y = -10 if _start_y > 0 else px_offset
    if _start_y + _show_height < board.get_height():
        max_y = image_size[1] + 10
    else:
        max_y = _cell_size * (_show_height - 1) + px_offset
    for x in range(_show_width):
        pixel_x = x * _cell_size + px_offset
        start = (pixel_x, min_y)
        end = (pixel_x, max_y)
        draw.line([start, end], fill=line_color, width=line_width)

    # draws the horizontal lines.
    min_x = -10 if _start_x > 0 else px_offset
    if _start_x + _show_width < board.get_width():
        max_x = image_size[0] + 10
    else:
        max_x = _cell_size * (_show_width - 1) + px_offset
    for y in range(_show_height):
        pixel_y = y * _cell_size + px_offset
        start = (min_x, pixel_y)
        end = (max_x, pixel_y)
        draw.line([start, end], fill=line_color, width=line_width)

    # determines the positions of star points on the board.
    star_points = set()
    if board.get_width() > 10 and board.get_height() > 10:
        star_points.update(
            [
                (3, 3),
                (3, board.get_height() - 4),
                (board.get_width() - 4, 3),
                (board.get_width() - 4, board.get_height() - 4),
            ]
        )

    if board.get_width() % 2 == 1 and board.get_height() % 2 == 1:
        star_points.add((board.get_width() // 2, board.get_height() // 2))

    if len(star_points) == 0:
        return

    show_cols = set()
    show_rows = set()
    for point in star_points:
        if point[0] - _start_x < _show_width:
            show_cols.add(point[0] - _start_x)
        if point[1] - _start_y < _show_height:
            show_rows.add(point[1] - _start_y)

    # draws the star point images.
    star_point_graphic = _STAR_POINT_IMAGES[_draw_cell_size]
    comp = Image.new("RGBA", image_size, (0, 0, 0, 0))
    for show_x in show_rows:
        for show_y in show_cols:
            draw_x = int(_scaled_margin + _cell_size * (show_x + 0.5) + line_width / 2)
            draw_y = int(_scaled_margin + _cell_size * (show_y + 0.5) + line_width / 2)
            comp.paste(star_point_graphic, (draw_x, draw_y))
    _BOARD_IMAGE.alpha_composite(comp)
