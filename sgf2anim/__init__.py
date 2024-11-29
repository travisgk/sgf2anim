import os
import re
import time
import numpy as np
from PIL import Image
from ._commands import (
    get_has_used_line_annotations,
    get_line_annotations_image,
    set_move_num,
    play_setup_moves,
    run_command,
)
from ._image_resources import (
    get_stone_images,
    get_board_image,
    get_show_width,
    get_show_height,
    get_cell_size,
    get_scaled_margin,
    setup_board,
)
from ._image_text import create_cell_text
from ._katrain_file import *
from ._save_gif import save_GIF_to_file
from ._settings import get_settings


_ANNOTATION_FUNC_NAMES = [
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


# saves individual stone graphics used in Sensei's Library.
def save_stone_graphics(stones_directory: str):
    GRAPHIC_SIZE = 64
    MARKS = (("CR", "c.png"), ("SQ", "s.png"), ("TR", "t.png"), ("MA", "x.png"))

    for key, image_extension in MARKS:
        get_stone_images()[GRAPHIC_SIZE][key].save(
            os.path.join(stones_directory, "e" + image_extension),
            format="PNG",
            compress_level=9,
        )

    for char, text_color in [
        ("b", get_settings().NUMBER_COLOR_FOR_BLACK),
        ("w", get_settings().NUMBER_COLOR_FOR_WHITE),
    ]:
        stone_graphic = get_stone_images()[GRAPHIC_SIZE][char.upper()]
        stone_graphic.save(
            os.path.join(stones_directory, f"{char}.png"),
            format="PNG",
            compress_level=9,
        )

        for i in range(1, 101):
            comp = create_cell_text(
                GRAPHIC_SIZE,
                str(i),
                text_color,
                get_settings().NUMBER_TEXT_SCALE,
            )
            image = Image.alpha_composite(stone_graphic, comp)
            image.save(
                os.path.join(stones_directory, f"{char}{i}.png"),
                format="PNG",
                compress_level=9,
            )

        for key, image_extension in MARKS:
            Image.alpha_composite(
                stone_graphic, get_stone_images()[GRAPHIC_SIZE][key]
            ).save(
                os.path.join(stones_directory, char + image_extension),
                format="PNG",
                compress_level=9,
            )


def process_directory(
    directory: str,
    out_path_addon: str = "",
    frame_delay_ms: int = 1500,
    start_freeze_ms: int = 3000,
    end_freeze_ms: int = 10000,
    number_display_ms: int = 500,
):
    sgf_paths = find_all_SGF_paths(directory)
    print(f"there are {len(sgf_paths)} sgf files in {directory}.")

    for path in sgf_paths:
        success = False
        get_settings().set_for_animated_diagram()
        success = save_diagram(
            path,
            path[:-4] + out_path_addon + ".gif",
            frame_delay_ms,
            start_freeze_ms,
            end_freeze_ms,
            number_display_ms,
        )
        get_settings().set_for_static_diagram()
        success = success and save_diagram(
            path,
            path[:-4] + out_path_addon + ".png",
            frame_delay_ms,
            start_freeze_ms,
            end_freeze_ms,
            number_display_ms,
        )


def find_all_SGF_paths(directory: str):
    all_paths = os.listdir(directory)
    sgf_paths = [os.path.join(directory, p) for p in all_paths if p.endswith(".sgf")]
    return sgf_paths


# returns True if saving the diagram was successful.
# <frame_delay_ms> is the duration of each frame appears in the GIF.
# <start_freeze_ms> is the duration of the first frame.
# <end_freeze_ms> is the duration of the last frame.
# <number_display_ms> is how long the move number annotation
#                     appears on the stone if they aren't set to be maintained.
def save_diagram(
    sgf_path: str,
    out_path: str = None,
    frame_delay_ms: int = 1500,
    start_freeze_ms: int = 3000,
    end_freeze_ms: int = 10000,
    number_display_ms: int = 500,
):
    save_as_static = not out_path.endswith(".gif")

    # 1) determines if the SGF is usable.
    if not os.path.exists(sgf_path):
        print(f"could not open {sgf_path}.")
        return False

    used_temp_file = False
    temp_path = sgf_path[:-4] + "-temp.sgf"

    def delete_temp_file():
        # deletes the temporary .sft file if one was created.
        if used_temp_file:
            os.remove(temp_path)

    if is_katrain_file(sgf_path):
        used_temp_file = True
        create_cleaned_katrain_file(in_path=sgf_path, out_path=temp_path)
        sgf_path = temp_path

    with open(sgf_path, "r") as file:
        content = file.read()
    content = content.replace("\n", "").replace("(", "").replace(")", "")
    content = _remove_comments(content)
    node_strings = content.split(";")

    if len(node_strings) == 0:
        print("No node strings were found.")
        return False
    while len(node_strings[0]) == 0:
        if len(node_strings) == 1:
            print("Only one node string was found.")
            return False
        node_strings = node_strings[1:]

    command_lists = [_to_commands(node_str) for node_str in node_strings]
    if len(node_strings) == 1 or (
        len(node_strings) == 2
        and not save_as_static
        and all(
            [(func_name in _ANNOTATION_FUNC_NAMES) for func_name, _ in command_lists[1]]
        )
    ):
        print(f"{sgf_path} doesn't need a GIF.")
        return False

    # 2) sets all the components up.
    board = setup_board(sgf_path, command_lists)
    stones_image = _create_change_image()
    annotations_image = _create_change_image()
    play_setup_moves(command_lists, stones_image, annotations_image, board)

    base_image = Image.alpha_composite(get_board_image(), stones_image)
    base_image.alpha_composite(annotations_image)
    if get_has_used_line_annotations():
        base_image.alpha_composite(get_line_annotations_image())

    if not save_as_static:
        frames = []
        frames.append((base_image, False))
        stones_image = _create_change_image()
        annotations_image = _create_change_image()

    # 3) executes the commands contained in every node.
    for i in range(1, len(node_strings)):
        commands = command_lists[i]

        # any move number command will always be run first.
        for j, command in enumerate(commands):
            function_name, parameters = command

            if function_name == "MN":
                set_move_num(int(parameters[0]))
                del commands[j]
                break

        # runs the rest of the commands.
        extra_frame = None
        move_was_pass = False
        for command in commands:
            command_extra_frame, was_pass = run_command(
                command, stones_image, annotations_image, board
            )
            if command_extra_frame is not None:
                extra_frame = command_extra_frame
            if was_pass:
                move_was_pass = True

        # frame is dropped if set to do so with a passing move
        # or if the node consisted only of annotative commands.
        if (move_was_pass and get_settings().MAINTAIN_NUMBERS_AT_END) or (
            all([(func_name in _ANNOTATION_FUNC_NAMES) for func_name, _ in commands])
        ):
            continue

        if not save_as_static:
            stones_image.alpha_composite(annotations_image)
            if get_has_used_line_annotations():
                stones_image.alpha_composite(get_line_annotations_image())
            frames.append((stones_image, False))

            if extra_frame is not None:
                # the image of the stone w/o annotations
                # is added after the frame where the move number is shown
                # in order to make the move number on the stone disappear.
                if get_has_used_line_annotations():
                    extra_frame.alpha_composite(get_line_annotations_image())
                frames.append((extra_frame, True))

            stones_image = _create_change_image()
            annotations_image = _create_change_image()

    # 4) saves the frame(s) to file.
    try:
        if save_as_static:
            base_image.alpha_composite(stones_image)
            base_image.alpha_composite(annotations_image)
            if get_has_used_line_annotations():
                base_image.alpha_composite(get_line_annotations_image())

            base_image = base_image.convert("RGB")
            base_image.save(out_path, format="PNG", compress_level=9)
        else:
            save_GIF_to_file(
                out_path,
                frames,
                frame_delay_ms,
                start_freeze_ms,
                end_freeze_ms,
                number_display_ms,
            )
    except:
        print(f"{sgf_path} could not be rendered.")
        delete_temp_file()
        return False

    delete_temp_file()
    return True


# returns the given string with all comment commands removed.
def _remove_comments(content: str):
    pattern = r'GN\[|C\["?'
    while True:
        start_match = re.search(pattern, content)
        if start_match:
            start_index = start_match.start()
            end_match = re.search(r"\][A-Z]", content[start_index:])
            end_index = None
            if end_match:
                end_index = start_index + end_match.start() + 1
            elif content[-1] == "]":
                end_index = len(content)
            if end_index is not None:
                content = content[:start_index] + content[end_index:]
            else:
                break
        else:
            break
    return content


# returns a string broken down
# into strings of commands tuples (function name + param).
def _to_commands(node_str: str):
    commands = []
    while True:
        start_match = re.search(r"[A-Z]\[", node_str)
        if start_match:
            start_index = start_match.start()
            end_match = re.search(r"\][A-Z]", node_str[start_index:])
            end_index = None
            if end_match:
                end_index = start_index + end_match.start() + 1
            elif node_str[-1] == "]":
                end_index = len(node_str)
            if end_index is not None:
                parameters_str = node_str[start_index + 1 : end_index]
                parameters_str = parameters_str[1:-1]
                parameters = parameters_str.split("][")
                parameters = [p for p in parameters if len(p) > 0]
                commands.append(
                    (
                        node_str[0 : start_index + 1],
                        parameters,
                    )
                )
                node_str = node_str[end_index:]
            else:
                break
        else:
            break

    return commands


# creates a clear buffer image that will be alpha composited on top of the frame.
def _create_change_image():
    w = get_scaled_margin() * 2 + get_cell_size() * get_show_width()
    h = get_scaled_margin() * 2 + get_cell_size() * get_show_height()
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))
