import logging
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
import sys 

from data.enums import ScreenName
from screens.components import VerticalLayout, HelpIconButton
from screens.top_menu import TopMenuBar
from screens.navigator import ScreenNavigator
from screens.actions import action_show_help

from pathlib import Path

bundle_dir = Path(__file__).parent
path_to_dat = Path.cwd() / bundle_dir / Path("styling.kv")

class ScreenManager(App):
    navigator: ScreenNavigator = ObjectProperty(None)
    service_facade = ObjectProperty(None)
    menu_bar_widget: TopMenuBar = ObjectProperty(None)
    help_button_widget: HelpIconButton = ObjectProperty(None)

    def build(self):
        # [BST - 330]
        self.title = 'WI-FLY'
        self.icon = './uploads/icon.png'

        if path_to_dat.exists():
            Builder.load_file(str(path_to_dat))
        else:
            print(f"FATAL ERROR: styling.kv not found in {path_to_dat}. The application cannot start.")
            sys.exit(1)

        root_float_layout = FloatLayout() 

        background_image = Image(
            source='./uploads/background_image.png', 
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        root_float_layout.add_widget(background_image)

        # [BST-327]
        self.menu_bar_widget = TopMenuBar()
        self.menu_bar_widget.size_hint = (1, None) 
        self.menu_bar_widget.height = dp(50)
        self.menu_bar_widget.pos_hint = {'top': 1}
        root_float_layout.add_widget(self.menu_bar_widget)

        navigator_container = FloatLayout()
        navigator_container.size_hint = (1, 1)
        navigator_container.pos_hint = {'top': 1 - (self.menu_bar_widget.height / self.root_window.height if self.root_window else 0.05)}

        self.navigator = ScreenNavigator()
        self.navigator.screen_manager.size_hint = (1, 1)
        navigator_container.add_widget(self.navigator.screen_manager)
        root_float_layout.add_widget(navigator_container)

        # [BST-328]
        # [BST-326]
        self.help_button_widget = HelpIconButton(
            source='./uploads/help.png', 
            label_text='Help'
        )
        self.help_button_widget.size_hint = (None, None)
        self.help_button_widget.size = (dp(60), dp(80))
        self.help_button_widget.pos_hint = {'right': 0.98, 'bottom': 0.02}
        # [BST-329]
        self.help_button_widget.bind(on_release=lambda x: action_show_help())
        root_float_layout.add_widget(self.help_button_widget)

        for screen in self.navigator.screen_manager.screens:
            if hasattr(screen, '_service_facade'): 
                screen._service_facade = self.service_facade

        self.toggle_menu_bar_visibility(False)
        self.help_button_widget.opacity = 1
        self.help_button_widget.disabled = False

        return root_float_layout

    def navigate(self, screen_name: str):
        assert self.navigator is not None

        is_login_screen = (screen_name == ScreenName.LOGIN.value)
        is_file_transfer_screen = (screen_name == ScreenName.FILE_TRANSFER.value)
        no_menu_screen = is_login_screen or is_file_transfer_screen
        self.toggle_menu_bar_visibility(not no_menu_screen) 

        is_post_connection_screen = (screen_name == ScreenName.POST_CONNECTION.value)
        is_images_screen = (screen_name == ScreenName.IMAGES.value)
        no_connection_button = is_post_connection_screen or is_images_screen
        if self.menu_bar_widget and self.menu_bar_widget.connection_button:
            self.menu_bar_widget.set_connection_button_visibility(not no_connection_button)

        is_connection_screen = (screen_name == ScreenName.CONNECTION.value)
        if self.menu_bar_widget and self.menu_bar_widget.button_images:
            self.menu_bar_widget.set_images_button_visibility(not is_connection_screen)

        self.navigator.navigate_to(screen_name)

    def toggle_menu_bar_visibility(self, visible: bool):
        if self.menu_bar_widget:
            self.menu_bar_widget.opacity = 1 if visible else 0
            self.menu_bar_widget.disabled = not visible
            self.menu_bar_widget.height = dp(50) if visible else 0 
            self.menu_bar_widget.size_hint_y = None if visible else 0 
            if self.menu_bar_widget.parent:
                self.menu_bar_widget.parent.do_layout()