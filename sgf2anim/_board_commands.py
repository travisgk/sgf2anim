import os
from .weiqi_board import WeiqiBoard, BLACK_NUM, WHITE_NUM
from ._draw_board_image import get_draw_cell_size
from ._settings import get_settings
from ._graphics_setup import get_stone_images, decode_letter_coords, decode_labels
from ._paste import mass_clear, mass_paste_stone, mass_paste_annotation
from ._textbox import create_cell_text

MARKER_FUNC_NAMES = [
    "CR",
    "DD",
    "MA",
    "SL",
    "SQ",
    "TR",
]
ANNOTATION_FUNC_NAMES = [
    "AR",
    "C",
    "CR",
    "DD",
    "LB",
    "LN",
    "MA",
    "MN",
    "SL",
    "SQ",
    "TR",
]

_move_num = 0


def play_setup_moves(
    commands_lists,
    stones_image,
    annotations_image,
    board_image,
    board_image_no_lines,
    board,
    cell_size,
    start_point,
):
    global _move_num
    setup_commands = commands_lists[0]
    for command in setup_commands:
        function_name, parameters = command
        run_command(
            function_name,
            stones_image,
            annotations_image,
            board_image,
            board_image_no_lines,
            parameters,
            board,
            cell_size,
            start_point,
        )
    _move_num = 1


# returns an extra frame (if any)
# and a boolean which states if the move was a pass.
def run_command(
    function_name,
    stones_image,
    annotations_image,
    board_image,
    board_image_no_lines,
    parameters,
    board,
    cell_size,
    start_point,
):
    global _move_num
    if function_name == "AB":
        points = decode_letter_coords(parameters)
        for point in points:
            board.add_initial_stone(point, BLACK_NUM)
        paste_image = get_stone_images()[get_draw_cell_size()]["B"]
        mass_paste_stone(
            stones_image, board_image, paste_image, cell_size, points, start_point
        )

    elif function_name == "AW":
        points = decode_letter_coords(parameters)
        for point in points:
            board.add_initial_stone(point, WHITE_NUM)
        paste_image = get_stone_images()[get_draw_cell_size()]["W"]
        mass_paste_stone(
            stones_image, board_image, paste_image, cell_size, points, start_point
        )

    elif function_name == "AE":
        points = decode_letter_coords(parameters)
        for point in points:
            board.set_empty_space(point)
        mass_clear(stones_image, board_image, cell_size, points, start_point)
        mass_clear(annotations_image, board_image, cell_size, points, start_point)

    elif start_point is None:
        return None, False

    elif function_name in [
        "B",
        "W",
    ]:
        if (len(parameters)) == 0:
            return None, True

        point = decode_letter_coords(parameters)[0]
        parameter = parameters[0]

        player_num = BLACK_NUM if function_name == "B" else WHITE_NUM
        was_legal, cleared_points = board.make_move(point, player_num)
        if get_settings().RENDER_CAPTURES:
            mass_clear(
                stones_image, board_image, cell_size, cleared_points, start_point
            )
            mass_clear(
                annotations_image, board_image, cell_size, cleared_points, start_point
            )

        paste_image = get_stone_images()[get_draw_cell_size()][function_name]
        mass_paste_stone(
            stones_image,
            board_image,
            paste_image,
            cell_size,
            [
                point,
            ],
            start_point,
        )

        extra_frame = None
        if get_settings().SHOW_STONE_NUMBERS:
            # an extra frame is added
            # which obscures (reverts) the shown stone number.
            if not get_settings().MAINTAIN_STONE_NUMBERS:
                extra_frame = stones_image.copy()
                extra_frame.alpha_composite(annotations_image)

            use_marker = get_settings().MARKER_INSTEAD_OF_NUMBERS
            if use_marker:
                paste_image = create_cell_text(
                    cell_size,
                    "0",
                    get_settings().PLACEMENT_MARKER_COLOR,
                    get_settings().NUMBER_TEXT_SCALE,
                )
            else:
                color_for_black = get_settings().NUMBER_COLOR_FOR_BLACK
                color_for_white = get_settings().NUMBER_COLOR_FOR_WHITE
                paste_image = create_cell_text(
                    cell_size,
                    "0" if use_marker else str(_move_num),
                    color_for_black if function_name == "B" else color_for_white,
                    get_settings().NUMBER_TEXT_SCALE,
                )

            mass_paste_annotation(
                function_name,
                annotations_image,
                board_image,
                board_image_no_lines,
                stones_image,
                paste_image,
                cell_size,
                [
                    point,
                ],
                start_point,
                board,
            )

        _move_num += 1
        return extra_frame, False

    elif function_name in MARKER_FUNC_NAMES:
        #
        paste_image = get_stone_images()[get_draw_cell_size()][function_name]
        points = decode_letter_coords(parameters)
        mass_paste_annotation(
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
        )

    elif function_name == "LB":
        points, strings = decode_labels(parameters)
        for i in range(len(points)):
            point = points[i]
            string = strings[i]
            paste_image = create_cell_text(
                cell_size, string, (0, 0, 0, 255), get_settings().LABEL_TEXT_SCALE
            )
            mass_paste_annotation(
                function_name,
                annotations_image,
                board_image,
                board_image_no_lines,
                stones_image,
                paste_image,
                cell_size,
                [
                    point,
                ],
                start_point,
                board,
            )

    return None, False  # no extra frame


def set_move_num(move_num):
    global _move_num
    _move_num = move_num
