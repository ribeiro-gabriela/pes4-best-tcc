import os
import shutil
import glob
from datetime import datetime
from typing import List

from data.classes import File, FileRecord
from data.errors import DuplicateFileError, FileAccessError, IdentificationError, IntegrityError
from services.file_validator_service import FileValidatorService
from services.logging_service import LoggingService


class ImportedFilesService:
    
    def __init__(self, file_validator: FileValidatorService, storage_path: str):
        self.logging_service = LoggingService(ImportedFilesService.__name__)
        self.file_validator = file_validator
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def _parse_txt_file(self, txt_path: str) -> FileRecord:
        """
        Helper para ler um arquivo .txt de metadados e convertê-lo em um FileRecord.
        """
        props = {}
        with open(txt_path, 'r') as f:
            for line in f:
                key, value = line.strip().split('=', 1)
                props[key] = value
        
        sw_pn = props['softwarePN']
        bin_path = os.path.join(self.storage_path, f"{sw_pn}.bin")
        
        file_obj = File(path=bin_path, fileName=f"{sw_pn}.bin")
        
        return FileRecord(
            file=file_obj,
            softwarePN=sw_pn,
            hardwarePN=props['hardwarePN'],
            dataHash=props['dataHash'],
            importedAt=datetime.fromisoformat(props['importedAt']),
            sizeBytes=int(props['sizeBytes'])
        )

    # [BST-250]
    def list(self) -> List[FileRecord]:
        records = []
        # [BST-250]
        search_pattern = os.path.join(self.storage_path, "*.txt")
        for txt_path in glob.glob(search_pattern):
            try:
                records.append(self._parse_txt_file(txt_path))
            except Exception as e:
                self.logging_service.error(f"Failed to parse metadata file {txt_path}", e)
        return records

    # [BST-254]
    def listFiltered(self, hardwarePN: str) -> List[FileRecord]:
        records = []
        # [BST-254]
        search_pattern = os.path.join(self.storage_path, f"*-{hardwarePN}.txt")
        for txt_path in glob.glob(search_pattern):
            try:
                records.append(self._parse_txt_file(txt_path))
            except Exception as e:
                self.logging_service.error(f"Failed to parse metadata file {txt_path}", e)
        return records

    # [BST-256]
    def get(self, softwarePN: str) -> FileRecord:
        # [BST-256]
        search_pattern = os.path.join(self.storage_path, f"{softwarePN}-*.txt")
        found_files = glob.glob(search_pattern)
        
        if found_files:
            raise FileAccessError("File not found")
        
        try:
            # [BST-256]
            return self._parse_txt_file(found_files[0])
        except Exception as e:
            error = FileAccessError("Failed to parse metadata", e)
            self.logging_service.error(f"Failed to parse metadata file {found_files[0]}", error)
            raise error

    # [BST-255]
    def delete(self, softwarePN: str) -> None:
        try:
            # [BST-255]
            search_pattern = os.path.join(self.storage_path, f"{softwarePN}*")
            files_to_delete = glob.glob(search_pattern)
            
            if not files_to_delete:
                # [BST-257]
                self.logging_service.log(f"Delete operation: No files found for SW_PN {softwarePN}.")
                return

            for f_path in files_to_delete:
                os.remove(f_path)
            
            # [BST-257]
            self.logging_service.log(f"Delete operation successful for SW_PN {softwarePN}. {len(files_to_delete)} files removed.")

        except Exception as e:
            # [BST-257]
            self.logging_service.error(f"Delete operation failed for SW_PN {softwarePN}", e)

    def importFile(self, file: File) -> FileRecord:
        # [BST-251]
        if not self.file_validator.checkIdentification(file):
            # [BST-257]
            msg = f"Import failed: Identification check failed for {file.fileName}"
            err = IdentificationError(msg)
            self.logging_service.error(msg, err)
            # [BST-252]
            raise err

        # [BST-259]
        if not self.file_validator.checkIntegrity(file):
            # [BST-257]
            msg = f"Import failed: Integrity check failed for {file.fileName}"
            err = IntegrityError(msg)
            self.logging_service.error(msg, err)
            # [BST-260]
            raise err

        # (Assumindo que os PNs e hash são extraídos após validação)
        sw_pn = self.file_validator.get_software_pn(file)
        hw_pn = self.file_validator.get_hardware_pn(file)
        data_hash = self.file_validator.get_hash(file)
        size_bytes = os.path.getsize(file.path)
        
        # [BST-253]
        bin_path = os.path.join(self.storage_path, f"{sw_pn}.bin")
        # [BST-253]
        txt_path = os.path.join(self.storage_path, f"{sw_pn}-{hw_pn}.txt")

        # [BST-258]
        if os.path.exists(bin_path) or os.path.exists(txt_path):
            msg = f"Import failed: File with SW_PN {sw_pn} already exists."
            err = DuplicateFileError(msg)
            # [BST-257]
            self.logging_service.error(msg, err)
            # [BST-258]
            raise err

        try:
            # [BST-253]
            shutil.copy(file.path, bin_path)
            
            imported_at = datetime.now()
            
            # [BST-253]
            metadata_content = (
                f"softwarePN={sw_pn}\n"
                f"hardwarePN={hw_pn}\n"
                f"dataHash={data_hash}\n"
                f"importedAt={imported_at.isoformat()}\n"
                f"sizeBytes={size_bytes}\n"
                f"original_filename={file.fileName}\n"
            )
            with open(txt_path, 'w') as f:
                f.write(metadata_content)

            # [BST-267]
            created_bin_file = File(path=bin_path, fileName=os.path.basename(bin_path))
            if not self.file_validator.checkIntegrity(created_bin_file):
                # [BST-249]
                os.remove(bin_path)
                os.remove(txt_path)
                # [BST-257]
                msg = f"Import failed: Integrity check failed for *created* file {bin_path}"
                err = IntegrityError(msg)
                self.logging_service.error(msg, err)
                # [BST-248]
                raise err
            
            # [BST-257]
            self.logging_service.log(f"Import successful: {file.fileName} imported as {sw_pn}.bin")

            new_file_obj = File(path=bin_path, fileName=os.path.basename(bin_path))
            
            return FileRecord(
                file=new_file_obj,
                softwarePN=sw_pn,
                hardwarePN=hw_pn,
                dataHash=data_hash,
                importedAt=imported_at,
                sizeBytes=size_bytes
            )

        except Exception as e:
            # [BST-257]
            # (Log genérico de falha caso algo inesperado ocorra)
            if not isinstance(e, (IntegrityError, IdentificationError, DuplicateFileError)):
                self.logging_service.error(f"Import failed during file operation for {file.fileName}", e)
            
            # (Limpeza em caso de falha durante a cópia ou escrita)
            if os.path.exists(bin_path):
                os.remove(bin_path)
            if os.path.exists(txt_path):
                os.remove(txt_path)
                
            raise e