import os
import re
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
    get_board_image,
    get_show_width,
    get_show_height,
    get_cell_size,
    get_scaled_margin,
    setup_board,
)
from ._save_gif import save_GIF_to_file
from ._settings import get_settings


_MODIFIERS = ["AB", "AW", "AE", "AR", "CR", "DD", "LB", "LN", "MA", "SL", "SQ", "TR"]
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


def process_senseis_library(directory):
    return


def process_directory(directory):
    all_paths = os.listdir(directory)
    sgf_paths = [
        os.path.join(directory, path) for path in all_paths if path.endswith(".sgf")
    ]

    for path in sgf_paths:
        print(f"\n\n\n{path}")
        get_settings().set_for_animated_diagram()
        save_diagram(path, save_as_static=False)
        get_settings().set_for_static_diagram()
        save_diagram(path, save_as_static=True)

    print(f"{len(sgf_paths)} sgf files in {directory}")


# returns True if saving the diagram was successful.
def save_diagram(sgf_path, save_as_static=False):
    # 1) determines if the SGF is usable.
    if not os.path.exists(sgf_path):
        print(f"could not open {sgf_path}.")
        return

    with open(sgf_path, "r") as file:
        content = file.read()
    content = content.replace("\n", "").replace("(", "").replace(")", "")
    content = _remove_comments(content)
    node_strings = content.split(";")

    if len(node_strings) == 0:
        return
    if len(node_strings[0]) == 0:
        if len(node_strings) == 1:
            return
        node_strings = node_strings[1:]

    if len(node_strings[0]) >= 1:
        for modifier in _MODIFIERS:
            if modifier in node_strings[0]:
                break
        else:
            # no commands in the first node.
            return

    command_lists = [_to_commands(node_str) for node_str in node_strings]
    if len(node_strings) == 1 or (
        len(node_strings) == 2
        and not save_as_static
        and all(
            [(func_name in _ANNOTATION_FUNC_NAMES) for func_name, _ in command_lists[1]]
        )
    ):
        print(f"{sgf_path} doesn't need a GIF.")
        return

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

        if move_was_pass and get_settings().MAINTAIN_NUMBERS_AT_END:
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
    save_path = sgf_path[:-4] + (".gif" if not save_as_static else "_copy.png")

    try:
        if save_as_static:
            base_image.alpha_composite(stones_image)
            base_image.alpha_composite(annotations_image)
            if get_has_used_line_annotations():
                base_image.alpha_composite(get_line_annotations_image())

            base_image = base_image.convert("RGB")
            base_image.save(save_path, format="PNG", compress_level=9)

            # palette_size = get_settings().DIAGRAM_PALETTE_SIZE
            # compressed_image = base_image.quantize(
            #    colors=palette_size, method=Image.FASTOCTREE
            # )
            # compressed_gif.save(save_path, optimize=True, save_all=True)
        else:
            save_GIF_to_file(save_path, frames)
    except:
        print(f"{sgf_path} could not be rendered.")
        return False

    return True


# returns the given string with all comment commands removed.
def _remove_comments(content):
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
def _to_commands(node_str):
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
