import numpy as np
import imageio.v3 as imageio
from PIL import Image
from ._graphics_settings import get_settings

from ._profiling import reset_time, get_elapsed_time

def save_GIF_to_file(
	save_path,
	frames,
	frame_delay_ms=1500,
	start_freeze_ms=3000,
	end_freeze_ms=10000,
	number_display_ms=500
):
	reset_time() # DEBUG
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
				print("this is making an alpha_composite with extra")
				#prev_frame.show()
				#frame.show()
				frame = Image.alpha_composite(prev_frame, frame)
				#frame.show()
				print("end showing alpha comp")



		if not is_extra_frame or extra_frame_ms > 0 and not(i == n_frames - 1 and is_extra_frame and get_settings().MAINTAIN_NUMBERS_AT_END):
			if get_settings().MAINTAIN_STONE_NUMBERS:
				duration = frame_delay_ms
			elif is_extra_frame:
				duration = extra_frame_ms
			else:
				duration = number_display_ms
			durations.append(duration)
			save_frames.append(np.array(frame, dtype=np.uint8))

		'''elif (
			not get_settings().MAINTAIN_NUMBERS_AT_END 
			and is_extra_frame and i == n_frames - 1
		):
			durations.append(frame_delay_ms)
			save_frames.append(np.array(frame, dtype=np.uint8))'''
	durations[0] = start_freeze_ms
	durations[-1] = end_freeze_ms
	print(f"writing frames took {get_elapsed_time():.2f}.") # DEBUG

	reset_time() # DEBUG
	imageio.imwrite(save_path, save_frames, duration=durations, loop=0, subrectangles=False)
	print(f"imageio.imwrite took {get_elapsed_time():.2f}.") # DEBUG
	

	# The last frame is now loaded
	#last_frame = gif.convert("RGBA")  # Ensure it's in RGBA format if you want to keep transparency
	#last_frame.show()