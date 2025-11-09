import hashlib
from typing import Dict

from data.classes import File
from services.logging_service import LoggingService

class FileValidatorService:
    def __init__(self):
        self.logging_service = LoggingService(FileValidatorService.__name__)

    def _read_header(self, file: File) -> Dict[str, str]:
        with open(file.path, 'rb') as f:
            # Ler somente o Header do arquivo
            header = f.read(40)
            
            # Extrair somente o Software PN
            sw_pn_bytes = header[0:20]
            sw_pn = sw_pn_bytes.rstrip(b'\x00').decode('ascii')
            
            # Extrair somente o Hardware PN
            hw_pn_bytes = header[20:40]
            hw_pn = hw_pn_bytes.rstrip(b'\x00').decode('ascii')
            
        return {"sw_pn": sw_pn, "hw_pn": hw_pn}
    
    def _read_data_and_trailing(self, file: File) -> str:
        with open(file.path, 'rb') as f:
            # Lê o arquivo inteiro
            file_content = f.read()

            # Extrai somente a parte dos dados, excluindo o Header e o SHA-256 hash
            data = file_content[40:-32]   

            # Extrai somente o SHA-256 hash
            trailing = file_content[-32:].hex()
            
        return data, trailing

    def checkIdentification(self, file: File) -> bool:
        try:
            header = self._read_header(file)
            sw_pn = header.get("sw_pn")
            hw_pn = header.get("hw_pn")

            # [BST-269]
            is_valid = sw_pn is not None and sw_pn != ""

            # [BST-280]
            self.logging_service.log(
                f"checkIdentification result for {file.fileName}: {is_valid}"
            )

            # [BST-269]
            return sw_pn, hw_pn, is_valid

        except Exception as e:
            self.logging_service.error(
                f"File read error during checkIdentification for {file.fileName}", e
            )
            return None, None, False

    def checkIntegrity(self, file: File) -> bool:
        try:
            # [BST-271, BST-272]
            data_section, extracted_hash = self._read_data_and_trailing(file)
            calculated_hash = hashlib.sha256(data_section).hexdigest()

            # [BST-274]
            is_valid = calculated_hash == extracted_hash

            # [BST-280]
            self.logging_service.log(
                f"checkIntegrity result for {file.fileName}: {is_valid}"
            )

            # [BST-274]
            return data_section, extracted_hash, is_valid

        except Exception as e:
            self.logging_service.error(
                f"File read error during checkIntegrity for {file.fileName}", e
            )
            return None, None, False

    def checkCompatibility(self, file: File, hardwarePN: str) -> bool:
        try:
            # [BST-276]
            header = self._read_header(file)
            extracted_hw_pn = header.get("hardwarePN")

            # [BST-278]
            is_valid = extracted_hw_pn == hardwarePN

            # [BST-280]
            self.logging_service.log(
                f"checkCompatibility result for {file.fileName} (Target: {hardwarePN}): {is_valid}"
            )

            # [BST-278]
            return is_valid

        except Exception as e:
            # [BST-281]
            self.logging_service.error(
                f"File read error during checkCompatibility for {file.fileName}", e
            )
            return False
