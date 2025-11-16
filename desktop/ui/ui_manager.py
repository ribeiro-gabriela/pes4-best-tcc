from data.events import Event
from ui.screen_manager import ScreenManager

from ui.event_router import emit_event, event_router
from ui.state_controller import StateController

from kivy.base import ExceptionManager
from pathlib import Path
import sys

from services.logging_service import LoggingService
from services.user_authentication_service import UserAuthenticationService
from services.user_database_module import UserDatabase
from services.connection_service import ConnectionService
from services.file_tranfer_service import FileTransferService
from services.imported_files_service import ImportedFilesService
from services.service_facade import ServiceFacade
from services.wifi_module import WifiModule
from services.file_validator_service import FileValidatorService
from services.arinc_module import ArincModule

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class CustomExceptionHandler():
    def handle_exception(self, exception):
        emit_event(Event(Event.EventType.ERROR, error=exception, properties={'message': str(exception)}))
        return ExceptionManager.PASS

class UiManager:

    def __init__(self):
        self.logger_app = LoggingService("UiManager")
        self.logger_auth = LoggingService("UserAuthenticationService")
        self.logger_app.log("Starting the UiManager configuration...")

        self.user_database = UserDatabase() 
        self.wifi_module = WifiModule() 
        self.file_validator_service = FileValidatorService() 
        self.arinc_module = ArincModule() 

        self.user_authentication_service = UserAuthenticationService(
            self.user_database,
            self.logger_auth
        )
        self.connection_service = ConnectionService(
            self.wifi_module,
            test_mode=True  # Habilita modo de teste com hardware PN simulado
        )
        self.file_transfer_service = FileTransferService(
            self.file_validator_service,
            self.connection_service,
            self.arinc_module
        )
        self.imported_files_service = ImportedFilesService(
            self.file_validator_service,
            "uploaded_files"
        )

        self.logger_app.log("Individual services initialized.")

        self.service_facade = ServiceFacade(
            authentication_service=self.user_authentication_service,
            connection_service=self.connection_service,
            file_transfer_service=self.file_transfer_service,
            imported_files_service=self.imported_files_service
        )
        self.logger_app.log("ServiceFacade initialized with all services.")

        self.screen_manager = ScreenManager()
        self.screen_manager.service_facade = self.service_facade
        self.logger_app.log("ScreenManager initialized and ServiceFacade injected.")

        self.state_controller = StateController(
            event_router, 
            self.screen_manager,
            self.service_facade
        )
        self.logger_app.log("The StateController has been initialized.")

    def run(self):
        ExceptionManager.add_handler(CustomExceptionHandler())
        self.screen_manager.run()