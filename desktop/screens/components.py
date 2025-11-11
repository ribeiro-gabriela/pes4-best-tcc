from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton 
from kivy.uix.textinput import TextInput 
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from typing import List, Dict, Any

class MenuButton(Button):
    pass

class HelpButton(Button):
    pass

class HorizontalLayout(BoxLayout):
    pass

class ScreenLayout(BoxLayout):
    pass

class PrimaryButton(Button):
    pass

class SecondaryButton(Button):
    pass

class TitleLabel(Label):
    pass

class ConnectButton(Button):
    pass

class CompactLayout(BoxLayout):
    pass

class TableLayout(GridLayout):
    pass

class HeaderLabel(Label):
    pass

class NormalLabel(Label):
    pass

class WifiLabel(Label):
    pass

class VerticalLayout(BoxLayout):
    pass

class WifiNetworkItem(BoxLayout):
    ssid = StringProperty('')
    signal = NumericProperty(0)
    security_type = StringProperty('')
    connect_action = ObjectProperty(None)

PRIMARY = (0.2, 0.6, 0.8, 1)
SECONDARY = (0.3, 0.3, 0.3, 1)

class SystemImageItem(ToggleButton): 
    image_name = StringProperty('')
    is_compatible = BooleanProperty(False) 
    on_selection = ObjectProperty(None) 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.group = 'system_images' 
        self.size_hint_y = None
        self.height = dp(50)
        self.background_normal = ''
        self.background_down = '' 
        self.color = (1,1,1,1) 

    def on_state(self, instance, value):
        super().on_state(instance, value) 
        if self.on_selection:
            self.on_selection(self)

class LoginCard(BoxLayout):
    pass

class LoginTextInput(TextInput):
    pass

class HelpIconButton(ButtonBehavior, BoxLayout):
    source = StringProperty('')
    label_text = StringProperty('')