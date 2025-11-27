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

class WiFiLabel(Label):
    pass

class VerticalLayout(BoxLayout):
    pass

class WifiNetworkItem(BoxLayout):
    ssid = StringProperty('')
    signal = NumericProperty(0)
    security_type = StringProperty('')
    connect_action = ObjectProperty(None)

class SystemImageItem(ToggleButton):
    image_name = StringProperty('')
    on_selection = ObjectProperty(None)
    active = BooleanProperty(False) 

    def __init__(self, **kwargs):
        _on_selection_callback = kwargs.pop('on_selection', None)
        super().__init__(**kwargs)

        if _on_selection_callback:
            self.on_selection = _on_selection_callback

    def on_release(self):
        was_active_before_super = self.active
        super().on_release() 

        if self.active == was_active_before_super:
            self.active = not was_active_before_super
        
        if self.on_selection:
            self.on_selection(self)

class LoginCard(BoxLayout):
    pass

class LoginTextInput(TextInput):
    pass

class HelpIconButton(ButtonBehavior, BoxLayout):
    source = StringProperty('')
    label_text = StringProperty('')

class ImageListItem(BoxLayout):
    file_name = StringProperty('')
    delete_action = ObjectProperty(None)

class DeleteButton(Button):
    pass