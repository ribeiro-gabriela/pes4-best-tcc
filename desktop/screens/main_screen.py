from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout

from screens.actions import action_go_to_screen, action_show_help
from screens.components import ScreenLayout, TitleLabel, PrimaryButton, HelpButton

from data.enums import ScreenName
from ui.event_router import emit_event
from data.events import Event

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
                
        self.name = ScreenName.MAIN.value
        
        root_float_layout = FloatLayout()
        
        screen_content_layout = ScreenLayout() 
        screen_content_layout.size_hint = (0.8, 0.8) 
        screen_content_layout.pos_hint = {'center_x': 0.5, 'center_y': 0.5} 
        screen_content_layout.add_widget(TitleLabel(text='Welcome to the System!'))

        btn_images = PrimaryButton(text=f'Go to {ScreenName.IMAGES.value}')
        btn_images.on_press = lambda: emit_event(Event(Event.EventType.NAVIGATE, properties={'target': ScreenName.IMAGES.value}))
        screen_content_layout.add_widget(btn_images)

        btn_connection = PrimaryButton(text=f'Go to {ScreenName.CONNECTION.value}')
        btn_connection.on_press = lambda: emit_event(Event(Event.EventType.NAVIGATE, properties={'target': ScreenName.CONNECTION.value}))
        screen_content_layout.add_widget(btn_connection)


        root_float_layout.add_widget(screen_content_layout) 

        help_button = HelpButton(text="Help") 
        help_button.size_hint = (None, None) 
        help_button.size = (dp(100), dp(50)) 
        help_button.pos_hint = {'right': 0.98, 'bottom': 0.02} 
        help_button.on_press = action_show_help() 
        root_float_layout.add_widget(help_button)

        self.add_widget(root_float_layout)
    
    def do_logout(self):
        emit_event(Event(Event.EventType.LOGOUT))

def error():
    raise Exception("Error")