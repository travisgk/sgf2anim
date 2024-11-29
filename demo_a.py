import os
import time
import sgf2anim


def main():
    start_time = time.time()

    main_dir = os.path.dirname(os.path.abspath(__file__))
    load_dir = os.path.join(main_dir, "_demo_res", "demo_a_res")

    # creates a static diagram (and animated diagram, if there are moves)
    # for every .sgf file in the <load_dir>.
    sgf2anim.process_directory(
        load_dir,
        out_path_addon="_output",
        frame_delay_ms=1200,
        start_freeze_ms=3000,
        end_freeze_ms=10000,
        number_display_ms=1200,
    )

    # saves stone graphics to a directory.
    output_stones_dir = os.path.join(load_dir, "stones")
    try:
        os.makedirs(output_stones_dir, exist_ok=True)
    except OSError as error:
        print(f"error creating directory '{output_stones_dir}': {error}")
    sgf2anim.save_stone_graphics(output_stones_dir)

    elapsed = time.time() - start_time
    print(f"that took {elapsed:>.2f} seconds.")


if __name__ == "__main__":
    main()
