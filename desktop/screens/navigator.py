from kivy.uix.screenmanager import ScreenManager as KivyScreenManager

from screens.main_screen import MainScreen
from screens.images_screen import ImagesScreen
from screens.connection_screen import ConnectionScreen
from screens.login_screen import LoginScreen 
from screens.error_screen import ErrorScreen
from screens.post_connection_screen import PostConnectionScreen
from screens.file_transfer_screen import FileTransferScreen 

from data.enums import ScreenName

class ScreenNavigator():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = KivyScreenManager()
        self._add_screens()

    def _add_screens(self):
        self.screen_manager.add_widget(LoginScreen(name=ScreenName.LOGIN.value))
        self.screen_manager.add_widget(MainScreen(name=ScreenName.MAIN.value))
        self.screen_manager.add_widget(ImagesScreen(name=ScreenName.IMAGES.value))
        self.screen_manager.add_widget(ConnectionScreen(name=ScreenName.CONNECTION.value))
        self.screen_manager.add_widget(PostConnectionScreen(name=ScreenName.POST_CONNECTION.value))
        self.screen_manager.add_widget(FileTransferScreen(name=ScreenName.FILE_TRANSFER.value))
        self.screen_manager.add_widget(ErrorScreen(name=ScreenName.ERROR.value))


    def navigate_to(self, screen_name: str):
        self.screen_manager.current = screen_name