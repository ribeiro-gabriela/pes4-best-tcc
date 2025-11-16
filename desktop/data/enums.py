from enum import Enum

class ScreenName(Enum):
    MAIN = "main"
    IMAGES = "images"
    CONNECTION = "connection"
    LOGIN = "login"
    POST_CONNECTION = "post_connection"
    FILE_TRANSFER = "file_transfer"
    ERROR = "error"

class AppState(Enum):
    LOGIN = 'Login'
    MAIN = 'Main'
    CONNECTION = 'Connection'
    IMAGES = 'Images'
    POST_CONNECTION = 'PostConnection'
    LOADING = 'Loading'
    ERROR = 'Error'
    
class ArincTransferResult(Enum):
    SUCCESS='success'
    FAILED='failed'
