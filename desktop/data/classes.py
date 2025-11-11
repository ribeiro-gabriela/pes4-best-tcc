from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class User:
    username: str
    password_hash: str

@dataclass
class Session:
    user: User
    # [BST-287]
    createdAt: datetime
    expiresAt: datetime  # (Definido no login, ex: 8 horas)

    def is_expired(self) -> bool:
        # [BST-291]
        return datetime.now() > self.expiresAt

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
    command: str

@dataclass
class Response:
    status: str
    data: str