
class IntegrityError(Exception):
    pass

class IdentificationError(Exception):
    pass

class DuplicateFileError(Exception):
    pass


class ConnectionAuthenticationError(Exception):
    pass

class ConnectionError(Exception):
    pass

class RequestTimeoutError(Exception):
    pass


class DisconnectedError(Exception):
    pass

class CompatibilityError(Exception):
    pass

class FileAccessError(Exception):
    pass