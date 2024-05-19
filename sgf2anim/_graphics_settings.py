class Settings:
	def __init__(self):
		self.MAX_WIDTH = 600
		self.MAX_HEIGHT = 600
		self.IMAGE_MARGIN = 2

		self.MIN_CELL_SIZE = 4
		self.MAX_CELL_SIZE = 256

		self.SHOW_STONE_NUMBERS = True
		self.MAINTAIN_STONE_NUMBERS = True
		self.MAINTAIN_NUMBERS_AT_END = True
		self.MARKER_INSTEAD_OF_NUMBERS = False
		self.LABEL_TEXT_SCALE = 0.55
		self.NUMBER_TEXT_SCALE = 0.51
		self.CENTER_LABELS_VERTICALLY = False

		self.STYLE_NAME = "main"
		self.LINE_COLOR = (63, 39, 32)
		self.LINE_THICKNESS = 1
		self.MARKER_COLOR = (29, 164, 98)
		self.PLACEMENT_MARKER_COLOR = (0, 138, 225)
		self.NUMBER_COLOR_FOR_BLACK = (255, 255, 255)
		self.NUMBER_COLOR_FOR_WHITE = (0, 0, 0)

		self.FORCE_STONES_CENTER = False
		self.RENDER_CAPTURES = False
		self.DIAGRAM_PALETTE_SIZE = 128 # 64, 32, etc., for more compression


	def set_for_diagram(self):
		self.SHOW_STONE_NUMBERS = True
		self.MAINTAIN_STONE_NUMBERS = True
		self.MAINTAIN_NUMBERS_AT_END = True
		self.MARKER_INSTEAD_OF_NUMBERS = False
		self.RENDER_CAPTURES = False


	def set_for_animated_diagram(self):
		self.SHOW_STONE_NUMBERS = True
		self.MAINTAIN_STONE_NUMBERS = False
		self.MAINTAIN_NUMBERS_AT_END = True
		self.MARKER_INSTEAD_OF_NUMBERS = True
		self.RENDER_CAPTURES = True


	def set_for_animated_game(self):
		self.SHOW_STONE_NUMBERS = True
		self.MAINTAIN_STONE_NUMBERS = False
		self.MAINTAIN_NUMBERS_AT_END = False
		self.MARKER_INSTEAD_OF_NUMBERS = True
		self.RENDER_CAPTURES = True


_settings = Settings()

def get_settings():
	return _settings