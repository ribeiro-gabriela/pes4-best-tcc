from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.metrics import dp 


from data.enums import ScreenName
from ui.event_router import emit_event
from data.events import Event
from screens.actions import action_show_help

class ErrorScreen(Screen):
    error_message = StringProperty("An unexpected error occurred in the application.")

    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = 'error'

    def on_enter(self, *args):
        pass

    def dismiss_error(self, instance=None): 
        emit_event(Event(Event.EventType.DISMISS_ERROR))