from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen

from custom_types.screens import ScreenName
from ui.actions import action_go_to_screen
from ui.components import (
    CompactLayout,
    HorizontalLayout,
    TableLayout,
    TitleLabel,
    HeaderLabel,
    WifiLabel,
    ConnectButton,
    SecondaryButton,
)
from services.service_facade import get_wifi_connections


class ConnectionScreen(Screen):
    def __init__(self):
        super().__init__()

        self.name = ScreenName.CONNECTION.value

        main_layout = CompactLayout()

        first_row = HorizontalLayout(size_hint_y=None, height=60)

        title_label = TitleLabel(text="WiFi Connections", font_size=20)
        first_row.add_widget(title_label)

        btn_back = SecondaryButton(
            text=f"Back to {ScreenName.MAIN.value}", font_size=16
        )
        btn_back.on_press = action_go_to_screen(ScreenName.MAIN)
        first_row.add_widget(btn_back)
        
        main_layout.add_widget(first_row)

        second_row = ScrollView()

        self.wifi_table = TableLayout()
        second_row.add_widget(self.wifi_table)

        main_layout.add_widget(second_row)

        self.add_widget(main_layout)

        self.load_wifi_connections()

    def load_wifi_connections(self):
        wifi_table = self.wifi_table
        wifi_table.clear_widgets()

        wifi_connections = get_wifi_connections()

        header_ssid = HeaderLabel(text="SSID")
        wifi_table.add_widget(header_ssid)

        header_action = HeaderLabel(text="Action")
        wifi_table.add_widget(header_action)

        for conn in wifi_connections:
            ssid, info = conn["ssid"], conn["info"]

            ssid_text = (
                f"{ssid}\nSignal: {info['signal']} | Security: {info['security']}"
            )
            ssid_label = WifiLabel(text=ssid_text)
            wifi_table.add_widget(ssid_label)

            connect_btn = ConnectButton(text="Connect")
            connect_btn.on_press = lambda: self.connect_to_wifi(ssid)
            wifi_table.add_widget(connect_btn)

    def connect_to_wifi(self, network_name):
        print(f"Attempting to connect to: {network_name}")
