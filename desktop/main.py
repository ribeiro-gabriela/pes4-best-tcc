from pathlib import Path
import sys
from kivy.resources import resource_add_path, resource_find

from services.arinc_module import ArincModule
from services.connection_service import ConnectionService
from services.file_tranfer_service import FileTransferService
from services.file_validator_service import FileValidatorService
from services.imported_files_service import ImportedFilesService
from services.service_facade import ServiceFacade
from services.user_authentication_service import UserAuthenticationService
from services.wifi_module import WifiModule

BASE = Path(__file__).resolve().parent
resource_add_path(str(BASE / "ui"))

print("KV encontrado?", resource_find("styling.kv"))

from services.user_database_module import UserDatabase
from ui.ui_manager import UiManager


user_database = UserDatabase() 
wifi_module = WifiModule() 
file_validator_service = FileValidatorService() 

user_authentication_service = UserAuthenticationService(
    user_database
)
connection_service = ConnectionService(
    wifi_module,
    test_mode=False  # Habilita modo de teste com hardware PN simulado
)
arinc_module = ArincModule(connection_service) 
file_transfer_service = FileTransferService(
    file_validator_service,
    connection_service,
    arinc_module
)
imported_files_service = ImportedFilesService(
    file_validator_service,
    "uploaded_files"
)

service_facade = ServiceFacade(
    authentication_service=user_authentication_service,
    connection_service=connection_service,
    file_transfer_service=file_transfer_service,
    imported_files_service=imported_files_service,
    file_validator_service=file_validator_service,
)

desktop_app = UiManager(service_facade)

if __name__ == '__main__':
    desktop_app.run()