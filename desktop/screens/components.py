from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton 
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from typing import List, Dict, Any
from kivy.graphics import Color, RoundedRectangle

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.group = 'system_images' 
        self.size_hint_y = None
        self.height = dp(50)

        self.background_normal = ''
        self.background_down = ''
        self.color = (0.9, 0.9, 0.9, 1)
        self.background_color = (0.18, 0.18, 0.20, 1)

        self.text = self.image_name
        self.bind(image_name=lambda *_: setattr(self, 'text', self.image_name)) 

        with self.canvas.before:
            self._bg_color = Color(rgba=SECONDARY)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5),])

        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)
        self._update_bg() 

    def on_state(self, *args):
        pass

    def _update_bg(self, *args):
        self._bg_color.rgba = PRIMARY if self.state == 'down' else SECONDARY
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size