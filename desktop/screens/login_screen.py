from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.uix.textinput import TextInput
from kivy.metrics import dp 
from kivy.uix.floatlayout import FloatLayout 

from ui.event_router import emit_event, event_router
from data.events import Event
from data.enums import ScreenName
from screens.actions import action_show_help
from screens.components import ScreenLayout, TitleLabel, NormalLabel, PrimaryButton, HelpButton


class LoginScreen(Screen):
    login_message = StringProperty("") 

    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = 'login'

        root_float_layout = FloatLayout()

        screen_content_layout = ScreenLayout(orientation='vertical') 
        screen_content_layout.size_hint = (0.8, 0.8) 
        screen_content_layout.pos_hint = {'center_x': 0.5, 'center_y': 0.5} 

        screen_content_layout.add_widget(TitleLabel(text='Access the System', size_hint_y=None, height='60dp'))

        self.username_input = TextInput(
            hint_text='Username', multiline=False, password=False,
            font_size='18sp', size_hint_y=None, height='60dp', padding=[dp(10), dp(10), dp(10), dp(10)],
            background_color=[1, 1, 1, 1],
            write_tab=False
        )
        self.username_input.bind(on_text_validate=self.focus_password_input)
        screen_content_layout.add_widget(self.username_input)

        self.password_input = TextInput(
            hint_text='Password', multiline=False, password=True,
            font_size='18sp', size_hint_y=None, height='60dp', padding=[dp(10), dp(10), dp(10), dp(10)],
            background_color=[1, 1, 1, 1],
            write_tab=False
        )
        self.password_input.bind(on_text_validate=lambda instance: self.attempt_login(self.username_input.text, self.password_input.text))
        screen_content_layout.add_widget(self.password_input)

        self.error_label_widget = NormalLabel(
            text=self.login_message,
            color=[0.9, 0.2, 0.2, 1],
            size_hint_y=None, height='40dp',
            text_size=(screen_content_layout.width * 0.9, None), 
            halign='center', valign='middle'
        )
        screen_content_layout.bind(width=lambda instance, value: setattr(self.error_label_widget, 'text_size', (value * 0.9, None)))
        self.bind(login_message=self.error_label_widget.setter('text'))
        screen_content_layout.add_widget(self.error_label_widget)

        login_button = PrimaryButton(text='Enter', size_hint_y=None, height='60dp')
        login_button.bind(on_release=lambda x: self.attempt_login(self.username_input.text, self.password_input.text))
        screen_content_layout.add_widget(login_button)

        root_float_layout.add_widget(screen_content_layout) 
        
        help_button = HelpButton(text="Help")
        help_button.size_hint = (None, None)
        help_button.size = (dp(100), dp(50))
        help_button.pos_hint = {'right': 0.98, 'bottom': 0.02}
        help_button.on_press = action_show_help()
        root_float_layout.add_widget(help_button)
        
        self.add_widget(root_float_layout) 

        event_router.register_callback(self._handle_event)
        
    def _handle_event(self, event: Event) -> None:
        if event.type == Event.EventType.LOGIN_FAILURE:
            if self.manager and self.manager.current == self.name:
                self.login_message = event.properties.get('message', 'Unknown login error.')
                self.password_input.text = ""
        elif event.type == Event.EventType.LOGIN_SUCCESS:
            if self.manager and self.manager.current == self.name:
                self.login_message = ""
                self.username_input.text = ""
                self.password_input.text = ""


    def on_enter(self, *args):
        self.login_message = "" 
        self.username_input.text = "" 
        self.password_input.text = ""
        self.username_input.focus = True
        return super().on_enter(*args)
    
    def focus_password_input(self, instance):
        self.password_input.focus = True

    def attempt_login(self, username, password):
        self.login_message = "" 

        if not username and not password:
            self.login_message = "Please enter your username and password."
            return
        elif not username:
            self.login_message = "Please enter your username."
            return
        elif not password:
            self.login_message = "Please enter the password."
            return

        emit_event(Event(Event.EventType.LOGIN_ATTEMPT, properties={'username': username, 'password': password}))