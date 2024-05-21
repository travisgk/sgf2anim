import os
from PIL import Image, ImageDraw
from .weiqi_board import WeiqiBoard
from ._settings import get_settings
from ._textbox import load_font, make_color_copy


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
_scaled_margin = None
_annotations = None


def get_stone_images():
    return _STONE_IMAGES


def get_star_images():
    return _STAR_POINT_IMAGES


def get_scaled_margin():
    return _scaled_margin


def get_annotation(show_x, show_y):
    return _annotations[show_x][show_y]


def set_annotation(show_x, show_y, function_name):
    global _annotations
    _annotations[show_x][show_y] = function_name


# loads the image resources if they have not yet been loaded.
def _load_resources():
    global _STONE_IMAGES, _STAR_POINT_IMAGES
    if len(_STONE_IMAGES) > 0:
        return

    load_font(get_settings().STYLE_NAME)

    star_point_image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(star_point_image)
    center = (256, 256)
    radius = 50  # determines size of the star point
    bbox = [
        (center[0] - radius, center[1] - radius),
        (center[0] + radius, center[1] + radius),
    ]
    star_draw.ellipse(bbox, fill=get_settings().LINE_COLOR)

    current_directory = os.path.dirname(os.path.abspath(__file__))
    res_dir = os.path.join(current_directory, "_res")

    loaded_images = {}
    for key, value in _STONE_IMAGE_PATHS.items():
        image_path = os.path.join(res_dir, get_settings().STYLE_NAME, value)
        loaded_images[key] = Image.open(image_path)
        if key not in [
            "B",
            "W",
        ]:
            loaded_images[key] = make_color_copy(
                loaded_images[key], get_settings().MARKER_COLOR
            )

    for cell_size in range(
        get_settings().MIN_CELL_SIZE, get_settings().MAX_CELL_SIZE + 1
    ):
        _STONE_IMAGES[cell_size] = {}
        for key, value in _STONE_IMAGE_PATHS.items():
            image_path = os.path.join(res_dir, value)
            _STONE_IMAGES[cell_size][key] = loaded_images[key].resize(
                (cell_size, cell_size), resample=Image.LANCZOS
            )

        _STAR_POINT_IMAGES[cell_size] = star_point_image.resize(
            (cell_size, cell_size), resample=Image.LANCZOS
        )


# returns the weiqi game <Board> object,
# the cell size, the show size,
# and the start point on the board (e.g.19x19) where the display begins.
def setup_board(sgf_path, nodes, commands_lists):
    global _scaled_margin, _annotations
    _load_resources()

    # 1) determines the coordinate ranges that every play finds itself in.
    min_x = 99
    min_y = 99
    max_x = 0
    max_y = 0
    for command_list in commands_lists:
        for command in command_list:
            function_name, parameters = command
            if function_name == "LB":
                points, _ = decode_labels(parameters)
            else:
                points = decode_letter_coords(parameters)
            for point in points:
                min_x = min(min_x, point[0])
                min_y = min(min_y, point[1])
                max_x = max(max_x, point[0])
                max_y = max(max_y, point[1])

    # 2) determines the size of the board from the single "SZ" command.
    board = None
    setup_commands = commands_lists[0]
    for command in setup_commands:
        function_name, parameters = command
        if function_name == "SZ":
            parameters = parameters[0].split(":")
            if len(parameters) == 1:
                dim = int(parameters[0])
                width = dim
                height = dim
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
        image = Image.open(original_img_name)
        n_cells_wide = int((image.size[0] - 4) / 23)
        n_cells_high = int((image.size[1] - 4) / 23)
        image.close()
    else:
        n_cells_wide = min(board.get_width(), n_found_cells_wide + 1)
        n_cells_high = min(board.get_height(), n_found_cells_high + 1)

    padding_x = (n_cells_wide - n_found_cells_wide) // 2
    padding_y = (n_cells_high - n_found_cells_high) // 2

    start_x = min_x - padding_x
    start_y = min_y - padding_y

    # 4) ensures that the coordinates stay within the board.
    start_x = max(start_x, 0)
    start_x = min(start_x, board.get_width() - n_cells_wide)
    start_y = max(start_y, 0)
    start_y = min(start_y, board.get_height() - n_cells_high)
    end_x = start_x + n_cells_wide - 1
    end_y = start_y + n_cells_high - 1

    # 5) the viewport will extend to the board's edge if its close enough.
    if start_x <= 2 and (n_cells_wide - 1) >= max_x:
        start_x = 0
        end_x = n_cells_wide - 1
    elif end_x >= board.get_width() - 3 and (board.get_width() - n_cells_wide) <= min_x:
        start_x = board.get_width() - n_cells_wide
        end_x = start_x + n_cells_wide - 1

    if start_y <= 2 and (n_cells_high - 1) >= max_y:
        start_y = 0
        end_y = n_cells_high - 1
    elif (
        end_y >= board.get_height() - 3 and (board.get_height() - n_cells_high) <= min_x
    ):
        start_y = board.get_height() - n_cells_high
        end_y = start_y + n_cells_high - 1

    # 6) determines how large (in pixels) each cell graphic should be.
    show_width = end_x - start_x + 1
    show_height = end_y - start_y + 1

    _annotations = [[None for _ in range(show_height)] for _ in range(show_width)]

    longest_show_dim = max(show_width, show_height)
    longest_image_dim = max(get_settings().MAX_WIDTH, get_settings().MAX_HEIGHT)
    _scaled_margin = round(longest_image_dim / longest_show_dim * 0.0853)

    width_no_margin = get_settings().MAX_WIDTH - _scaled_margin * 2
    height_no_margin = get_settings().MAX_HEIGHT - _scaled_margin * 2
    cell_size = min(
        [
            width_no_margin // show_width,
            height_no_margin // show_height,
            get_settings().MAX_CELL_SIZE,
        ]
    )
    cell_size = max(cell_size, get_settings().MIN_CELL_SIZE)
    start_point = (
        start_x,
        start_y,
    )

    return (
        board,
        cell_size,
        (
            show_width,
            show_height,
        ),
        (
            start_x,
            start_y,
        ),
    )


def decode_labels(parameters):
    points = []
    strings = []
    for parameter in parameters:
        results = decode_letter_coords(
            [
                parameter[:2],
            ]
        )
        if len(results) == 0:
            continue
        points.append(results[0])
        strings.append(parameter[3:])
    return points, strings


def decode_letter_coords(parameters):
    points = []
    for parameter in parameters:
        if len(parameter) != 2:
            continue
        x = _letter_to_number(parameter[0])
        y = _letter_to_number(parameter[1])
        if x is not None and y is not None:
            points.append(
                (
                    x,
                    y,
                )
            )
    return points


def _letter_to_number(letter):
    if "a" <= letter <= "z":
        return ord(letter) - ord("a")
    if "A" <= letter <= "Z":
        return ord(letter) - ord("A")
    return None
