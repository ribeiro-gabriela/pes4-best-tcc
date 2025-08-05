from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from ui.actions import action_go_to_screen
from ui.components import ScreenLayout, TitleLabel, PrimaryButton

from custom_types.screens import ScreenName

class MainScreen(Screen):
    def __init__(self):
        super().__init__()
        
        self.name = ScreenName.MAIN.value
        
        layout = ScreenLayout()

        layout.add_widget(TitleLabel(text=f'{self.name} screen'))
        
        btn1 = PrimaryButton(text=f'Go to {ScreenName.IMAGES.value}')
        btn1.on_press = action_go_to_screen(ScreenName.IMAGES)
        layout.add_widget(btn1)
        
        btn2 = PrimaryButton(text=f'Go to {ScreenName.CONNECTION.value}')
        btn2.on_press = action_go_to_screen(ScreenName.CONNECTION)
        layout.add_widget(btn2)
        
        self.add_spacer_to_layout(layout)
        
        self.add_widget(layout)

    def add_spacer_to_layout(self, layout: ScreenLayout):
        layout.add_widget(Label())