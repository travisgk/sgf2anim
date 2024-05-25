class Settings:
    def __init__(self):
        # the settings for image resolution.
        self.MAX_WIDTH = 1000
        self.MAX_HEIGHT = 1000
        self.IMAGE_MARGIN = 2
        self.MIN_CELL_SIZE = 4
        self.MAX_CELL_SIZE = 256

        # the settings for the appearance of numbers on stones.
        self.SHOW_STONE_NUMBERS = True
        self.MAINTAIN_STONE_NUMBERS = True
        self.MAINTAIN_NUMBERS_AT_END = True
        self.MARKER_INSTEAD_OF_NUMBERS = False
        self.LABEL_TEXT_SCALE = 0.55
        self.NUMBER_TEXT_SCALE = 0.51
        self.DIGIT_TEXT_SCALE_FACTOR = 0.2
        self.LEFTWARD_ONE_CLIP_FACTOR = 0.06
        self.CENTER_LABELS_VERTICALLY = False
        self.LETTERS_PADDING_BOTTOM_PERCENT = 0.15
        self.NUMBERS_PADDING_BOTTOM_PERCENT = 0.03

        # the settings for styling.
        self.STYLE_NAME = "main"
        self.LINE_COLOR = (63, 39, 32)
        self.LINE_THICKNESS = 1.1
        self.MARKER_COLOR = (29, 164, 98)
        self.LABEL_COLOR = (0, 0, 0)
        self.PLACEMENT_MARKER_COLOR = (0, 138, 225)
        self.NUMBER_COLOR_FOR_BLACK = (255, 255, 255)
        self.NUMBER_COLOR_FOR_WHITE = (0, 0, 0)
        self.ANNOTATE_LINE_COLOR = (0, 30, 180)
        self.ANNOTATE_LINE_THICKNESS = 8.0

        # additional render settings.
        self.DISPLAY_PADDING = 1  # the padding around all active cells.
        self.FORCE_STONES_CENTER = False
        self.RENDER_CAPTURES = False

        # for future implementation of a formatting for Sensei's Library.
        # if True, this will use the previous existing .png for the .sgf
        # in order to determine the viewport size of diagrams.
        self.DOING_SENSEIS_FORMAT = False

    # sets particular settings that are ideal for a static diagram image.
    def set_for_static_diagram(self):
        self.SHOW_STONE_NUMBERS = True
        self.MAINTAIN_STONE_NUMBERS = True
        self.MAINTAIN_NUMBERS_AT_END = True
        self.MARKER_INSTEAD_OF_NUMBERS = False
        self.RENDER_CAPTURES = False

    # sets particular settings that are ideal for an animated diagram GIF.
    def set_for_animated_diagram(self):
        self.SHOW_STONE_NUMBERS = True
        self.MAINTAIN_STONE_NUMBERS = False
        self.MAINTAIN_NUMBERS_AT_END = False
        self.MARKER_INSTEAD_OF_NUMBERS = True
        self.RENDER_CAPTURES = True


_settings = Settings()


def get_settings():
    return _settings
