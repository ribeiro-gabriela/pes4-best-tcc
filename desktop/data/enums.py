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

class ArincTransferResult(Enum):
    SUCCESS='success'
    FAILED='failed'

class LoadProtocolStatusCode(Enum):
    ACCEPTED='0001'
    IN_PROGRESS='0002'
    COMPLETED='0003'
    IN_PROGRESS_INFO='0004'
    NOT_ACCEPTED='1000'
    NOT_SUPPORTED='1002'
    ABORTED_BY_TARGET='1003'
    ABORTED_BY_DATA_LOADER='1004'
    ABORTED_BY_OPERATOR='1005'
    FAILED='1007'