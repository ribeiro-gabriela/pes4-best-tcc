from data.events import Event
from ui.screen_manager import ScreenManager

from ui.event_router import emit_event, event_router
from ui.state_controller import StateController

from kivy.base import ExceptionManager

class CustomExceptionHandler():
    def handle_exception(self, exception):
        emit_event(Event(Event.EventType.ERROR, exception))
        return ExceptionManager.PASS

class UiManager:
    event_router = event_router
    screen_manager = ScreenManager()
    state_controller = StateController(event_router, screen_manager)

    def run(self):
        ExceptionManager.add_handler(CustomExceptionHandler())
        
        self.screen_manager.run()
