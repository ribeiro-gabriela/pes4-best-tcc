import hashlib
from typing import Dict

from data.classes import File
from services.logging_service import LoggingService

class FileValidatorService:
    def __init__(self):
        self.logging_service = LoggingService(FileValidatorService.__name__)

    # --- Métodos de Simulação de Leitura de Seção (Mock) ---
    # (Estes métodos simulam a leitura de seções 'HEADER', 'DATA' e 'TRAILING'
    # de um formato de arquivo binário proprietário, conforme inferido
    # pelos requisitos)

    def _read_header(self, file: File) -> Dict[str, str]:
        """
        Mock: Simula a leitura da seção 'HEADER'.
        Lança IOError se o arquivo contiver 'read_error'.
        """
        if "read_error" in file.fileName:
            raise IOError(f"Simulated read error for {file.fileName}")

        # [BST-269]
        if "invalid_sw_pn" in file.fileName:
            # (Simula um cabeçalho sem SW PN válido)
            return {"hardwarePN": "HW123"}

        # [BST-276]
        if "mismatch_hw" in file.fileName:
            # (Simula um cabeçalho com HW PN diferente)
            return {"softwarePN": "SW-VALID", "hardwarePN": "HW_WRONG"}

        # (Simula um cabeçalho válido)
        return {"softwarePN": "SW-VALID", "hardwarePN": "HW123"}

    def _read_data(self, file: File) -> bytes:
        """
        Mock: Simula a leitura da seção 'DATA'.
        Lança IOError se o arquivo contiver 'read_error'.
        """
        if "read_error" in file.fileName:
            raise IOError(f"Simulated read error for {file.fileName}")

        # [BST-272]
        if "invalid_hash" in file.fileName:
            return b"data_payload_that_will_fail_hash_check"

        return b"valid_data_payload_content"

    def _read_trailing(self, file: File) -> str:
        """
        Mock: Simula a leitura da seção 'TRAILING' (Hash).
        Lança IOError se o arquivo contiver 'read_error'.
        """
        if "read_error" in file.fileName:
            raise IOError(f"Simulated read error for {file.fileName}")

        # [BST-271]
        if "invalid_hash" in file.fileName:
            return "wrong_hash_value_abc123"

        # (Retorna o hash correto para 'valid_data_payload_content')
        return hashlib.sha256(b"valid_data_payload_content").hexdigest()

    # --- Métodos de Verificação ---

    def checkIdentification(self, file: File) -> bool:
        try:
            header = self._read_header(file)

            # [BST-269]
            # (Verifica se a chave 'softwarePN' existe e tem um valor)
            sw_pn = header.get("softwarePN")
            is_valid = sw_pn is not None and sw_pn != ""

            # [BST-280]
            self.logging_service.log(
                f"checkIdentification result for {file.fileName}: {is_valid}"
            )

            # [BST-269]
            return is_valid

        except Exception as e:
            # [BST-281]
            self.logging_service.error(
                f"File read error during checkIdentification for {file.fileName}", e
            )
            # [BST-281]
            return False

    def checkIntegrity(self, file: File) -> bool:
        try:
            # [BST-271]
            extracted_hash = self._read_trailing(file)

            # [BST-272]
            data_section = self._read_data(file)
            calculated_hash = hashlib.sha256(data_section).hexdigest()

            # [BST-274]
            is_valid = calculated_hash == extracted_hash

            # [BST-280]
            self.logging_service.log(
                f"checkIntegrity result for {file.fileName}: {is_valid}"
            )

            # [BST-274]
            return is_valid

        except Exception as e:
            # [BST-281]
            self.logging_service.error(
                f"File read error during checkIntegrity for {file.fileName}", e
            )
            # [BST-281]
            return False

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
            # [BST-281]
            return False
