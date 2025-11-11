from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.metrics import dp
import sys 

from data.enums import ScreenName
from screens.components import VerticalLayout
from screens.top_menu import TopMenuBar
from screens.navigator import ScreenNavigator

from pathlib import Path

bundle_dir = Path(__file__).parent
path_to_dat = Path.cwd() / bundle_dir / Path("styling.kv")

class ScreenManager(App):
    navigator: ScreenNavigator = ObjectProperty(None)
    service_facade = ObjectProperty(None)
    menu_bar_widget: TopMenuBar = ObjectProperty(None)

    def build(self):
        if path_to_dat.exists():
            Builder.load_file(str(path_to_dat))
        else:
            print(f"FATAL ERROR: styling.kv not found in {path_to_dat}. The application cannot start.")
            sys.exit(1)

        root_layout = VerticalLayout() 

        self.menu_bar_widget = TopMenuBar()
        root_layout.add_widget(self.menu_bar_widget)

        self.navigator = ScreenNavigator()
        root_layout.add_widget(self.navigator.screen_manager)

        for screen in self.navigator.screen_manager.screens:
            if hasattr(screen, '_service_facade'): 
                screen._service_facade = self.service_facade

        self.toggle_menu_bar_visibility(False)

        return root_layout

    def navigate(self, screen_name: str):
        assert self.navigator is not None
        
        self.navigator.navigate_to(screen_name)

    def toggle_menu_bar_visibility(self, visible: bool):
        if self.menu_bar_widget:
            self.menu_bar_widget.opacity = 1 if visible else 0
            self.menu_bar_widget.disabled = not visible
            self.menu_bar_widget.height = dp(50) if visible else 0 
            self.menu_bar_widget.size_hint_y = None if visible else 0 
            if self.root:
                self.root.do_layout()