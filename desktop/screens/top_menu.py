from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from kivy.uix.image import Image
from kivy.properties import ObjectProperty 

from data.enums import ScreenName
from screens.components import HorizontalLayout, MenuButton
from ui.event_router import emit_event
from data.events import Event


class TopMenuBar(BoxLayout):
    connection_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 0    
        self.opacity = 0  
        self.disabled = True 
        
        self.spacing = dp(10)
        self.padding = [dp(10), dp(10), dp(10), dp(10)]

        embraer_logo = Image(
            source='./uploads/EMB_Logo_white_RGB_1.png', 
            allow_stretch=False,
            keep_ratio=True, 
            size_hint_x=None,
            width=dp(100), 
            pos_hint={'center_y': 0.5} 
        )
        self.add_widget(embraer_logo)
        
        left_buttons = HorizontalLayout()

        button_home = MenuButton(text="HOME")
        button_home.on_press = lambda: emit_event(Event(Event.EventType.NAVIGATE, properties={'target': ScreenName.MAIN.value}))
        left_buttons.add_widget(button_home)

        button_images = MenuButton(text=ScreenName.IMAGES.name)
        button_images.on_press = lambda: emit_event(Event(Event.EventType.NAVIGATE, properties={'target': ScreenName.IMAGES.value}))
        left_buttons.add_widget(button_images)

        self.connection_button = MenuButton(text=ScreenName.CONNECTION.name)
        self.connection_button.on_press = lambda: emit_event(Event(Event.EventType.NAVIGATE, properties={'target': ScreenName.CONNECTION.value}))
        left_buttons.add_widget(self.connection_button)

        #RETIRAR AO SAIR DO MODO DE TESTE
        button_transfer = MenuButton(text=ScreenName.FILE_TRANSFER.name)
        button_transfer.on_press = lambda: emit_event(Event(Event.EventType.NAVIGATE, properties={'target': ScreenName.FILE_TRANSFER.value}))
        left_buttons.add_widget(button_transfer)

        self.add_widget(left_buttons)

        spacer = Label()
        self.add_widget(spacer)

        logout_button = MenuButton(text="Logout") 
        logout_button.on_press = lambda: emit_event(Event(Event.EventType.LOGOUT)) 
        self.add_widget(logout_button)

    def set_connection_button_visibility(self, visible: bool):
        if self.connection_button:
            self.connection_button.opacity = 1 if visible else 0
            self.connection_button.disabled = not visible
            self.connection_button.width = dp(100) if visible else 0 