import logging
from pathlib import Path
import os
import platform
from kivy.resources import resource_add_path, resource_find

from services.arinc_module import ArincModule
from services.connection_service import ConnectionService
from services.file_tranfer_service import FileTransferService
from services.file_validator_service import FileValidatorService
from services.imported_files_service import ImportedFilesService
from services.service_facade import ServiceFacade
from services.user_authentication_service import UserAuthenticationService
from services.wifi_module import WifiModule
from services.wifi_module_linux import WifiModuleLinux

logging.getLogger('kivy').setLevel(logging.ERROR) 


BASE = Path(__file__).resolve().parent
resource_add_path(str(BASE))
resource_add_path(str(BASE / "ui"))

FILE_DIRECTORY = "file_directory"
if not os.path.exists(FILE_DIRECTORY):
    os.makedirs(FILE_DIRECTORY)

from services.user_database_module import UserDatabase
from ui.ui_manager import UiManager

user_database = UserDatabase() 

if platform.system() == "Windows":
    wifi_module = WifiModule() 
else:
    wifi_module = WifiModuleLinux()

file_validator_service = FileValidatorService() 

user_authentication_service = UserAuthenticationService(
    user_database
)
connection_service = ConnectionService(
    wifi_module,
    test_mode=False  # Habilita modo de teste com hardware PN simulado
)
arinc_module = ArincModule(connection_service, FILE_DIRECTORY) 
file_transfer_service = FileTransferService(
    file_validator_service,
    connection_service,
    arinc_module
)
imported_files_service = ImportedFilesService(
    file_validator_service,
    f"{FILE_DIRECTORY}/images"
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