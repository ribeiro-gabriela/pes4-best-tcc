from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen

from ui.components import ScreenLayout, TitleLabel, PrimaryButton

class Screen1(Screen):
    def __init__(self, screen_manager: ScreenManager, **kwargs):
        super().__init__(**kwargs)

        self.screen_manager = screen_manager

        self.name = 'screen1'
        
        layout = ScreenLayout()

        #Title
        layout.add_widget(TitleLabel(text='Welcome to Screen 1'))
        
        # Button 1 - Navigate to Screen 2
        btn1 = PrimaryButton(text='Go to Screen 2')
        btn1.on_press = self.go_to_screen2
        layout.add_widget(btn1)
        
        # Button 2 - Navigate to Screen 3
        btn2 = PrimaryButton(text='Go to Screen 3')
        btn2.on_press = self.go_to_screen3
        layout.add_widget(btn2)
        
        #Spacer
        layout.add_widget(Label())
        
        self.add_widget(layout)

    def go_to_screen2(self):
        self.screen_manager.current = 'screen2'
    
    def go_to_screen3(self):
        self.screen_manager.current = 'screen3'
