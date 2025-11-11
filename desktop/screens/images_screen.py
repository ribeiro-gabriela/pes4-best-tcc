from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp
import shutil
import os
import platform

from data.enums import ScreenName
from screens.actions import action_go_to_screen, action_show_help
from screens.components import ScreenLayout, TitleLabel, PrimaryButton, SecondaryButton, HelpButton

UPLOAD_DIR = "uploads"

class ImagesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name = ScreenName.IMAGES.value

        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        self.layout = ScreenLayout(orientation='vertical')
        self.layout.add_widget(TitleLabel(text=f'{self.name} screen'))

        btn_back = SecondaryButton(text=f'Back to {ScreenName.MAIN.value}')
        btn_back.on_press = action_go_to_screen(ScreenName.MAIN)
        self.layout.add_widget(btn_back)

        btn_upload = PrimaryButton(text='Upload')
        btn_upload.bind(on_press=self.open_file_chooser) 
        self.layout.add_widget(btn_upload)

        self.files_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.files_box.bind(minimum_height=self.files_box.setter('height')) 
        scroll = ScrollView()
        scroll.add_widget(self.files_box)
        self.layout.add_widget(scroll)

        self.refresh_file_list()
        
        root_layout = FloatLayout()
        root_layout.add_widget(self.layout)
        
        help_button = HelpButton(text="Help")
        help_button.size_hint = (None, None)
        help_button.size = (dp(100), dp(50))
        help_button.pos_hint = {'right': 0.98, 'bottom': 0.02}
        help_button.on_press = action_show_help()
        root_layout.add_widget(help_button)
        
        self.add_widget(root_layout)

    def open_file_chooser(self, instance):
        if platform.system() == "Windows":
            start_path = "C:\\"
        else:
            start_path = os.path.expanduser("~") 

        chooser = FileChooserListView(path=start_path, filters=['*.*'])

        btn_back_folder = Button(text="Return", size_hint_y=None, height=40)
        btn_back_folder.bind(on_press=lambda btn: self.go_back_folder(chooser)) 

        btn_upload_file = Button(text="Upload", size_hint_y=None, height=40)
        btn_upload_file.bind(on_press=lambda btn: self.on_upload_clicked(chooser)) 

        btn_row = BoxLayout(size_hint_y=None, height=40)
        btn_row.add_widget(btn_back_folder)
        btn_row.add_widget(btn_upload_file)

        layout = BoxLayout(orientation="vertical")
        layout.add_widget(chooser)
        layout.add_widget(btn_row)

        popup = Popup(title="Select a file", content=layout, size_hint=(0.9, 0.9))
        self._file_popup = popup  
        self._file_chooser = chooser 
        popup.open()

    def go_back_folder(self, chooser):
        parent_dir = os.path.dirname(chooser.path)
        if os.path.exists(parent_dir) and parent_dir != chooser.path:
            chooser.path = parent_dir

    def on_upload_clicked(self, chooser):
        if chooser.selection:
            self.save_file(chooser.selection[0])
        if hasattr(self, "_file_popup"):
            self._file_popup.dismiss()

    def save_file(self, file_path):
        filename = os.path.basename(file_path)
        dest_path = os.path.join(UPLOAD_DIR, filename)
        shutil.copy(file_path, dest_path)
        self.refresh_file_list()

    def refresh_file_list(self):
        self.files_box.clear_widgets()
        for filename in os.listdir(UPLOAD_DIR):
            file_row = BoxLayout(size_hint_y=None, height=40)
            file_row.add_widget(Label(text=filename))
            btn_delete = Button(text="Delete", size_hint_x=None, width=100)
            btn_delete.bind(on_press=lambda inst, f=filename: self.delete_file(f)) 
            file_row.add_widget(btn_delete)
            self.files_box.add_widget(file_row)

    def delete_file(self, filename):
        os.remove(os.path.join(UPLOAD_DIR, filename))
        self.refresh_file_list()
