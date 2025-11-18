from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from kivy.uix.image import Image
from kivy.properties import ObjectProperty 

from data.enums import ScreenName
from screens.components import HorizontalLayout, MenuButton
from ui.event_router import emit_event
from data.events import Event
from services.service_facade import ServiceFacade

service_facade: ServiceFacade = None

# [BST-332]
def check_authentication(target_screen: str):
    if service_facade and service_facade.isAuthenticated():
        emit_event(Event(Event.EventType.NAVIGATE, properties={'target': target_screen}))
    else:
        emit_event(Event(Event.EventType.LOGOUT))

class TopMenuBar(BoxLayout):
    connection_button = ObjectProperty(None)
    button_images = ObjectProperty(None)

    def __init__(self, **kwargs):
        # [BST-327]
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
        # [BST-332]
        button_home.on_press = lambda: check_authentication(ScreenName.MAIN.value)
        left_buttons.add_widget(button_home)

        self.button_images = MenuButton(text="Manage Images")
        # [BST-332]
        self.button_images.on_press = lambda: check_authentication(ScreenName.IMAGES.value)
        left_buttons.add_widget(self.button_images)

        self.connection_button = MenuButton(text="Search BC Modules")
        # [BST-332]
        self.connection_button.on_press = lambda: check_authentication(ScreenName.CONNECTION.value)
        left_buttons.add_widget(self.connection_button)

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
            self.connection_button.width = dp(130) if visible else 0 

    def set_images_button_visibility(self, visible: bool):
        if self.button_images:
            self.button_images.opacity = 1 if visible else 0
            self.button_images.disabled = not visible
            self.button_images.width = dp(130) if visible else 0 