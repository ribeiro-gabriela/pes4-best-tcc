from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from custom_types.screens import ScreenName
from ui.actions import action_go_to_screen
from ui.components import ScreenLayout, TitleLabel, PrimaryButton, SecondaryButton

class ImagesScreen(Screen):
    def __init__(self):
        super().__init__()

        self.name = ScreenName.IMAGES.value

        layout = ScreenLayout()
        
        layout.add_widget(TitleLabel(text=f'{self.name} screen'))
        
        btn1 = SecondaryButton(text=f'Back to {ScreenName.MAIN.value}')
        btn1.on_press = action_go_to_screen(ScreenName.MAIN)
        layout.add_widget(btn1)
        
        btn2 = PrimaryButton(text=f'Upload')
        layout.add_widget(btn2)

        btn3 = PrimaryButton(text='Delete')
        layout.add_widget(btn3)
        
        # Spacer
        layout.add_widget(Label())  
        
        self.add_widget(layout)
