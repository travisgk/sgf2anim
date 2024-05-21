from PIL import Image, ImageDraw
from ._graphics_setup import get_star_images, get_scaled_margin
from ._settings import get_settings

_draw_cell_size = None


def get_draw_cell_size():
    return _draw_cell_size


# returns two full images of the section of the board that's being displayed.
# the first image includes board lines, while the second one does not.
def draw_board_image(board, cell_size, show_size, start_pos):
    global _annotations, _draw_cell_size
    _annotations = [[None for _ in range(show_size[1])] for _ in range(show_size[0])]

    static_board_image = Image.new(
        "RGBA",
        (
            get_scaled_margin() * 2 + cell_size * show_size[0],
            get_scaled_margin() * 2 + cell_size * show_size[1],
        ),
        (
            243,
            176,
            109,
            255,
        ),
    )
    static_board_no_lines = static_board_image.copy()
    draw = ImageDraw.Draw(static_board_image)

    px_offset = get_scaled_margin() + cell_size // 2
    line_width = get_settings().LINE_THICKNESS + int(cell_size * 0.03)

    # 1) draws the vertical lines.
    if start_pos[1] > 0:
        min_y = -10
    else:
        min_y = px_offset

    if start_pos[1] + show_size[1] < board.get_height():
        max_y = static_board_image.size[1] + 10
    else:
        max_y = cell_size * (show_size[1] - 1) + px_offset

    line_color = get_settings().LINE_COLOR
    for x in range(show_size[0]):
        pixel_x = cell_size * x + px_offset
        start_point = (pixel_x, min_y)
        end_point = (pixel_x, max_y)
        draw.line([start_point, end_point], fill=line_color, width=line_width)

    # 2) draws the horizontal lines.
    if start_pos[0] > 0:
        min_x = -10
    else:
        min_x = px_offset

    if start_pos[0] + show_size[0] < board.get_width():
        max_x = static_board_image.size[0] + 10
    else:
        max_x = cell_size * (show_size[0] - 1) + px_offset

    for y in range(show_size[1]):
        pixel_y = cell_size * y + px_offset
        start_point = (min_x, pixel_y)
        end_point = (max_x, pixel_y)
        draw.line([start_point, end_point], fill=line_color, width=line_width)

    # 3) determines star point positions.
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
        star_points.add(
            (
                board.get_width() // 2,
                board.get_height() // 2,
            )
        )

    # 4) determines the cell size used in drawing so that
    #    all cells align in the center with the board's lines (if desired).
    adjusted_size = cell_size
    if (line_width % 2 == 0 and cell_size % 2 == 1) or (
        line_width % 2 == 1 and cell_size % 2 == 0
    ):
        adjusted_size -= 1
    centered = get_settings().FORCE_STONES_CENTER
    _draw_cell_size = adjusted_size if centered else cell_size

    if len(star_points) == 0:
        return static_board_image, static_board_no_lines

    # 5) draws star point images.
    star_point_image = get_star_images()[adjusted_size]
    comp = Image.new(
        "RGBA",
        static_board_image.size,
        (
            0,
            0,
            0,
            0,
        ),
    )
    cols = set([point[0] for point in star_points])
    rows = set([point[1] for point in star_points])
    for x in range(show_size[0]):
        col = start_pos[0] + x
        if col not in cols:
            continue
        for y in range(show_size[1]):
            row = start_pos[1] + y
            if row in rows:
                draw_x = int(
                    get_scaled_margin()
                    + cell_size * (x + 0.5)
                    - (adjusted_size / 2)
                    + line_width / 2
                )
                draw_y = int(
                    get_scaled_margin()
                    + cell_size * (y + 0.5)
                    - (adjusted_size / 2)
                    + line_width / 2
                )
                comp.paste(star_point_image, (draw_x, draw_y))

    static_board_image.alpha_composite(comp)
    return static_board_image, static_board_no_lines
