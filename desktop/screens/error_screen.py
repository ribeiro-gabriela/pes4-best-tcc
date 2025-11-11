from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.metrics import dp 
from kivy.uix.floatlayout import FloatLayout 


from data.enums import ScreenName
from ui.event_router import emit_event
from data.events import Event
from screens.actions import action_show_help

from screens.components import ScreenLayout, TitleLabel, NormalLabel, PrimaryButton, HelpButton


class ErrorScreen(Screen):
    error_message = StringProperty("An unexpected error occurred in the application.")

    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = 'error'

        root_float_layout = FloatLayout()
        
        screen_content_layout = ScreenLayout() 
        screen_content_layout.size_hint = (0.8, 0.8) 
        screen_content_layout.pos_hint = {'center_x': 0.5, 'center_y': 0.5} 

        screen_content_layout.add_widget(TitleLabel(text='An error occurred!', color=[1, 0, 0, 1]))
        
        self.error_label_widget = NormalLabel(
            text=self.error_message,
            color=[0.9, 0.2, 0.2, 1],
            text_size=(screen_content_layout.width * 0.9, None), 
            halign='center', valign='middle',
            size_hint_y=None, height='100dp'
        )

        screen_content_layout.bind(width=lambda instance, value: setattr(self.error_label_widget, 'text_size', (value * 0.9, None)))
        self.bind(error_message=self.error_label_widget.setter('text'))
        screen_content_layout.add_widget(self.error_label_widget)
        
        dismiss_button = PrimaryButton(text='Dismiss')
        dismiss_button.bind(on_release=self.dismiss_error)
        screen_content_layout.add_widget(dismiss_button)

        root_float_layout.add_widget(screen_content_layout) 
        
        help_button = HelpButton(text="Help")
        help_button.size_hint = (None, None)
        help_button.size = (dp(100), dp(50))
        help_button.pos_hint = {'right': 0.98, 'bottom': 0.02}
        help_button.on_press = action_show_help()
        root_float_layout.add_widget(help_button)
        
        self.add_widget(root_float_layout) 

    def on_enter(self, *args):
        pass

    def dismiss_error(self, instance):
        emit_event(Event(Event.EventType.DISMISS_ERROR))