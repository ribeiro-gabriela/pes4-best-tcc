from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout

from screens.actions import action_go_to_screen, action_show_help
from screens.components import ScreenLayout, TitleLabel, PrimaryButton

from data.enums import ScreenName
from ui.event_router import emit_event
from data.events import Event
from services.service_facade import ServiceFacade

service_facade: ServiceFacade = None

# [BST-332]
"""def check_authentication(target_screen: str):
    if service_facade and service_facade.isAuthenticated():
        emit_event(Event(Event.EventType.NAVIGATE, properties={'target': target_screen}))
    else:
        emit_event(Event(Event.EventType.LOGOUT))"""

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = ScreenName.MAIN.value
        
    def emit_navigate_to_images(self):
        # [BST-332]
        #check_authentication(ScreenName.IMAGES.value)
        #TROCAR A LINHA COMENTADA
        emit_event(Event(Event.EventType.NAVIGATE, properties={'target': ScreenName.IMAGES.value}))

    def emit_navigate_to_connections(self):
        # [BST-332]
        # [BST-305]
        #check_authentication(ScreenName.CONNECTION.value)
        #TROCAR A LINHA COMENTADA
        emit_event(Event(Event.EventType.NAVIGATE, properties={'target': ScreenName.CONNECTION.value}))

    def do_logout(self):
        emit_event(Event(Event.EventType.LOGOUT))

def error():
    raise Exception("Error")