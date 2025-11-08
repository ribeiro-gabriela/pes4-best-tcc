import threading
import time
import os

from typing import Literal
from data.classes import File, FileRecord, Package, TransferStatus

from data.enums import ArincFileType, ArincTransferResult, ArincTransferStep
from services.connection_service import ConnectionService
from services.logging_service import LoggingService
from tftpy import TftpServer

version:  Literal['A4'] = 'A4'

class ArincModule:
    transfer_status: TransferStatus | None = None
    transfer_thread: threading.Thread | None = None

    def __init__(self, connection_service: ConnectionService):
        self.logging_service = LoggingService(ConnectionService.__name__)
        self.connection_service = connection_service
        self.tftp_server_thread = threading.Thread(target=self._tftp_server_thread, daemon=True)
        self.tftp_server_thread.start()

    # [BST-235]
    def startTransfer(self, file: FileRecord) -> bool:
        if(not self.connection_service.isConnected()):
            raise Exception("Not connected")

        hw_id = self.connection_service.getConnectionHardwarePN()
        target = f'{hw_id}_UNDEF'
        upload_initialization = self._get_file(target, ArincFileType.LUI)

        if(upload_initialization['acceptanceStatusCode'] != '0001'): #request not accepted
            return False

        self.transfer_status = TransferStatus(False, target, ArincTransferStep.LIST, file, 0, None)

        self.transfer_thread = threading.Thread(target=self._arinc_transfer_thread, daemon=True)

        return True
    
    # [BST-237]
    def getProgress(self) -> TransferStatus:
        status = self.transfer_status
        if status is None:
            raise Exception('Not in transfer')


        if status.transferResult is not None:
            if(self.transfer_thread is not None):
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

        if(self.transfer_thread is not None):
            self.transfer_thread.join()
            self.transfer_thread = None
    
    def _get_file(self, target: str, file_type: ArincFileType) -> dict:
        pkg = self.connection_service.receivePackage(f'{target}.{file_type}')
        return self._parse_file(pkg.path, file_type)
    
    def _put_file(self, target: str, file_type: ArincFileType, contents: dict):
        file_path = self._encode_file(target, contents, file_type)
        pgk = Package(f'{target}.{file_type}', file_path)
        self.connection_service.sendPackage(pgk)

    def _read_file_in_store(self, target: str, file_type: ArincFileType) -> dict:
        return self._parse_file(f'tmp/server/{target}.{file_type}', file_type)
    
    def _parse_file(self, file_path: str, file_type: ArincFileType) -> dict:
        return _parse_arinc_file(file_path, file_type)
    def _encode_file(self, target: str, contents: dict, file_type: ArincFileType) -> str:
        return _encode_arinc_file(target, contents, file_type)
    
    def _tftp_server_thread(self):
        server = TftpServer("tmp/server/", self._server_callback)
        server.listen()

    def _arinc_transfer_thread(self):
        while self.transfer_status and not self.transfer_status.canceled:
            #periodically check for status
            status = self._read_file_in_store(self.transfer_status.currentTarget, ArincFileType.LUS)

            match status['StatusCode']:
                case '0001':
                    if (ArincTransferStep.LIST):
                        image_filename = self.transfer_status.fileRecord.file.fileName
                        contents = {
                            'ProtocolVersion': version,
                            'NumberOfHeaderFiles':1,
                            'HeaderFiles': [{
                                'HeaderFileName':f'{image_filename}.{ArincFileType.LUH}',
                                'LoadPartNumberName':f'{image_filename}.{ArincFileType.LUH}',
                            }]
                        }
                        self._put_file(self.transfer_status.currentTarget, ArincFileType.LUR, contents)
                        self.transfer_status.transferStep = ArincTransferStep.TRANFER
                        self.transfer_status.progressPercent = 20

                case '0002' | '0004':
                    if (self.transfer_status.progressPercent < 40):
                        self.transfer_status.progressPercent = 40

                case '0003':
                    self.transfer_status.transferStep = ArincTransferStep.NOT_IN_TRANSFER
                    self.transfer_status.progressPercent = 100
                    self.transfer_status.transferResult = ArincTransferResult.SUCCESS

                case '1003'|'1004'|'1005': #operation aborted
                    self.transfer_status.canceled = True
                    self.transfer_status.transferStep = ArincTransferStep.NOT_IN_TRANSFER
                    self.transfer_status.progressPercent = 100
                    self.transfer_status.transferResult = ArincTransferResult.FAILED

                case '1007': #operation failed
                    self.transfer_status.transferStep = ArincTransferStep.NOT_IN_TRANSFER
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
            return open(self.transfer_status.fileRecord.file.path, 'r')
        
        if filename == f'{target}.{ArincFileType.LUH}':
            contents = {}
            file_path = self._encode_file(target, contents, ArincFileType.LUH)
            return open(file_path, 'r')
        
        return None

def _parse_arinc_file(file_path: str, file_type: ArincFileType):
    with open(file_path, 'r') as file:
        match file_type:
            case ArincFileType.LUI:
                pass
            case ArincFileType.LUS:
                pass

        return {}

def _encode_arinc_file(target: str, contents: dict, file_type: ArincFileType):
    file_path = f"tmp/server/{target}.{file_type}"

    with open(file_path,'x') as file:
        match file_type:
            case ArincFileType.LUR:
                pass
            case ArincFileType.LUH:
                pass

    return file_path