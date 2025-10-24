from kivy.app import App
from kivy.lang import Builder

from data.enums import ScreenName
from screens.components import VerticalLayout
from screens.top_menu import TopMenuBar
from screens.navigator import ScreenNavigator

from pathlib import Path

bundle_dir = Path(__file__).parent
path_to_dat = Path.cwd() / bundle_dir / Path("styling.kv")

class ScreenManager(App):
    navigator: ScreenNavigator

    def build(self):
        Builder.load_file(str(path_to_dat))

        layout = VerticalLayout()

        menu_bar = TopMenuBar()
        layout.add_widget(menu_bar)

        navigator = ScreenNavigator()
        self.navigator = navigator
        layout.add_widget(navigator.screen_manager)

        return layout

    def navigate(self, screen: ScreenName):
        assert self.navigator is not None
        
        self.navigator.navigate_to(screen.value)
