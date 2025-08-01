from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen

from ui.components import CompactLayout, HorizontalLayout, TableLayout, TitleLabel, HeaderLabel, WifiLabel, ConnectButton, SecondaryButton
from services.service_facade import get_wifi_connections

class Screen3(Screen):
    def __init__(self, screen_manager: ScreenManager, **kwargs):
        super().__init__(**kwargs)

        self.screen_manager = screen_manager        

        self.name = 'screen3'
        
        main_layout = CompactLayout()
        
        # Title and back button
        top_layout = HorizontalLayout(size_hint_y = None, height=60)
        
        title_label = TitleLabel(text='WiFi Connections', font_size=20)
        top_layout.add_widget(title_label)

        
        btn_back = SecondaryButton(text='Back to Screen 1', font_size=16)
        btn_back.on_press = self.go_to_screen1
        top_layout.add_widget(btn_back)
        
        # WiFi table
        scroll = ScrollView()

        self.wifi_table = TableLayout()
        
        scroll.add_widget(self.wifi_table)
        
        # add components to screen layout
        main_layout.add_widget(top_layout)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        
        # Load WiFi connections after the widget is built
        self.load_wifi_connections()
    
    def go_to_screen1(self):
        self.screen_manager.current = 'screen1'
  
    def load_wifi_connections(self):
        """Load WiFi connections into the table"""
        wifi_table = self.wifi_table
        wifi_table.clear_widgets()
        
        wifi_connections = get_wifi_connections()
        
        # Add headers
        header_ssid = HeaderLabel(text='SSID')
        wifi_table.add_widget(header_ssid)
        
        header_action = HeaderLabel(text='Action')
        wifi_table.add_widget(header_action)
        
        # Add WiFi connections
        for conn in wifi_connections:
            ssid, info = conn["ssid"], conn["info"] 

            # SSID label with signal info
            ssid_text = f"{ssid}\nSignal: {info['signal']} | Security: {info['security']}"
            ssid_label = WifiLabel(text=ssid_text)
            wifi_table.add_widget(ssid_label)
            
            # Connect button
            connect_btn = ConnectButton(text='Connect')
            connect_btn.on_press = lambda: self.connect_to_wifi(ssid)
            wifi_table.add_widget(connect_btn)
    
    def connect_to_wifi(self, network_name):
        """Handle WiFi connection"""
        print(f"Attempting to connect to: {network_name}")