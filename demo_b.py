import os
import time
import sgf2anim


def main():
    start_time = time.time()

    main_dir = os.path.dirname(os.path.abspath(__file__))
    load_dir = os.path.join(main_dir, "_demo_res", "demo_b_res")
    sgf_paths = sgf2anim.find_all_SGF_paths(load_dir)

    sgf2anim.get_settings().MARKER_COLOR = (29, 127, 164)
    for sgf_path in sgf_paths:
        print(sgf_path)

        # saves an animated diagram for the .sgf file.
        sgf2anim.get_settings().SHOW_STONE_NUMBERS = True
        sgf2anim.get_settings().MAINTAIN_STONE_NUMBERS = True
        sgf2anim.get_settings().MAINTAIN_NUMBERS_AT_END = True
        sgf2anim.get_settings().MARKER_INSTEAD_OF_NUMBERS = False
        sgf2anim.get_settings().RENDER_CAPTURES = True

        # saves an animated diagram for the .sgf file.
        out_path = sgf_path[:-4] + "_output.gif"
        sgf2anim.save_diagram(
            sgf_path,
            out_path=out_path,
            frame_delay_ms=1500,
            start_freeze_ms=3000,
            end_freeze_ms=10000,
            number_display_ms=1000,
        )

        # sets default settings for a static diagram.
        sgf2anim.get_settings().set_for_static_diagram()

        out_path = sgf_path[:-4] + "_output.png"
        sgf2anim.save_diagram(sgf_path, out_path=out_path)

    elapsed = time.time() - start_time
    print(f"that took {elapsed:>.2f} seconds.")


if __name__ == "__main__":
    main()
