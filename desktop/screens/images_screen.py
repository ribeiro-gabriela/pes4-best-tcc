from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
import shutil
import os
import platform

from data.enums import ScreenName
from screens.actions import action_go_to_screen
from screens.components import ScreenLayout, TitleLabel, PrimaryButton, SecondaryButton

UPLOAD_DIR = "uploads"

class ImagesScreen(Screen):
    def __init__(self):
        super().__init__()

        self.name = ScreenName.IMAGES.value

        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        self.layout = ScreenLayout(orientation='vertical')
        self.layout.add_widget(TitleLabel(text=f'{self.name} screen'))

        btn_back = SecondaryButton(text=f'Back to {ScreenName.MAIN.value}')
        btn_back.on_press = action_go_to_screen(ScreenName.MAIN)
        self.layout.add_widget(btn_back)

        btn_upload = PrimaryButton(text='Upload')
        btn_upload.bind(on_press=self.open_file_chooser) # pyright: ignore[reportAttributeAccessIssue]
        self.layout.add_widget(btn_upload)

        # Lista de arquivos
        self.files_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.files_box.bind(minimum_height=self.files_box.setter('height')) # pyright: ignore[reportAttributeAccessIssue]
        scroll = ScrollView()
        scroll.add_widget(self.files_box)
        self.layout.add_widget(scroll)

        self.refresh_file_list()
        self.add_widget(self.layout)

    def open_file_chooser(self, instance):
        # Detecta SO e escolhe ponto inicial
        if platform.system() == "Windows":
            start_path = "C:\\"
        else:
            start_path = os.path.expanduser("~")  # macOS/Linux

        chooser = FileChooserListView(path=start_path, filters=['*.*'])

        # Botão Voltar pasta
        btn_back_folder = Button(text="Voltar", size_hint_y=None, height=40)
        btn_back_folder.bind(on_press=lambda btn: self.go_back_folder(chooser)) # pyright: ignore[reportAttributeAccessIssue]

        # Botão Upload
        btn_upload_file = Button(text="Upload", size_hint_y=None, height=40)
        btn_upload_file.bind(on_press=lambda btn: self.on_upload_clicked(chooser)) # pyright: ignore[reportAttributeAccessIssue]

        # Layout para botões
        btn_row = BoxLayout(size_hint_y=None, height=40)
        btn_row.add_widget(btn_back_folder)
        btn_row.add_widget(btn_upload_file)

        # Layout principal
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(chooser)
        layout.add_widget(btn_row)

        popup = Popup(title="Select a file", content=layout, size_hint=(0.9, 0.9))
        self._file_popup = popup  # guardar para fechar depois
        self._file_chooser = chooser  # guardar para usar no upload
        popup.open()

    def go_back_folder(self, chooser):
        """Volta para a pasta anterior no FileChooser."""
        parent_dir = os.path.dirname(chooser.path)
        if os.path.exists(parent_dir) and parent_dir != chooser.path:
            chooser.path = parent_dir

    def on_upload_clicked(self, chooser):
        """Confirma upload do arquivo selecionado."""
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
            btn_delete.bind(on_press=lambda inst, f=filename: self.delete_file(f)) # pyright: ignore[reportAttributeAccessIssue]
            file_row.add_widget(btn_delete)
            self.files_box.add_widget(file_row)

    def delete_file(self, filename):
        os.remove(os.path.join(UPLOAD_DIR, filename))
        self.refresh_file_list()
