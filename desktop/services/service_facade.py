from data.classes import File, FileRecord
from services.connection_service import ConnectionService
from services.file_tranfer_service import FileTransferService
from services.imported_files_service import ImportedFilesService
from services.user_authentication_service import UserAuthenticationService
from services.wifi_module import WifiModule

from typing import List, Any, Tuple
from data.errors import IdentificationError


class ServiceFacade:
    def __init__(
        self,
        authentication_service: UserAuthenticationService,
        connection_service: ConnectionService,
        file_transfer_service: FileTransferService,
        imported_files_service: ImportedFilesService,
    ):
        self.authentication_service = authentication_service
        self.connection_service = connection_service
        self.file_transfer_service = file_transfer_service
        self.imported_files_service = imported_files_service

    def login(self, username: str, password: str) -> Tuple[bool, str]:
        # [BST-331]
        try:
            self.authentication_service.login(username, password)
            return True, "Login successfully!"
        except IdentificationError as e:
            return False, str(e) 
        except Exception as e:
            return False, f"An unexpected error occurred during login: {e}"

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
        # [BST-320]
        # [BST-321]
        # [BST-324]
        return self.file_transfer_service.getProgress()

    def cancel(self) -> None:
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
    
    def getWifiConnections(self) -> List[dict]: 
        return self.connection_service.scan() 
    
    def connectToWifi(self, target: str, password: str = None) -> None: 
        self.connection_service.connect(target, password)