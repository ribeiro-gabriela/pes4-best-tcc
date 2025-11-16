from io import BufferedReader
import threading
import time
import os

from typing import Literal
from data.classes import (
    ArincLUH,
    ArincLUI,
    ArincLUR,
    ArincLURHeaderFile,
    ArincLUS,
    ArincLUSHeaderFile,
    FileRecord,
    Package,
    TransferStatus,
)

from data.enums import (
    ArincFileType,
    ArincTransferResult,
    ArincTransferStep,
    LoadProtocolStatusCode,
)
from services.connection_service import ConnectionService
from services.logging_service import LoggingService
from tftpy import TftpServer

version: Literal["A4"] = "A4"


class ArincModule:
    transfer_status: TransferStatus | None = None
    transfer_thread: threading.Thread | None = None

    def __init__(self, connection_service: ConnectionService):
        self.logging_service = LoggingService(ConnectionService.__name__)
        self.connection_service = connection_service
        self.tftp_server_thread = threading.Thread(
            target=self._tftp_server_thread, daemon=True
        )
        self.tftp_server_thread.start()

    # [BST-235]
    def startTransfer(self, file: FileRecord) -> bool:
        if not self.connection_service.isConnected():
            raise Exception("Not connected")

        hw_id = self.connection_service.getConnectionHardwarePN()
        target = f"{hw_id}_UNDEF"
        lui_file = self._get_LUI_file(target)

        if (
            not lui_file or lui_file.StatusCode != LoadProtocolStatusCode.ACCEPTED
        ):  # request not accepted
            return False

        self.transfer_status = TransferStatus(
            False, target, ArincTransferStep.LIST, file, 0, None
        )

        self.transfer_thread = threading.Thread(
            target=self._arinc_transfer_thread, daemon=True
        )

        return True

    # [BST-237]
    def getProgress(self) -> TransferStatus:
        status = self.transfer_status
        if status is None:
            raise Exception("Not in transfer")

        if status.transferResult is not None:
            if self.transfer_thread is not None:
                self.transfer_thread.join()
                self.transfer_thread = None
            self.transfer_status = None

        return status

    # [BST-245]
    def cancel(self):
        if self.transfer_status is None:
            self.logging_service.log("Not in transfer")
            return

        self.transfer_status.canceled = True
        self.transfer_status.transferResult = ArincTransferResult.FAILED

        if self.transfer_thread is not None:
            self.transfer_thread.join()
            self.transfer_thread = None

    def _get_LUI_file(self, target: str) -> ArincLUI | None:
        pkg = self.connection_service.receivePackage(f"{target}.{ArincFileType.LUI}")
        return _parse_LUI_file(pkg.path)

    def _put_file(self, target: str, file_path: str, file_type: ArincFileType):
        pkg = Package(f"{target}.{file_type}", file_path)
        self.connection_service.sendPackage(pkg)

    def _read_LUS_file(self, target: str) -> ArincLUS | None:
        return _parse_LUS_file(f"tmp/server/{target}.{ArincFileType.LUS}")

    def _tftp_server_thread(self):
        server = TftpServer("tmp/server/", self._server_callback)
        server.listen()

    def _arinc_transfer_thread(self):
        while self.transfer_status and not self.transfer_status.canceled:
            # periodically check for status
            lus_file = self._read_LUS_file(self.transfer_status.currentTarget)

            match lus_file:
                case "0001":
                    if ArincTransferStep.LIST:
                        image_filename = self.transfer_status.fileRecord.file.fileName
                        target = self.transfer_status.currentTarget

                        lur_file = ArincLUR(
                            [
                                ArincLURHeaderFile(
                                    f"{image_filename}.{ArincFileType.LUH}",
                                    image_filename,
                                )
                            ]
                        )
                        file_path = _encode_LUR_file(target, lur_file)
                        self._put_file(target, file_path, ArincFileType.LUR)

                        self.transfer_status.transferStep = ArincTransferStep.TRANFER
                        self.transfer_status.progressPercent = 20

                case "0002" | "0004":
                    if self.transfer_status.progressPercent < 40:
                        self.transfer_status.progressPercent = 40

                case "0003":
                    self.transfer_status.transferStep = (
                        ArincTransferStep.NOT_IN_TRANSFER
                    )
                    self.transfer_status.progressPercent = 100
                    self.transfer_status.transferResult = ArincTransferResult.SUCCESS

                case "1003" | "1004" | "1005":  # operation aborted
                    self.transfer_status.canceled = True
                    self.transfer_status.transferStep = (
                        ArincTransferStep.NOT_IN_TRANSFER
                    )
                    self.transfer_status.progressPercent = 100
                    self.transfer_status.transferResult = ArincTransferResult.FAILED

                case "1007":  # operation failed
                    self.transfer_status.transferStep = (
                        ArincTransferStep.NOT_IN_TRANSFER
                    )
                    self.transfer_status.progressPercent = 100
                    self.transfer_status.transferResult = ArincTransferResult.FAILED

            time.sleep(0.1)

    def _server_callback(self, filename: str, **args):
        if self.transfer_status is None:
            return None

        target = self.transfer_status.currentTarget

        if self.transfer_status.canceled:
            # return canceled status file
            return None

        if filename == self.transfer_status.fileRecord.file.fileName:
            return open(self.transfer_status.fileRecord.file.path, "rb")

        if filename == f"{target}.{ArincFileType.LUH}":
            file_record = self.transfer_status.fileRecord
            luh_file = ArincLUH(
                file_record.dataHash,
                file_record.softwarePN,
                file_record.hardwarePN,
                file_record.sizeBytes,
            )
            file_path = _encode_LUH_file(target, luh_file)
            return open(file_path, "rb")

        return None


def _parse_LUS_file(file_path: str) -> ArincLUS | None:
    try:
        with open(file_path, "rb") as file:
            file_lenght = int.from_bytes(file.read(4), "big", signed=False)
            protocol_version = file.read(2).decode("ascii")
            status_code = LoadProtocolStatusCode(file.read(2).hex())
            status_description_lenght = int.from_bytes(
                file.read(2), "big", signed=False
            )

            status_description = None
            if status_description_lenght > 0:
                status_description = file.read(status_description_lenght).decode(
                    "ascii"
                )[:-1]

            counter = int.from_bytes(file.read(2), "big", signed=False)
            exception_timer = int.from_bytes(file.read(2), "big", signed=False)
            estimation_time = int.from_bytes(file.read(2), "big", signed=False)
            load_list_ratio = int(file.read(3).decode("ascii"))
            number_of_header_files = int.from_bytes(file.read(2), "big", signed=False)

            header_files = []
            header_files = header_files
            for _ in range(number_of_header_files):
                header_file_name_lenght = int.from_bytes(
                    file.read(1), "big", signed=False
                )
                header_file_name = file.read(header_file_name_lenght).decode("ascii")[
                    :-1
                ]

                load_part_number_name_lenght = int.from_bytes(
                    file.read(1), "big", signed=False
                )
                load_part_number_name = file.read(load_part_number_name_lenght).decode(
                    "ascii"
                )[:-1]

                load_ratio = int(file.read(3).decode("ascii"))
                load_status = LoadProtocolStatusCode(file.read(4).hex())

                load_status_description_lenght = int.from_bytes(
                    file.read(2), "big", signed=False
                )
                load_status_description = None
                if load_status_description_lenght > 0:
                    load_status_description = file.read(
                        load_status_description_lenght
                    ).decode("ascii")[:-1]

                header_files.append(
                    ArincLUSHeaderFile(
                        header_file_name,
                        load_part_number_name,
                        load_ratio,
                        load_status,
                        load_status_description,
                    )
                )

            return ArincLUS(
                status_code,
                status_description,
                counter,
                exception_timer,
                estimation_time,
                load_list_ratio,
                header_files,
            )
    except:
        return None


def _parse_LUI_file(file_path: str) -> ArincLUI | None:
    try:
        with open(file_path, "rb") as file:
            file_lenght = int.from_bytes(file.read(4), "big", signed=False)
            protocol_version = file.read(2).decode("ascii")
            status_code = LoadProtocolStatusCode(file.read(2).hex())
            status_description_lenght = int.from_bytes(
                file.read(2), "big", signed=False
            )
            status_description = None
            if status_description_lenght > 0:
                status_description = file.read(-1).decode("ascii")[:-1]

            return ArincLUI(status_code, status_description)
    except:
        return None


def _encode_LUR_file(target: str, lur_file: ArincLUR) -> str:
    file_path = f"tmp/server/{target}.{ArincFileType.LUR}"

    if os.path.exists(file_path):
        os.unlink(file_path)

    with open(file_path, "xb") as file:
        bytes_to_write = bytearray(version, "ascii")

        bytes_to_write.extend(
            len(lur_file.HeaderFiles).to_bytes(2, "big", signed=False)
        )

        for hf in lur_file.HeaderFiles:
            bytes_to_write.extend(
                (len(hf.FileName) + 1).to_bytes(1, "big", signed=False)
            )
            bytes_to_write.extend(hf.FileName.encode("ascii"))
            bytes_to_write.extend(b"\0")

            bytes_to_write.extend(
                (len(hf.PartNumberName) + 1).to_bytes(1, "big", signed=False)
            )
            bytes_to_write.extend(hf.PartNumberName.encode("ascii"))
            bytes_to_write.extend(b"\0")

        file.write((32 + len(bytes_to_write) * 8).to_bytes(4, "big", signed=False))
        file.write(bytes_to_write)

    return file_path


def _encode_LUH_file(target: str, luh_file: ArincLUH) -> str:
    file_path = f"tmp/server/{target}.{ArincFileType.LUH}"

    if os.path.exists(file_path):
        os.unlink(file_path)

    with open(file_path, "xb") as file:
        bytes_to_write = bytearray(version, "ascii")

        bytes_to_write.extend((luh_file.Size * 8).to_bytes(4, "big", signed=False))

        bytes_to_write.extend(
            (len(luh_file.SoftwarePartNumber) + 1).to_bytes(1, "big", signed=False)
        )
        bytes_to_write.extend(luh_file.SoftwarePartNumber.encode("ascii"))
        bytes_to_write.extend(b"\0")

        bytes_to_write.extend(
            (len(luh_file.HardwarePartNumber) + 1).to_bytes(1, "big", signed=False)
        )
        bytes_to_write.extend(luh_file.HardwarePartNumber.encode("ascii"))
        bytes_to_write.extend(b"\0")

        bytes_to_write.extend(
            (len(luh_file.DataHash) + 1).to_bytes(1, "big", signed=False)
        )
        bytes_to_write.extend(luh_file.DataHash.encode("ascii"))
        bytes_to_write.extend(b"\0")

        file.write((32 + len(bytes_to_write) * 8).to_bytes(4, "big", signed=False))
        file.write(bytes_to_write)

    return file_path
