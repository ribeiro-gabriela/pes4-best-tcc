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

    def __init__(self, connection_service: ConnectionService, base_path: str):
        self.logging_service = LoggingService(ConnectionService.__name__)
        self.connection_service = connection_service

        self._SERVER_PATH = base_path+"/tftp/server"
        self._CLIENT_PATH = base_path+"/tftp/client"

        if not os.path.exists(self._SERVER_PATH):
            os.makedirs(self._SERVER_PATH)
        if not os.path.exists(self._CLIENT_PATH):
            os.makedirs(self._CLIENT_PATH)
        
        self.tftp_server_thread = threading.Thread(
            target=self._tftp_server_thread, daemon=True
        )
        self.tftp_server_thread.start()

    # [BST-235]
    def startTransfer(self, file: FileRecord) -> bool:
        if not self.connection_service.isConnected():
            raise Exception("Not connected")

        self._create_file_with_data(file)

        hw_id = self.connection_service.getConnectionHardwarePN()
        target = f"{hw_id}_UNDEF"
        lui_file = None
        try:
            lui_file = self._get_LUI_file(target)
        except Exception as e:
            print(e)
            return False

        # if (
        #     not lui_file or lui_file.StatusCode != LoadProtocolStatusCode.ACCEPTED
        # ):  # request not accepted
        #     return False

        self.transfer_status = TransferStatus(
            False, target, ArincTransferStep.LIST, file, 0, None
        )

        self.transfer_thread = threading.Thread(
            target=self._arinc_transfer_thread, daemon=True
        )

        self.transfer_thread.start()

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

        self.transfer_status.cancelled = True
        self.transfer_status.transferResult = ArincTransferResult.FAILED

        if self.transfer_thread is not None:
            self.transfer_thread.join()
            self.transfer_thread = None

    def _get_LUI_file(self, target: str) -> ArincLUI | None:
        pkg = self.connection_service.receivePackage(f"{target}.{ArincFileType.LUI.value}")
        return self._parse_LUI_file(pkg.path)

    def _put_file(self, target: str, file_path: str, file_type: ArincFileType):
        pkg = Package(f"{target}.{file_type.value}", file_path)
        self.connection_service.sendPackage(pkg)

    def _read_LUS_file(self, target: str) -> ArincLUS | None:
        return self._parse_LUS_file(f"{self._SERVER_PATH}/{target}.{ArincFileType.LUS.value}")

    def _tftp_server_thread(self):
        server = TftpServer(f"{self._SERVER_PATH}/", self._server_callback)
        server.listen()

    def _arinc_transfer_thread(self):
        if self.transfer_status and not self.transfer_status.cancelled and self.transfer_status.transferStep == ArincTransferStep.LIST:
            software_pn = self.transfer_status.fileRecord.softwarePN
            target = self.transfer_status.currentTarget

            lur_file = ArincLUR(
                [
                    ArincLURHeaderFile(
                        f"{software_pn}.{ArincFileType.LUH.value}",
                        f"{software_pn}.bin",
                    )
                ]
            )
            file_path = self._encode_LUR_file(target, lur_file)
            self._put_file(target, file_path, ArincFileType.LUR)

            self.transfer_status.transferStep = ArincTransferStep.TRANFER
            self.transfer_status.progressPercent = 20


        while self.transfer_status and not self.transfer_status.cancelled:
            # periodically check for status
            lus_file = self._read_LUS_file(self.transfer_status.currentTarget)

            if lus_file:
                match lus_file.StatusCode:
                    case "0001":
                        if self.transfer_status.transferStep == ArincTransferStep.LIST:
                            software_pn = self.transfer_status.fileRecord.softwarePN
                            target = self.transfer_status.currentTarget

                            lur_file = ArincLUR(
                                [
                                    ArincLURHeaderFile(
                                        f"{software_pn}.{ArincFileType.LUH.value}",
                                        f"{software_pn}.bin",
                                    )
                                ]
                            )
                            file_path = self._encode_LUR_file(target, lur_file)
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
                        self.transfer_status.cancelled = True
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

        if self.transfer_status.cancelled:
            # return canceled status file
            return None

        # if filename == self.transfer_status.fileRecord.file.fileName:
        #     return open(self.transfer_status.fileRecord.file.path, "rb")

        if filename == f"{target}.{ArincFileType.LUH.value}":
            file_record = self.transfer_status.fileRecord
            luh_file = ArincLUH(
                file_record.softwarePN,
                file_record.hardwarePN,
                file_record.dataHash,
            )
            file_path = self._encode_LUH_file(target, luh_file)
            return open(file_path, "rb")

        return None


    def _parse_LUS_file(self, file_path: str) -> ArincLUS | None:
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


    def _parse_LUI_file(self, file_path: str) -> ArincLUI | None:
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
        except Exception as e:
            print(e)
            return None


    def _encode_LUR_file(self, target: str, lur_file: ArincLUR) -> str:
        file_path = f"{self._SERVER_PATH}/{target}.{ArincFileType.LUR.value}"

        with open(file_path, "wb") as file:
            bytes_to_write = bytearray(version.encode("ascii"))

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


    def _encode_LUH_file(self, target: str, luh_file: ArincLUH) -> str:
        file_path = f"{self._SERVER_PATH}/{target}.{ArincFileType.LUH.value}"

        with open(file_path, "wb") as file:
            bytes_to_write = bytearray(version.encode("ascii"))

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


    def _create_file_with_data(self, file: FileRecord):
        data_output_path = f"{self._SERVER_PATH}/{file.softwarePN}.bin"
        image_input_path = file.file.path

        HEADER_SIZE = 40
        FOOTER_SIZE = 32
        
        with open(image_input_path, 'rb') as image_file:
            # image_file.seek(0, 2)
            # total_size = image_file.tell()
            
            # bytes_to_copy = total_size - HEADER_SIZE - FOOTER_SIZE

            # if bytes_to_copy <= 0:
            #     raise Exception("Malformed sofware image file")

            # image_file.seek(HEADER_SIZE)
            # data_to_copy = image_file.read(bytes_to_copy)
            data_to_copy = image_file.read(-1)

        with open(data_output_path, 'wb') as data_file:
            data_file.write(data_to_copy)

