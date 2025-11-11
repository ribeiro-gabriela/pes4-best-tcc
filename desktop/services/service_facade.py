from data.classes import File, FileRecord
from services.connection_service import ConnectionService
from services.file_tranfer_service import FileTransferService
from services.imported_files_service import ImportedFilesService
from services.user_authentication_service import UserAuthenticationService
from services.file_validator_service import FileValidatorService
from services.wifi_module import get_wifi_connections
from typing import List, Any

class ServiceFacade:
    def __init__(
        self,
        authentication_service: UserAuthenticationService,
        connection_service: ConnectionService,
        file_transfer_service: FileTransferService,
        imported_files_service: ImportedFilesService,
        file_validator_service: FileValidatorService,
    ):
        self.authentication_service = authentication_service
        self.connection_service = connection_service
        self.file_transfer_service = file_transfer_service
        self.imported_files_service = imported_files_service
        self.file_validator_service = file_validator_service

    def login(self, username: str, password: str) -> None:
        # [BST-331]
        return self.authentication_service.login(username, password)

    def isAuthenticated(self) -> bool:
        # [BST-332]
        return self.authentication_service.isAuthenticated()

    def logout(self) -> None:
        return self.authentication_service.logout()

    def connect(self, target: str) -> None:
        return self.connection_service.connect(target)

    def disconnect(self) -> None:
        # [BST-316]
        return self.connection_service.disconnect()

    def getConnectionHardwarePN(self) -> str:
        # [BST-313]
        return self.connection_service.getConnectionHardwarePN()

    def isConnected(self) -> bool:
        return self.connection_service.isConnected()

    def startTransfer(self, file: File) -> bool:
        # [BST-319]
        return self.file_transfer_service.startTransfer(file)

    def getProgress(self) -> Any:
        # [BST-320, BST-321, BST-324]
        return self.file_transfer_service.getProgress()

    def cancelTransfer(self) -> None:
        return self.file_transfer_service.cancel()

    def listImportedFiles(self) -> List[FileRecord]:
        return self.imported_files_service.list()

    def listImportedFilesFiltered(self, hardware_pn: str) -> List[FileRecord]:
        # [BST-314]
        return self.imported_files_service.listFiltered(hardware_pn)

    def importFile(self, file: File) -> FileRecord:
        # [BST-333]
        return self.imported_files_service.importFile(file)

    def deleteImportedFile(self, softwarePN: str) -> None:
        return self.imported_files_service.delete(softwarePN)

    def getFileMetadata(self, file_id: str) -> FileRecord:
        return self.imported_files_service.get(file_id)

    # File Validator Service methods
    def checkFileIdentification(self, file: File):
        return self.file_validator_service.checkIdentification(file)

    def checkFileIntegrity(self, file: File):
        return self.file_validator_service.checkIntegrity(file)

    def checkFileCompatibility(self, file: File, hardwarePN: str) -> bool:
        return self.file_validator_service.checkCompatibility(file, hardwarePN)