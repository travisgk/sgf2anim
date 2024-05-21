import os
import numpy as np
import re
from PIL import Image
from ._settings import get_settings
from ._graphics_setup import get_scaled_margin, setup_board
from ._draw_board_image import draw_board_image
from ._board_commands import (
    ANNOTATION_FUNC_NAMES,
    play_setup_moves,
    run_command,
    set_move_num,
)
from ._save_gif import save_GIF_to_file


from ._profiling import reset_time, get_elapsed_time


def process_directory(directory):
    all_files = os.listdir(directory)
    sgf_file_paths = [
        os.path.join(directory, file) for file in all_files if file.endswith(".sgf")
    ]

    for path in sgf_file_paths:
        print(f"\n\n\n{path}")
        get_settings().set_for_animated_diagram()
        save_GIF(path, save_as_diagram=False)
        get_settings().set_for_diagram()
        save_GIF(path, save_as_diagram=True)

    print(f"{len(sgf_file_paths)} sgf files in {directory}")
    print(sgf_file_paths[:5])





# returns True if saving the GIF was successful.
def save_GIF(sgf_path, save_path=None, save_as_diagram=False):
    reset_time()  # DEBUG

    # determines the SGF is usable.
    if not os.path.exists(sgf_path):
        print(f"could not open {sgf_path}.")
        return

    with open(sgf_path, "r") as file:
        content = file.read()
    content = content.replace("\n", "").replace("(", "").replace(")", "")
    content = _remove_comments(content)

    nodes = content.split(";")

    if len(nodes) == 0:
        # file cannot be used.
        return

    if len(nodes[0]) == 0:
        if len(nodes) == 1:
            # file cannot be used.
            return
        nodes = nodes[1:]

    if len(nodes[0]) == 1:
        modifiers = [
            "AB",
            "AW",
            "AE",
            "AR",
            "CR",
            "DD",
            "LB",
            "LN",
            "MA",
            "SL",
            "SQ",
            "TR",
        ]
        for modifier in modifiers:
            if modifier in nodes[0]:
                break
        else:
            # file cannot be used.
            return

    commands_lists = [_to_commands(node) for node in nodes]

    if (
        len(nodes) == 1 
        or (
            len(nodes) == 2 
            and not save_as_diagram 
            and all(
                [
                    (func_name in ANNOTATION_FUNC_NAMES) 
                    for func_name, _ in commands_lists[1]
                ]
            )
        )
    ):
        # this doesn't need a GIF.
        print(f"{sgf_path} doesn't need a GIF.")
        return

    # 
    board, cell_size, show_size, start_point = setup_board(
        sgf_path, nodes, commands_lists
    )

    board_image, board_image_no_lines = draw_board_image(
        board, cell_size, show_size, start_point
    )

    image_of_stone_changes = _create_change_image(cell_size, show_size)
    image_of_annotation_changes = _create_change_image(cell_size, show_size)

    play_setup_moves(
        commands_lists,
        image_of_stone_changes,
        image_of_annotation_changes,
        board_image,
        board_image_no_lines,
        board,
        cell_size,
        start_point,
    )

    base_image = Image.alpha_composite(board_image, image_of_stone_changes)
    base_image = Image.alpha_composite(base_image, image_of_annotation_changes)
    # base_image.show()

    if not save_as_diagram:
        frames = []
        frames.append(
            (
                base_image,
                False,
            )
        )
        image_of_changes = _create_change_image(cell_size, show_size)

    for i, node in enumerate(nodes):
        if i == 0:
            continue
        commands = commands_lists[i]

        # move number command will always be run first.
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
            function_name, parameters = command
            command_extra_frame, was_pass = run_command(
                function_name,
                image_of_stone_changes,
                image_of_annotation_changes,
                board_image,
                board_image_no_lines,
                parameters,
                board,
                cell_size,
                start_point,
            )
            if command_extra_frame is not None:
                extra_frame = command_extra_frame
            if was_pass:
                move_was_pass = True

        if move_was_pass and get_settings().MAINTAIN_NUMBERS_AT_END:
            continue

        if not save_as_diagram:
            image_of_stone_changes.alpha_composite(image_of_annotation_changes)
            frames.append((image_of_stone_changes, False))
            # image_of_changes.show()
            if extra_frame is not None:
                frames.append((extra_frame, True))
            image_of_stone_changes = _create_change_image(cell_size, show_size)
            image_of_annotation_changes = _create_change_image(cell_size, show_size)

    if save_path is None:
        save_path = sgf_path[:-4] + (".gif" if not save_as_diagram else "_copy.png")

    try:
        if save_as_diagram:
            image_of_stone_changes.alpha_composite(image_of_annotation_changes)
            base_image.alpha_composite(image_of_stone_changes)
            base_image = base_image.convert("RGB")
            # base_image.save(save_path, format="PNG", compress_level=9)

            palette_size = get_settings().DIAGRAM_PALETTE_SIZE
            compressed_gif = base_image.quantize(
                colors=palette_size, method=Image.FASTOCTREE
            )
            compressed_gif.save(save_path, optimize=True, save_all=True)
        else:
            save_GIF_to_file(save_path, frames)

    except:
        print(f"{sgf_path} could not be rendered.")
        return False
    print(f"primary function took {get_elapsed_time():.2f}.")  # DEBUG
    return True


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


def _create_change_image(cell_size, show_size):
    w = get_scaled_margin() * 2 + cell_size * show_size[0]
    h = get_scaled_margin() * 2 + cell_size * show_size[1]
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))
