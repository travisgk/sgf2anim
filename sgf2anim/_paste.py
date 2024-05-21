from PIL import Image, ImageDraw
from .weiqi_board import BLACK_NUM, WHITE_NUM
from ._draw_board_image import get_draw_cell_size
from ._settings import get_settings
from ._graphics_setup import (
    get_stone_images,
    get_scaled_margin,
    get_annotation,
    set_annotation,
)


# clears the cells in the given <image_of_changes> with the given clear image.
def mass_clear(image_of_changes, below_image, cell_size, points, start_point):
    for point in points:
        show_x = point[0] - start_point[0]
        show_y = point[1] - start_point[1]
        set_annotation(show_x, show_y, None)
        _clear_cell(image_of_changes, below_image, cell_size, show_x, show_y)


def mass_paste_stone(
    stones_image, board_image, paste_image, cell_size, points, start_point
):
    comp = Image.new(
        "RGBA",
        stones_image.size,
        (
            0,
            0,
            0,
            0,
        ),
    )
    for point in points:
        show_x = point[0] - start_point[0]
        show_y = point[1] - start_point[1]
        set_annotation(show_x, show_y, None)
        bbox = _clear_cell(stones_image, board_image, cell_size, show_x, show_y)
        draw_x, draw_y, _, _ = bbox
        diff = cell_size - get_draw_cell_size()
        comp.paste(paste_image, ((draw_x + diff), (draw_y + diff)))
    stones_image.alpha_composite(comp)


def mass_paste_annotation(
    function_name,
    annotations_image,
    board_image,
    board_image_no_lines,
    stones_image,
    paste_image,
    cell_size,
    points,
    start_point,
    board,
):
    comp = Image.new(
        "RGBA",
        annotations_image.size,
        (
            0,
            0,
            0,
            0,
        ),
    )

    new_annotations = False
    for point in points:
        show_x = point[0] - start_point[0]
        show_y = point[1] - start_point[1]

        if get_annotation(show_x, show_y) == function_name:
            continue
        set_annotation(show_x, show_y, function_name)
        new_annotations = True
        bbox = _clear_cell(annotations_image, board_image, cell_size, show_x, show_y)

        draw_x, draw_y, _, _ = bbox
        diff = cell_size - get_draw_cell_size()

        underneath_stone = board.get_player_num(point)
        stone_cell = None
        if underneath_stone == BLACK_NUM:
            stone_cell = get_stone_images()[get_draw_cell_size()]["B"]
        elif underneath_stone == WHITE_NUM:
            stone_cell = get_stone_images()[get_draw_cell_size()]["W"]

        if stone_cell is not None:
            stone_comp = Image.new(
                "RGBA",
                annotations_image.size,
                (
                    0,
                    0,
                    0,
                    0,
                ),
            )
            stone_comp.paste(stone_cell, (draw_x, draw_y))
            annotations_image.alpha_composite(stone_comp)

        # adds background
        elif function_name == "LB":
            label_bg = _create_label_background(
                board_image_no_lines.crop(bbox), cell_size
            )
            label_comp = Image.new(
                "RGBA",
                annotations_image.size,
                (
                    0,
                    0,
                    0,
                    0,
                ),
            )
            label_comp.paste(label_bg, (draw_x, draw_y))
            annotations_image.alpha_composite(label_comp)

        comp.paste(paste_image, ((draw_x + diff), (draw_y + diff)))
    if new_annotations:
        annotations_image.alpha_composite(comp)


# returns the bounding box that's used
# to clear a cell of <image_of_changes>
# by pasting the same section of the <below_image> on top.
def _clear_cell(image_of_changes, below_image, cell_size, show_x, show_y):
    crop_box = _get_cell_crop(cell_size, show_x, show_y)
    paste_image = below_image.crop(crop_box)
    image_of_changes.paste(paste_image, (crop_box[0], crop_box[1]))
    return crop_box


def _get_cell_crop(cell_size, show_x, show_y):
    return (
        get_scaled_margin() + show_x * cell_size,
        get_scaled_margin() + show_y * cell_size,
        get_scaled_margin() + (show_x + 1) * cell_size,
        get_scaled_margin() + (show_y + 1) * cell_size,
    )


# creates a background for a label with the <board_cell> that has no lines.
# this helps make a label easier to read, unobscured by the intersection.
def _create_label_background(board_cell, cell_size):
    dim = cell_size * (get_settings().LABEL_TEXT_SCALE * 1.15)
    start_coord = int(cell_size / 2 - dim / 2)
    dim = int(dim)
    crop = board_cell.crop(
        (start_coord, start_coord, start_coord + dim, start_coord + dim)
    )

    bg = Image.new("RGBA", (cell_size, cell_size), (0, 0, 0, 0))
    bg.paste(crop, (start_coord, start_coord))
    return bg
