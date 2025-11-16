from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, StringProperty, BooleanProperty, ObjectProperty
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.metrics import dp
import shutil
import os
import platform

from data.enums import ScreenName
from data.classes import File, FileRecord
from screens.components import ImageListItem
from data.events import Event
from services.service_facade import ServiceFacade
from ui.event_router import emit_event


UPLOAD_DIR = "uploaded_files"

# [BST-332]
def check_authentication(screen_instance, action: callable, *args, **kwargs):
    service_facade = screen_instance._service_facade
    if service_facade and service_facade.isAuthenticated():
        action(*args, **kwargs)
    else:
        emit_event(Event(Event.EventType.LOGOUT))

class ImagesScreen(Screen):
    _service_facade: ServiceFacade = None
    image_files = ListProperty([]) 
    empty_list_message = StringProperty("No files saved.")
    show_empty_message = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name = ScreenName.IMAGES.value

    def on_enter(self, *args):
        print("Entered Images Screen. Loading files...")
        self.load_image_files()

    def load_image_files(self):
        # SIMULAÇÃO APENAS
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR) 

        current_files = []
        for file_name in os.listdir(UPLOAD_DIR):
            full_path = os.path.join(UPLOAD_DIR, file_name)
            if os.path.isfile(full_path):
                current_files.append({'name': file_name, 'path': full_path})

        # [BST-307]
        #current_files: List[FileRecord] = self._service_facade.listImportedFiles()
        
        self.image_files = current_files

        list_container = self.ids.image_list_container 
        list_container.clear_widgets() 

        if not self.image_files:
            self.show_empty_message = True
        else:
            self.show_empty_message = False
            for img_file in self.image_files:
                item = ImageListItem(
                    file_name=img_file['name'],
                    delete_action=self.delete_file 
                    #SIMULAÇÃO, TROCAR A LINHA COMENTADA
                    # delete_action=lambda pn=img_file.softwarePN: self.on_delete_clicked(pn)
                )
                list_container.add_widget(item)

        print(f"Loaded {len(self.image_files)} image files.")

    def open_file_chooser(self):
        # [BST-308]
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
            # [BST-332]
            check_authentication(self, self.save_file, chooser.selection[0])
        if hasattr(self, "_file_popup"):
            self._file_popup.dismiss()

    def save_file(self, file_path):
        """file_name = os.path.basename(file_path)
        file_object = File(path = file_path, fileName = file_name)
        # [BST-333]
        self._service_facade.importFile(file_object)
        self.load_image_files()"""

        # SIMULAÇÃO APENAS 
        filename = os.path.basename(file_path)
        dest_path = os.path.join(UPLOAD_DIR, filename)
        shutil.copy(file_path, dest_path)
        self.load_image_files()

    def on_delete_clicked(self, software_pn: str):
        # [BST-332]
        check_authentication(self, self.delete_file, software_pn)

    def delete_file(self, filename):
        # SIMULAÇÃO APENAS
        os.remove(os.path.join(UPLOAD_DIR, filename))
        #self._service_facade.deleteImportedFile(software_pn)
        self.load_image_files()
