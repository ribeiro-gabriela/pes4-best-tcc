import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

from ui.components import VerticalLayout
from ui.top_menu import TopMenuBar

from ui.screen1 import Screen1
from ui.screen2 import Screen2
from ui.screen3 import Screen3

from pathlib import Path
bundle_dir = Path(__file__).parent
path_to_dat = Path.cwd() / bundle_dir / Path("styling.kv")

class NavigationApp(App):
    def build(self):
        Builder.load_file(str(path_to_dat))

        layout = VerticalLayout()

        # Screen manager
        sm = ScreenManager()
        
        # Add screens
        sm.add_widget(Screen1(sm))
        sm.add_widget(Screen2(sm))
        sm.add_widget(Screen3(sm))
        
        # Menu bar
        menu_bar = TopMenuBar(sm)
        
        # Add to main layout
        layout.add_widget(menu_bar)
        layout.add_widget(sm)

        return layout

    
if __name__ == '__main__':
    NavigationApp().run()