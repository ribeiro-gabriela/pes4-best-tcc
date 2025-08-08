from kivy.app import App
from kivy.lang import Builder

from ui.components import VerticalLayout
from ui.top_menu import TopMenuBar
from ui.navigator import ScreenNavigator

from pathlib import Path

bundle_dir = Path(__file__).parent
path_to_dat = Path.cwd() / bundle_dir / Path("styling.kv")


class DesktopAppUi(App):
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

    def navigate_to(self, screen_name: str):
        assert self.navigator is not None
        
        self.navigator.navigate_to(screen_name)


if __name__ == "__main__":
    DesktopAppUi().run()
