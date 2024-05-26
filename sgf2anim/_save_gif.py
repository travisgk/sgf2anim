import numpy as np
import imageio.v3 as imageio
from PIL import Image
from ._settings import get_settings


def save_GIF_to_file(
    save_path,
    frames,
    frame_delay_ms=1500,
    start_freeze_ms=3000,
    end_freeze_ms=10000,
    number_display_ms=500,
):
    n_frames = len(frames)
    extra_frame_ms = max(0, frame_delay_ms - number_display_ms)

    durations = []
    save_frames = []
    for i in range(n_frames):
        frame = frames[i][0]
        is_extra_frame = frames[i][1]

        if not is_extra_frame and extra_frame_ms == 0 and i - 1 >= 0:
            prev_frame = frames[i - 1][0]
            prev_is_extra_frame = frames[i - 1][1]
            if prev_is_extra_frame:
                frame = Image.alpha_composite(prev_frame, frame)

        if (
            extra_frame_ms > 0
            or not is_extra_frame
            or (i == n_frames - 1 and not get_settings().MAINTAIN_NUMBERS_AT_END)
        ):
            if get_settings().MAINTAIN_STONE_NUMBERS:
                duration = frame_delay_ms
            elif is_extra_frame:
                duration = extra_frame_ms
            else:
                duration = number_display_ms
            durations.append(duration)
            save_frames.append(np.array(frame, dtype=np.uint8))

    durations[0] = start_freeze_ms
    durations[-1] = end_freeze_ms
    imageio.imwrite(
        save_path, save_frames, duration=durations, loop=0, subrectangles=True
    )
