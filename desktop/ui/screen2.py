from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen

from ui.components import ScreenLayout, TitleLabel, PrimaryButton, SecondaryButton

class Screen2(Screen):
    def __init__(self, screen_manager: ScreenManager, **kwargs):
        super().__init__(**kwargs)

        self.screen_manager = screen_manager

        self.name = 'screen2'
        
        layout = ScreenLayout()
        
        layout.add_widget(TitleLabel(text='Welcome to Screen 2'))
        
        #Navigate back to Screen 1
        btn1 = SecondaryButton(text='Back to Screen 1')
        btn1.on_press = self.go_to_screen1
        layout.add_widget(btn1)
        
        # Additional buttons for Screen 2
        btn2 = PrimaryButton(text='Button 2')
        layout.add_widget(btn2)

        btn3 = PrimaryButton(text='Button 3')
        layout.add_widget(btn3)
        
        # Spacer
        layout.add_widget(Label())  
        
        self.add_widget(layout)

    def go_to_screen1(self):
        self.screen_manager.current = 'screen1'
