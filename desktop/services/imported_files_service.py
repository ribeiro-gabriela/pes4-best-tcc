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

    def list(self) -> List[FileRecord]:
        records = []
        # [BST-250]
        search_pattern = os.path.join(self.storage_path, "*.txt")
        for txt_path in glob.glob(search_pattern):
            records.append(self._parse_txt_file(txt_path))
        return records

    def listFiltered(self, hardwarePN: str) -> List[FileRecord]:
        records = []
        # [BST-254]
        search_pattern = os.path.join(self.storage_path, f"*-{hardwarePN}.txt")
        for txt_path in glob.glob(search_pattern):
            records.append(self._parse_txt_file(txt_path))
        return records

    def get(self, softwarePN: str) -> FileRecord:
        # [BST-256]
        search_pattern = os.path.join(self.storage_path, f"{softwarePN}-*.txt")
        found_files = glob.glob(search_pattern)
        
        txt_path = found_files[0]
        
        file_record = self._parse_txt_file(txt_path)
        self.logging_service.log(f"File retrieved successfully: SW_PN {softwarePN}")

        return file_record
    
    def delete(self, softwarePN: str) -> None:
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

    def importFile(self, file: File) -> FileRecord:
        # [BST-251]
        sw_pn, hw_pn, is_identified = self.file_validator.checkIdentification(file)
        if not is_identified:
            # [BST-257]
            msg = f"Import failed: Identification check failed for {file.fileName}"
            err = IdentificationError(msg)
            self.logging_service.error(msg, err)
            # [BST-252]
            raise err

        # [BST-259]
        data_section, extracted_hash, is_integrity_valid = self.file_validator.checkIntegrity(file)
        if not is_integrity_valid:
            # [BST-257]
            msg = f"Import failed: Integrity check failed for {file.fileName}"
            err = IntegrityError(msg)
            self.logging_service.error(msg, err)
            # [BST-260]
            raise err
        size_bytes = len(data_section)

        # [BST-253]
        bin_path = os.path.join(self.storage_path, f"{sw_pn}.bin")
        txt_path = os.path.join(self.storage_path, f"{sw_pn}-{hw_pn}.txt")

        # [BST-258]
        if os.path.exists(bin_path) or os.path.exists(txt_path):
            msg = f"Import failed: File with SW_PN {sw_pn} already exists."
            err = DuplicateFileError(msg)
            # [BST-257]
            self.logging_service.error(msg, err)
            # [BST-612]
            raise err

        # [BST-253]
        shutil.copy(file.path, bin_path)
        
        imported_at = datetime.now()
        
        metadata_content = (
            f"softwarePN={sw_pn}\n"
            f"hardwarePN={hw_pn}\n"
            f"dataHash={extracted_hash}\n"
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
            msg = f"Import failed: Integrity check failed for created file {bin_path}"
            err = IntegrityError(msg)
            self.logging_service.error(msg, err)
            # [BST-248]
            raise err
        
        # [BST-257]
        self.logging_service.log(f"Import successful: {file.fileName} imported as {sw_pn}.bin")

        new_file_obj = File(path=bin_path, fileName=os.path.basename(bin_path))
        
        # [BST-611]
        return FileRecord(
            file=new_file_obj,
            softwarePN=sw_pn,
            hardwarePN=hw_pn,
            dataHash=extracted_hash,
            importedAt=imported_at,
            sizeBytes=size_bytes
        )