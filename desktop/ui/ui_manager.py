from data.events import Event
from ui.screen_manager import ScreenManager

from ui.event_router import emit_event, event_router
from ui.state_controller import StateController

from kivy.base import ExceptionManager
from pathlib import Path
import sys

from services.logging_service import LoggingService
from services.service_facade import ServiceFacade

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class CustomExceptionHandler():
    def handle_exception(self, exception):
        emit_event(Event(Event.EventType.ERROR, error=exception, properties={'message': str(exception)}))
        return ExceptionManager.PASS

class UiManager:
    def __init__(self, service_facade: ServiceFacade):
        self.logger_app = LoggingService(UiManager.__name__)
        self.logger_app.log("Starting the UiManager configuration...")
        self.service_facade = service_facade

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