from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen

from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp 
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ListProperty, StringProperty, BooleanProperty, ObjectProperty 

from data.enums import ScreenName
from screens.components import WifiNetworkItem

from services.service_facade import ServiceFacade
from ui.event_router import emit_event, event_router 
from data.events import Event
from typing import Optional, Dict, Any

class ConnectionScreen(Screen):
    _service_facade: ServiceFacade = None
    
    available_networks_data = ListProperty([]) 
    empty_list_message = StringProperty("No WiFi networks found.")
    show_empty_message = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = ScreenName.CONNECTION.value
        event_router.register_callback(self._handle_event)

    def _handle_event(self, event: Event) -> None:
        if event.type == Event.EventType.CONNECTION_FAILURE:
            if self.manager and self.manager.current == self.name:
                message = event.properties.get('message', 'WiFi connection failure.')
                self._show_error_popup(message)
        elif event.type == Event.EventType.CONNECTION_SUCCESS:
            pass 

    def on_enter(self, *args):
        if self._service_facade:
            self.load_wifi_connections()
        else:
            print("WARNING: ServiceFacade not injected into ConnectionScreen on_enter.")

    def load_wifi_connections(self):   
        list_container = self.ids.network_list_container 
        list_container.clear_widgets()

        if self._service_facade:
            real_networks = self._service_facade.getWifiConnections()

            if not real_networks:
                self.available_networks_data = [
                    {"ssid": "RM_2G_TestData", "info": {"security": "WPA2", "signal": -50}},
                    {"ssid": "RM_5G_TestData", "info": {"security": "Open", "signal": -70}},
                    {"ssid": "WIFI_TEST_3", "info": {"security": "WPA", "signal": -65}},
                ]
            else:
                self.available_networks_data = real_networks
            
            self.available_networks_data.sort(key=lambda x: x["info"]["signal"], reverse=False)

            for conn_data in self.available_networks_data:
                ssid = conn_data["ssid"]
                info = conn_data["info"]
                security_type = info["security"]
                signal_raw = info["signal"]

                numeric_signal = 0
                if isinstance(signal_raw, str):
                    try:
                        numeric_signal = int(signal_raw.replace(' dBm', '').strip())
                    except ValueError:
                        print(f"WARNING: Could not parse signal '{signal_raw}'. Using 0.")
                        numeric_signal = 0
                elif isinstance(signal_raw, (int, float)):
                    numeric_signal = signal_raw

                network_item = WifiNetworkItem(
                    ssid=ssid,
                    signal=numeric_signal,
                    security_type=security_type,
                    connect_action=lambda s=ssid, st=security_type: self._prompt_for_password_if_needed(s, st)
                )
                list_container.add_widget(network_item)
            
            self.show_empty_message = not bool(self.available_networks_data) 
                
        else:
            self.show_empty_message = True

    def _prompt_for_password_if_needed(self, network_name: str, security_type: str):
        if security_type == "Open" or security_type == "Unknown":
            self.connectToWifi(network_name, None)
        else:
            content = BoxLayout(orientation='vertical', spacing='10dp', padding='10dp')
            content.add_widget(Label(text=f"Senha para {network_name}:", size_hint_y=None, height='40dp'))

            def on_enter_pressed(instance):
                self._connect_with_password(network_name, instance.text, popup)

            password_input = TextInput(password=True, multiline=False, size_hint_y=None, height='40dp', on_text_validate=on_enter_pressed)
            content.add_widget(password_input)
            
            buttons = BoxLayout(size_hint_y=None, height='40dp', spacing='10dp')
            btn_connect = Button(text="Connect")
            btn_connect.bind(on_release=lambda x: self._connect_with_password(network_name, password_input.text, popup))
            buttons.add_widget(btn_connect)
            
            btn_cancel = Button(text="Cancel")
            btn_cancel.bind(on_release=lambda x: popup.dismiss())
            buttons.add_widget(btn_cancel)
            
            content.add_widget(buttons)

            popup = Popup(title="Connect to the Secure Network", content=content, size_hint=(0.7, 0.5))
            popup.open()

    def _connect_with_password(self, network_name: str, password: str, popup: Popup):
        popup.dismiss()
        self.connectToWifi(network_name, password)

    def connectToWifi(self, network_name, password=None):
        print(f"Attempting to connect to: {network_name}")
        if self._service_facade:
            try:
                self._service_facade.connectToWifi(network_name, password)
            except Exception as e:
                print(f"Connection failed: {e}")
                emit_event(Event(Event.EventType.ERROR, error=e, properties={"message": f"Failed to connect to {network_name}: {e}"}))
        else:
            print(f"WARNING: ServiceFacade not injected. Could not connect to {network_name}.")

    def _show_error_popup(self, message: str):
        popup_content = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
        popup_content.add_widget(Label(text=message, halign='center', valign='middle'))
        close_button = Button(text='Close', size_hint_y=None, height='40dp')
        popup_content.add_widget(close_button)
        popup = Popup(title='Connection Error', content=popup_content, size_hint=(0.7, 0.4))
        close_button.bind(on_release=popup.dismiss)
        popup.open()