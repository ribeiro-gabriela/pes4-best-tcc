from kivy.uix.screenmanager import ScreenManager

from ui.main_screen import MainScreen
from ui.images_screen import ImagesScreen
from ui.connection_screen import ConnectionScreen

class ScreenNavigator():
    def __init__(self) -> None:
        self.screen_manager = ScreenManager()
        self._add_screens()

    def _add_screens(self):
        self.screen_manager.add_widget(MainScreen())
        self.screen_manager.add_widget(ImagesScreen())
        self.screen_manager.add_widget(ConnectionScreen())

    def navigate_to(self, screen_name: str):
        self.screen_manager.current = screen_name