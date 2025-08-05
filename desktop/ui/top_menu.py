from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

from custom_types.screens import ScreenName
from ui.actions import action_go_to_screen, action_show_help
from ui.components import HorizontalLayout, MenuButton, HelpButton


class TopMenuBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        left_buttons = HorizontalLayout()

        button1 = _build_menu_button("Home", ScreenName.MAIN)
        left_buttons.add_widget(button1)

        button2 = _build_menu_button(ScreenName.IMAGES.name, ScreenName.IMAGES)
        left_buttons.add_widget(button2)

        button3 = _build_menu_button(ScreenName.CONNECTION.name, ScreenName.CONNECTION)
        left_buttons.add_widget(button3)

        self.add_widget(left_buttons)

        spacer = Label()
        self.add_widget(spacer)

        button_help = _build_help_button()
        self.add_widget(button_help)
        
def _build_menu_button(button_text: str, target_screen: ScreenName):
    button = MenuButton(text=button_text)
    button.on_press = action_go_to_screen(target_screen)
    return button

def _build_help_button():
    button = HelpButton(text="Help")
    button.on_press = action_show_help()
    return button