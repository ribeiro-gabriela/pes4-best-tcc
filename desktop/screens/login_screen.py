from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock

from ui.event_router import emit_event, event_router
from data.events import Event
from data.enums import ScreenName
from screens.actions import action_show_help


class LoginScreen(Screen):
    login_message = StringProperty("")
    
    username_input = ObjectProperty(None)
    password_input = ObjectProperty(None)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = ScreenName.LOGIN.value
        event_router.register_callback(self._handle_event)

    def on_kv_post(self, base_widget):
        self.username_input = self.ids.get('username_input')
        self.password_input = self.ids.get('password_input')
        
        if self.username_input:
            Clock.schedule_once(lambda dt: setattr(self.username_input, 'focus', True), 0)

    def _handle_event(self, event: Event) -> None:
        if event.type == Event.EventType.LOGIN_FAILURE:
            # [BST-300]
            if self.manager and self.manager.current == self.name:
                self.login_message = event.properties.get('message', 'Login failure')
                if self.password_input:
                    self.password_input.text = ""
        elif event.type == Event.EventType.LOGIN_SUCCESS:
            if self.manager and self.manager.current == self.name:
                self.login_message = ""
                if self.username_input:
                    self.username_input.text = ""
                if self.password_input:
                    self.password_input.text = ""

    def on_enter(self, *args):
        self.login_message = "" 
        if self.username_input:
            self.username_input.text = "" 
        if self.password_input:
            self.password_input.text = ""

        if not self.username_input and 'username_input' in self.ids:
            self.username_input = self.ids['username_input']
        if not self.password_input and 'password_input' in self.ids:
            self.password_input = self.ids['password_input']

        if self.username_input:
            Clock.schedule_once(lambda dt: setattr(self.username_input, 'focus', True), 0)

        return super().on_enter(*args)
    
    def focus_password_input(self, instance):
        if self.password_input:
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

        # [BST-331]
        emit_event(Event(Event.EventType.LOGIN_ATTEMPT, properties={'username': username, 'password': password}))