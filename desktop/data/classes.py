from dataclasses import dataclass
from datetime import datetime
import uuid

from data.enums import ArincTransferResult, ArincTransferStep

@dataclass
class User:
    id: uuid.UUID
    username: str

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
    connectedAt: int
    # [BST-208]
    # [BST-209]
    # [BST-210]
    pauseHealthCheck: bool = False

@dataclass
class Package:
    name: str
    path: str

@dataclass
class Request:
    pass

@dataclass
class Response:
    pass

@dataclass
class TransferStatus:
    canceled: bool
    currentTarget: str
    transferStep: ArincTransferStep
    fileRecord: FileRecord
    progressPercent: int
    transferResult: ArincTransferResult | None