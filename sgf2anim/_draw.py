from PIL import Image, ImageDraw
from .weiqi_board import BLACK_NUM, WHITE_NUM
from ._settings import get_settings
from ._image_resources import (
    get_stone_images,
    get_star_images,
    get_board_image,
    get_board_image_no_lines,
    get_board_start_point,
    get_show_width,
    get_show_height,
    get_cell_size,
    get_scaled_margin,
    get_draw_cell_size,
    get_board_line_width,
)


_annotations = None


def find_board_points_with_annotation(function_name):
    board_points = []
    for x in range(get_show_width()):
        for y in range(get_show_height()):
            if _annotations[x][y] == function_name:
                board_points.append(
                    (x + get_board_start_point()[0], y + get_board_start_point()[1])
                )
    return board_points


# clears all the representative graphic cells
# that correspond to the given <board_points>.
def mass_clear(image, board_points):
    global _annotations
    _init_annotations()
    for point in board_points:
        show_x = point[0] - get_board_start_point()[0]
        show_y = point[1] - get_board_start_point()[1]
        _annotations[show_x][show_y] = None
        _clear_cell(image, show_x, show_y)


def mass_paste_stone(stones_image, paste_graphic, board_points):
    global _annotations
    _init_annotations()
    comp = Image.new("RGBA", stones_image.size, (0, 0, 0, 0))
    for point in board_points:
        show_x = point[0] - get_board_start_point()[0]
        show_y = point[1] - get_board_start_point()[1]
        _annotations[show_x][show_y] = None
        bbox = _clear_cell(stones_image, show_x, show_y)
        draw_x, draw_y, _, _ = bbox
        diff = get_cell_size() - get_draw_cell_size()
        comp.paste(paste_graphic, (draw_x + diff, draw_y + diff))
    stones_image.alpha_composite(comp)


def mass_paste_annotation(
    function_name, annotations_image, paste_graphic, board_points, board
):
    global _annotations
    _init_annotations()
    has_new_annotations = False

    comp = Image.new("RGBA", annotations_image.size, (0, 0, 0, 0))
    for point in board_points:
        show_x = point[0] - get_board_start_point()[0]
        show_y = point[1] - get_board_start_point()[1]

        if _annotations[show_x][show_y] == function_name:
            continue

        has_new_annotations = True
        _annotations[show_x][show_y] = function_name
        bbox = _clear_cell(annotations_image, show_x, show_y)
        draw_x, draw_y, _, _ = bbox
        diff = get_cell_size() - get_draw_cell_size()

        # draws a pre-existing stone beneath a new annotation.
        underneath_stone = board.get_player_num(point)
        stone_graphic = None
        if underneath_stone == BLACK_NUM:
            stone_graphic = get_stone_images()[get_draw_cell_size()]["B"]
        elif underneath_stone == WHITE_NUM:
            stone_graphic = get_stone_images()[get_draw_cell_size()]["W"]

        if stone_graphic is not None:  # UNCERTAIN
            annotations_image.paste(stone_graphic, (draw_x, draw_y))

        elif function_name == "LB":
            bg_cell = get_board_image_no_lines().crop(bbox)
            label_bg = _create_label_background(bg_cell)
            label_comp = Image.new("RGBA", annotations_image.size, (0, 0, 0, 0))
            annotations_image.alpha_composite(label_comp)
        comp.paste(paste_graphic, (draw_x + diff, draw_y + diff))

    if has_new_annotations:
        annotations_image.alpha_composite(comp)


def mass_draw_lines(image, lines):
    draw = ImageDraw.Draw(image)
    line_color = get_settings().ANNOTATE_LINE_COLOR
    line_width = int(get_settings().ANNOTATE_LINE_THICKNESS + cell_size * 0.03)

    draw_lines = []
    for begin, end in lines:
        # transforms board points into pixel coordinates for drawing.
        begin_draw_point = (
            int(
                get_scaled_margin()
                + (begin[0] - get_board_start_point()[0] + 0.5) * get_cell_size()
            ),
            int(
                get_scaled_margin()
                + (begin[1] - get_board_start_point()[1] + 0.5) * get_cell_size()
            ),
        )
        end_draw_point = (
            int(
                get_scaled_margin()
                + (end[0] - get_board_start_point()[0] + 0.5) * get_cell_size()
            ),
            int(
                get_scaled_margin()
                + (end[1] - get_board_start_point()[1] + 0.5) * get_cell_size()
            ),
        )

        # draws circles on the ends of the lines.
        for point in [begin_draw_point, end_draw_point]:
            bbox = (
                int(point[0] - line_width // 2) + 1,
                int(point[1] - line_width // 2) + 1,
                int(point[0] + line_width // 2) - 1,
                int(point[1] + line_width // 2) - 1,
            )
            draw.ellipse(bbox, fill=line_color)

        # orthogonal lines are shortened on both sides by one pixel
        # in order to allow smooth connections between other lines.
        if begin_draw_point[1] == end_draw_point[1]:
            # horizontal line.
            offset = -1 if begin_draw_point[0] < end_draw_point[0] else 1
            begin_draw_point = (begin_draw_point[0] - offset, begin_draw_point[1])
            end_draw_point = (end_draw_point[0] + offset, end_draw_point[1])

        elif begin_draw_point[0] == end_draw_point[0]:
            # vertical line.
            offset = -1 if begin_draw_point[1] < end_draw_point[1] else 1
            begin_draw_point = (begin_draw_point[0], begin_draw_point[1] - offset)
            end_draw_point = (end_draw_point[0], end_draw_point[1] + offset)

        draw_lines.append((begin_draw_point, end_draw_point))

    # all the lines are finally drawn.
    for draw_line in draw_lines:
        draw.line(draw_line, fill=line_color, width=line_width)


# clears the given <image> at the cell located at <show_x>, <show_y>,
# then returns the bounding box of the selected cell.
def _clear_cell(image, show_x, show_y):
    crop_box = _get_cell_crop(show_x, show_y)
    graphic = get_board_image().crop(crop_box)
    image.paste(graphic, (crop_box[0], crop_box[1]))
    return crop_box


def _get_cell_crop(show_x, show_y):
    return (
        get_scaled_margin() + show_x * get_cell_size(),
        get_scaled_margin() + show_y * get_cell_size(),
        get_scaled_margin() + (show_x + 1) * get_cell_size(),
        get_scaled_margin() + (show_y + 1) * get_cell_size(),
    )


def _init_annotations():
    global _annotations
    if _annotations is not None:
        return
    _annotations = [
        [None for _ in range(get_show_height())] for _ in range(get_show_width())
    ]


# creates a background for a label with the <board_cell_image> (no lines).
# this helps make a label easier to read, unobscured by the intersection.
def _create_label_background(board_cell_image):
    dim = get_cell_size() * get_settings().LABEL_TEXT_SCALE * 1.15
    start_coord = int(get_cell_size() / 2 - dim / 2)
    dim = int(dim)
    crop = board_cell_image.crop(
        (start_coord, start_coord, start_coord + dim, start_coord + dim)
    )
    image = Image.new("RGBA", (get_cell_size(), get_cell_size()), (0, 0, 0, 0))
    image.paste(crop, (start_coord, start_coord))
    return image
