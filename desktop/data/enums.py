from enum import Enum

class ScreenName(Enum):
    MAIN = "main"
    IMAGES = "images"
    CONNECTION = "connection"
    LOGIN = "login"
    POST_CONNECTION = "post_connection"
    FILE_TRANSFER = "file_transfer"
    ERROR = "error"

class ArincFileType(Enum):
    LUI='LUI'
    LUS='LUS'
    LUR='LUR'
    LUH='LUH'

class ArincTransferStep(Enum):
    NOT_IN_TRANSFER='not_in_transfer'
    INIT='initialization'
    LIST='list_trasnfer'
    TRANFER='transfer'