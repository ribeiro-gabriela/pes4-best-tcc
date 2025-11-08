from typing import Any

from data.classes import File, FileRecord
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

        # (Status assumed from ArincModule based on requirements)
        self.STATUS_FINISHED = "TransferFinished"
        self.STATUS_FAILED = "TransferFailed"
        self.STATUS_CANCELLED = "TransferCancelled"

    def startTransfer(self, file_record: FileRecord) -> bool:
        file = file_record.file
        # [BST-244]
        if not self.connection_service.isConnected():
            err = DisconnectedError("ConnectionService is not connected.")
            # [BST-242]
            self.logging_service.error("startTransfer failed: Not connected.", err)
            raise err

        try:
            # [BST-227]
            hardware_pn = self.connection_service.getConnectionHardwarePN()

            # [BST-230]
            if not self.file_validator.checkIdentification(file):
                # [BST-231]
                raise IdentificationError("File identification check failed.")

            # [BST-232]
            if not self.file_validator.checkIntegrity(file):
                # [BST-233]
                raise IntegrityError("File integrity check failed.")

            # [BST-228]
            if not self.file_validator.checkCompatibility(file, hardware_pn):
                # [BST-229]
                raise CompatibilityError(
                    f"File not compatible with hardware {hardware_pn}."
                )

            # Validations passed

            # [BST-234]
            self.connection_service.pauseHealthCheck()

            try:
                # [BST-236]
                self.logging_service.log(
                    f"Starting transfer for {file.fileName} to {hardware_pn}."
                )

                # [BST-235]
                result = self.arinc_module.startTransfer(file_record)

                # [BST-238]
                return result

            except Exception as transfer_ex:
                # (Handle failure during ArincModule.startTransfer)
                # [BST-242]
                self.logging_service.error(
                    "startTransfer failed during ArincModule execution.", transfer_ex
                )
                # [BST-239] (Implied: Resume HC if start fails after pause)
                self.connection_service.resumeHealthCheck()
                raise transfer_ex

        except (
            IdentificationError,
            IntegrityError,
            CompatibilityError,
        ) as validation_ex:
            # [BST-242]
            self.logging_service.error(
                f"startTransfer failed validation: {validation_ex}", validation_ex
            )
            raise validation_ex

    def getProgress(self) -> Any:
        # [BST-244]
        if not self.connection_service.isConnected():
            err = DisconnectedError("Cannot getProgress: Not connected.")
            # [BST-242]
            self.logging_service.error("getProgress failed: Not connected.", err)
            raise err

        # [BST-237]
        status = self.arinc_module.getProgress()

        # [BST-239]
        if status == self.STATUS_FINISHED:
            # [BST-239]
            self.connection_service.resumeHealthCheck()
            # [BST-242]
            self.logging_service.log("Transfer operation finished successfully.")

        elif status == self.STATUS_FAILED:
            # [BST-239] (Implied: Resume HC on failure state)
            self.connection_service.resumeHealthCheck()
            # [BST-242]
            self.logging_service.log("Transfer operation failed.")

        elif status == self.STATUS_CANCELLED:
            # [BST-239] (Implied: Resume HC on cancel state)
            self.connection_service.resumeHealthCheck()
            # [BST-242]
            self.logging_service.log("Transfer operation was cancelled.")

        # [BST-237]
        return status

    def cancel(self):
        # [BST-247]
        self.logging_service.log("Attempting to cancel transfer operation.")

        # [BST-244]
        if not self.connection_service.isConnected():
            self.logging_service.log("Cancel request: Not connected.")
            return

        # [BST-245]
        self.arinc_module.cancel()

        # [BST-246]
        self.connection_service.resumeHealthCheck()

        # [BST-247]
        # [BST-242]
        self.logging_service.log("Cancel operation processed; health check resumed.")
