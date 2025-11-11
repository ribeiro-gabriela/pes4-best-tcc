from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class User:
    id: uuid.UUID
    username: str

@dataclass
class Session:
    user: User
    lastActivityAt: datetime

@dataclass
class File:
    path: str
    fileName: str

@dataclass
class FileRecord:
    file: File
    softwarePN: str
    hardwarePN: str
    dataHash: str
    importedAt: datetime
    sizeBytes: int


@dataclass
class Connection:
    device: str
    hardwarePN: str
    address: str
    connectedAt: str
    # [BST-208]
    # [BST-209]
    # [BST-210]
    pauseHealthCheck: bool = False

@dataclass
class Package:
    pass

@dataclass
class Request:
    pass

@dataclass
class Response:
    pass