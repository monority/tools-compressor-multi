from enum import Enum


class MenuAction(Enum):
    COMPRESS_FILE = "1"
    COMPRESS_CURRENT_DIR = "2"
    COMPRESS_DIRECTORY = "3"
    SHOW_FORMATS = "4"
    EXIT = "5"