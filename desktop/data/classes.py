from dataclasses import dataclass
from datetime import datetime
import uuid

from data.enums import ArincFileType, ArincTransferResult, ArincTransferStep, LoadProtocolStatusCode

@dataclass
class User:
    username: str
    password_hash: str

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
    command: str

@dataclass
class Response:
    status: str
    data: str

@dataclass
class TransferStatus:
    canceled: bool
    currentTarget: str
    transferStep: ArincTransferStep
    fileRecord: FileRecord
    progressPercent: int
    transferResult: ArincTransferResult | None

@dataclass
class ArincLUI:
    FileType = ArincFileType.LUI
    StatusCode: LoadProtocolStatusCode
    StatusDescription: str | None

@dataclass
class ArincLUSHeaderFile:
    FileName: str
    PartNumberName: str
    LoadRatio: int
    LoadStatus: LoadProtocolStatusCode
    LoadDescription: str | None

@dataclass
class ArincLUS:
    FileType = ArincFileType.LUS
    StatusCode: LoadProtocolStatusCode
    StatusDescription: str | None
    Counter: int
    ExceptionTimer: int
    EstimatedTime: int
    LoadListRatio: int
    HeaderFiles: list[ArincLUSHeaderFile]

@dataclass
class ArincLURHeaderFile:
    FileName: str
    PartNumberName: str

@dataclass
class ArincLUR:
    FileType = ArincFileType.LUR
    HeaderFiles: list[ArincLURHeaderFile]

@dataclass
class ArincLUH:
    FileType = ArincFileType.LUH
    DataHash: str
    SoftwarePartNumber: str
    HardwarePartNumber: str
    Size: int