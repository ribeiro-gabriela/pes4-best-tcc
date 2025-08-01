from kivy.uix.screenmanager import ScreenManager
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

from ui.components import HorizontalLayout, MenuButton, HelpButton

class TopMenuBar(BoxLayout):
    def __init__(self, screen_manager: ScreenManager, **kwargs):
        self.screen_manager = screen_manager

        super().__init__(**kwargs)
        
        # Left aligned buttons
        left_buttons = HorizontalLayout()
        
        btn_screen1 = MenuButton(text='Screen 1')
        btn_screen1.on_press = lambda: self.go_to_screen('screen1')
        left_buttons.add_widget(btn_screen1)
        
        btn_screen2 = MenuButton(text='Screen 2')
        btn_screen2.on_press = lambda: self.go_to_screen('screen2')
        left_buttons.add_widget(btn_screen2)
        
        btn_screen3 = MenuButton(text='Screen 3') 
        btn_screen3.on_press = lambda: self.go_to_screen('screen3')
        left_buttons.add_widget(btn_screen3)

        self.add_widget(left_buttons)

        # Spacer
        spacer = Label()
        self.add_widget(spacer)

        # Right aligned help button
        btn_help = HelpButton(text='Help', size_hint_x=None, width=100)
        btn_help.on_press = self.show_help
        self.add_widget(btn_help)
    
    def go_to_screen(self, screen_name):
        if self.screen_manager:
            self.screen_manager.current = screen_name
    
    def show_help(self):
        print("Help button pressed")
