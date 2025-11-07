import threading
import time

from typing import Literal
from data.classes import File, Package, TransferStatus

from data.enums import ArincFileType, ArincTransferStep
from services.connection_service import ConnectionService
from services.logging_service import LoggingService
from tftpy import TftpServer

version:  Literal['A4'] = 'A4'

def _default_transfer_status():
    return TransferStatus(False, False, 0, None, ArincTransferStep.NOT_IN_TRANSFER, None)

class ArincModule:
    transfer_status: TransferStatus = _default_transfer_status()
    transfer_thread: threading.Thread | None = None

    def __init__(self, connection_service: ConnectionService):
        self.logging_service = LoggingService(ConnectionService.__name__)
        self.connection_service = connection_service
        self.tftp_server_thread = threading.Thread(target=self._tftp_server_thread, daemon=True)
        self.tftp_server_thread.start()

    # [BST-235]
    def startTransfer(self, file: File) -> bool:
        if(not self.connection_service.isConnected()):
            raise Exception("Not connected")

        hw_id = self.connection_service.getConnectionHardwarePN()
        target = f'{hw_id}_UNDEF'
        upload_initialization = self._get_file(target, ArincFileType.LUI)

        if(upload_initialization['acceptanceStatusCode'] != '0001'): #request not accepted
            return False

        self.transfer_status = TransferStatus(True, False, 0, target, ArincTransferStep.LIST, file)

        self._write_file_to_store(file)

        self.tftp_server_thread = threading.Thread(target=self._arinc_transfer_thread, daemon=True)

        return True
    
    # [BST-237]
    def getProgress(self) -> TransferStatus:
        status = self.transfer_status
        
        if(status.progressPercent == 100):
            if(self.transfer_thread is not None):
                self.transfer_thread.join()
                self.transfer_thread = None
            self.transfer_status = _default_transfer_status()

        return status
    
    # [BST-245]
    def cancel(self):
        if(not self.transfer_status.inTransfer):
            self.logging_service.log("Not in transfer")
            return
        
        self.transfer_status.canceled = True
        self.transfer_status.inTransfer = False

        if(self.transfer_thread is not None):
            self.transfer_thread.join()
            self.transfer_thread = None
    
    def _get_file(self, target: str, file_type: ArincFileType) -> dict:
        pkg = self.connection_service.receivePackage(f'{target}.{file_type}')
        return self._parse_file(pkg.path, file_type)
    
    def _put_file(self, target: str, file_type: ArincFileType, contents: dict):
        file_path = self._encode_file(contents, file_type)
        pgk = Package(f'{target}.{file_type}', file_path)
        self.connection_service.sendPackage(pgk)

    def _read_file_in_store(self, target: str, file_type: ArincFileType) -> dict:
        return self._parse_file(f'tmp/server/{target}.{file_type}', file_type)
    def _write_file_to_store(self, file: File):
        pass
    
    def _parse_file(self, file_path: str, file_type: ArincFileType) -> dict:
        return {}
    def _encode_file(self, contents: dict, file_type: ArincFileType) -> str:
        return ''
    
    def _tftp_server_thread(self):
        server = TftpServer("tmp/server/", self._server_callback)
        server.listen()

    def _arinc_transfer_thread(self):
        while self.transfer_status.inTransfer:
            if self.transfer_status.currentTarget is not None:
                #periodically check for status
                status = self._read_file_in_store(self.transfer_status.currentTarget, ArincFileType.LUS)

                match status['StatusCode']:
                    case '0001':
                        if (ArincTransferStep.LIST):
                            self._put_file(self.transfer_status.currentTarget, ArincFileType.LUI, {})
                            self.transfer_status.transferStep = ArincTransferStep.TRANFER
                            self.transfer_status.progressPercent = 20

                    case '0002' | '0004':
                        if (self.transfer_status.progressPercent < 40):
                            self.transfer_status.progressPercent = 40

                    case '0003':
                        self.transfer_status.inTransfer = False
                        self.transfer_status.transferStep = ArincTransferStep.NOT_IN_TRANSFER
                        self.transfer_status.progressPercent = 100

                    # case '':

            time.sleep(0.1)
    
    def _server_callback(self, filename: str, **args):
        if(self.transfer_status.currentTarget is not None and self.transfer_status.canceled):
            # return canceled status file
            return None

        if(not self.transfer_status.inTransfer):
            return None
        
        target = self.transfer_status.currentTarget
        
        if(filename == f'{target}.LUH'):
            file_path = self._encode_file({}, ArincFileType.LUH)
            return open(file_path)
        
        return None
