import os
import time
import sgf2anim


def main():
    start_time = time.time()

    main_dir = os.path.dirname(os.path.abspath(__file__))
    load_dir = os.path.join(main_dir, "_demo_res", "demo_c_res")
    sgf_paths = sgf2anim.find_all_SGF_paths(load_dir)

    # creates diagrams with the "main" style.
    process_files(sgf_paths, "_main")

    # sets up the "frost" style and creates diagrams with it.
    sgf2anim.get_settings().STYLE_NAME = "frost"
    sgf2anim.get_settings().DIGIT_TEXT_SCALE_FACTOR = 0.32
    sgf2anim.get_settings().LEFTWARD_ONE_CLIP_FACTOR = -0.05
    sgf2anim.get_settings().LINE_COLOR = (75, 107, 155)
    sgf2anim.get_settings().LINE_THICKNESS = 1.2
    sgf2anim.get_settings().MARKER_COLOR = (46, 84, 105)

    process_files(sgf_paths, "_frost")

    elapsed = time.time() - start_time
    print(f"that took {elapsed:>.2f} seconds.")


def process_files(sgf_paths, path_addon):
    for sgf_path in sgf_paths:
        # sets particular settings for GIF output.
        sgf2anim.get_settings().SHOW_STONE_NUMBERS = True
        sgf2anim.get_settings().MAINTAIN_STONE_NUMBERS = False
        sgf2anim.get_settings().MAINTAIN_NUMBERS_AT_END = False
        sgf2anim.get_settings().MARKER_INSTEAD_OF_NUMBERS = False
        sgf2anim.get_settings().RENDER_CAPTURES = True

        # saves an animated diagram for the .sgf file.
        out_path = sgf_path[:-4] + path_addon + ".gif"
        sgf2anim.save_diagram(
            sgf_path,
            out_path=out_path,
            frame_delay_ms=1600,
            start_freeze_ms=3000,
            end_freeze_ms=9000,
            number_display_ms=900,
        )

        # sets default settings for a static diagram.
        sgf2anim.get_settings().set_for_static_diagram()

        # saves a static diagram for the .sgf file.
        out_path = sgf_path[:-4] + path_addon + ".png"
        sgf2anim.save_diagram(sgf_path, out_path=out_path)
        print(sgf_path)


if __name__ == "__main__":
    main()
