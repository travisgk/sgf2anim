import os
from PIL import Image
from .weiqi_board import WeiqiBoard, BLACK_NUM, WHITE_NUM
from ._decode_coords import decode_lines, decode_labels, decode_letter_coords
from ._draw import (
    find_board_points_with_annotation,
    mass_clear,
    mass_paste_stone,
    mass_paste_annotation,
    mass_draw_lines,
    reset_annotations,
)
from ._image_text import create_cell_text
from ._image_resources import (
    get_stone_images,
    get_board_image,
    get_board_image_no_lines,
    get_draw_cell_size,
)
from ._settings import get_settings


_move_num = 0
_has_used_line_annotations = False
_line_annotations_image = None


def get_has_used_line_annotations():
    return _has_used_line_annotations


def get_line_annotations_image():
    return _line_annotations_image


def set_move_num(move_num):
    global _move_num
    _move_num = move_num


def play_setup_moves(commands_lists, stones_image, annotations_image, board):
    global _move_num, _has_used_line_annotations
    reset_annotations()
    for command in commands_lists[0]:
        run_command(command, stones_image, annotations_image, board)
    _move_num = 1
    _has_used_line_annotations = False


# returns an extra frame (if any)
# and a boolean which states if the move was a pass.
def run_command(command, stones_image, annotations_image, board):
    global _move_num, _has_used_line_annotations, _line_annotations_image
    function_name, parameters = command
    if function_name == "AB":
        # adds initial black stone.
        points = decode_letter_coords(parameters)
        for point in points:
            board.add_initial_stone(point, BLACK_NUM)
        paste_graphic = get_stone_images()[get_draw_cell_size()]["B"]
        mass_paste_stone(stones_image, paste_graphic, points)

    elif function_name == "AW":
        # adds initial white stone.
        points = decode_letter_coords(parameters)
        for point in points:
            board.add_initial_stone(point, WHITE_NUM)
        paste_graphic = get_stone_images()[get_draw_cell_size()]["W"]
        mass_paste_stone(stones_image, paste_graphic, points)

    elif function_name == "AE":
        # clears initial cell.
        points = decode_letter_coords(parameters)
        for point in points:
            board.set_empty_space(point)
        mass_clear(stones_image, points)
        mass_clear(annotations_image, points)

    elif function_name in ["B", "W"]:
        if len(parameters) == 0:
            # move was a pass.
            return None, True

        # plays stone.
        point = decode_letter_coords(parameters)[0]
        player_num = BLACK_NUM if function_name == "B" else WHITE_NUM
        was_legal, cleared_points = board.make_move(point, player_num)

        if get_settings().RENDER_CAPTURES:
            mass_clear(stones_image, cleared_points)
            mass_clear(annotations_image, cleared_points)

        stone_graphic = get_stone_images()[get_draw_cell_size()][function_name]
        mass_paste_stone(stones_image, stone_graphic, [point])

        extra_frame = None
        if get_settings().SHOW_STONE_NUMBERS:
            if not get_settings().MAINTAIN_STONE_NUMBERS:
                # an extra frame is added
                # which obscures (reverts) the shown stone number.
                extra_frame = stones_image.copy()
                extra_frame.alpha_composite(annotations_image)  # UNCERTAIN

            use_marker = get_settings().MARKER_INSTEAD_OF_NUMBERS
            if use_marker:
                paste_graphic = create_cell_text(
                    get_draw_cell_size(),
                    "0",
                    get_settings().PLACEMENT_MARKER_COLOR,
                    get_settings().NUMBER_TEXT_SCALE,
                )
            else:
                move_num_str = str(_move_num)
                n_digits = 1 if use_marker else len(move_num_str)
                color_for_black = get_settings().NUMBER_COLOR_FOR_BLACK
                color_for_white = get_settings().NUMBER_COLOR_FOR_WHITE
                factor = get_settings().DIGIT_TEXT_SCALE_FACTOR
                paste_graphic = create_cell_text(
                    get_draw_cell_size(),
                    move_num_str,
                    color_for_black if function_name == "B" else color_for_white,
                    get_settings().NUMBER_TEXT_SCALE + (n_digits - 1) * factor,
                )

            mass_paste_annotation(
                function_name, annotations_image, paste_graphic, [point], board
            )

        _move_num += 1
        return extra_frame, False

    elif function_name in ["CR", "DD", "MA", "SL", "SQ", "TR"]:
        if len(parameters) == 0 and function_name in ["DD", "SL"]:
            clears = find_board_points_with_annotation(function_name)
            mass_clear(annotations_image, clears)
        else:
            paste_graphic = get_stone_images()[get_draw_cell_size()][function_name]
            points = decode_letter_coords(parameters)
            mass_paste_annotation(
                function_name, annotations_image, paste_graphic, points, board
            )

    elif function_name == "LB":
        points, strings = decode_labels(parameters)
        for i in range(len(points)):
            point = points[i]
            string = strings[i]
            paste_graphic = create_cell_text(
                get_draw_cell_size(),
                string,
                get_settings().LABEL_COLOR,
                get_settings().LABEL_TEXT_SCALE,
            )
            mass_paste_annotation(
                function_name, annotations_image, paste_graphic, [point], board
            )

    elif function_name == "LN":
        lines = decode_lines(parameters)
        if not _has_used_line_annotations:
            _line_annotations_image = Image.new("RGBA", stones_image.size, (0, 0, 0, 0))
            _has_used_line_annotations = True
        mass_draw_lines(_line_annotations_image, lines)

    return None, False
