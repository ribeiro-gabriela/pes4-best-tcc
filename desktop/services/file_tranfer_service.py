from typing import Any

from data.classes import File
from data.errors import (
    CompatibilityError,
    DisconnectedError,
    IdentificationError,
    IntegrityError,
)
from services.arinc_module import ArincModule
from services.connection_service import ConnectionService
from services.file_validator_service import FileValidatorService
from services.logging_service import LoggingService

# Status outputs from ArincModule
STATUS_FINISHED = "TransferFinished"
STATUS_FAILED = "TransferFailed"
STATUS_CANCELLED = "TransferCancelled"

class FileTransferService:
    def __init__(
        self,
        file_validator: FileValidatorService,
        connection_service: ConnectionService,
        arinc_module: ArincModule,
    ):
        self.logging_service = LoggingService(FileTransferService.__name__)
        self.file_validator = file_validator
        self.connection_service = connection_service
        self.arinc_module = arinc_module

    def startTransfer(self, file: File) -> bool:
        # [BST-244]
        if not self.connection_service.isConnected():
            # [BST-242]
            msg = "ConnectionService is not connected."
            err = DisconnectedError(msg)
            self.logging_service.error("startTransfer failed: Not connected.", err)
            raise err

        # [BST-227]
        hardware_pn = self.connection_service.getConnectionHardwarePN()

        # [BST-230]
        _, _, is_identified = self.file_validator.checkIdentification(file)
        if not is_identified:
            # [BST-231]
            msg = f"File identification check failed for {file.fileName}"
            err = IdentificationError(msg)
            self.logging_service.error(msg, err)
            raise err

        # [BST-232]
        _, _, is_integrity_valid = self.file_validator.checkIntegrity(file)
        if not is_integrity_valid:
            # [BST-233]
            msg = f"File integrity check failed for {file.fileName}"
            err = IntegrityError(msg)
            self.logging_service.error(msg, err)
            raise err

        # [BST-228]
        if not self.file_validator.checkCompatibility(file, hardware_pn):
            # [BST-229]
            msg = f"File compatibility check failed for {file.fileName} with hardware {hardware_pn}"
            err = CompatibilityError(msg)
            self.logging_service.error(msg, err)
            raise err

        # [BST-234]
        self.connection_service.pauseHealthCheck()

        # [BST-236]
        self.logging_service.log(
            f"Starting transfer for {file.fileName} to {hardware_pn}."
        )

        # [BST-235]
        result = self.arinc_module.startTransfer(file)

        # [BST-238]
        return result

    def getProgress(self) -> Any:
        # [BST-244]
        if not self.connection_service.isConnected():
            # [BST-242]
            msg = "Cannot getProgress: Not connected."
            err = DisconnectedError(msg)
            self.logging_service.error("getProgress failed: Not connected.", err)
            raise err

        # [BST-237]
        status = self.arinc_module.getProgress()

        # [BST-239]
        if status == STATUS_FINISHED:
            # [BST-239]
            self.connection_service.resumeHealthCheck()
            # [BST-242]
            self.logging_service.log("Transfer operation finished successfully.")

        elif status == STATUS_FAILED:
            # [BST-239]
            self.connection_service.resumeHealthCheck()
            # [BST-242]
            self.logging_service.log("Transfer operation failed.")

        elif status == STATUS_CANCELLED:
            # [BST-242]
            self.logging_service.log("Transfer operation was cancelled.")

        # [BST-237]
        return status

    def cancel(self):
        # [BST-244]
        if not self.connection_service.isConnected():
            # [BST-242]
            msg = "ConnectionService is not connected."
            err = DisconnectedError(msg)
            self.logging_service.error("cancelTransfer failed: Not connected.", err)
            return

        # [BST-245]
        self.arinc_module.cancel()

        # [BST-246]
        self.connection_service.resumeHealthCheck()

        # [BST-247]
        self.logging_service.log("Transfer operation cancelled and health check resumed.")
