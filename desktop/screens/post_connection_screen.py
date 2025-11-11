from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty, ListProperty, BooleanProperty
from kivy.metrics import dp
from kivy.clock import Clock

from data.enums import ScreenName
from screens.components import SystemImageItem, NormalLabel, HelpButton
from screens.actions import action_show_help
from ui.event_router import emit_event, event_router
from data.events import Event
from services.service_facade import ServiceFacade 
from typing import Optional, Dict, Any, List

class PostConnectionScreen(Screen):
    _service_facade: ServiceFacade = None 
    
    hardware_pn = StringProperty('N/A')
    
    image_list_container: Optional[BoxLayout] = None
    
    selected_image_item: Optional[SystemImageItem] = ObjectProperty(None, allownone=True)
    
    def __init__(self, **kwargs):
        
        super().__init__(**kwargs)
        self.name = ScreenName.POST_CONNECTION.value
        event_router.register_callback(self._handle_event)
        self._all_images_data: List[Dict[str, Any]] = []

    def _is_test_mode(self) -> bool:
        return str(self.hardware_pn).startswith("HW-PN-TEST")
    
    def on_kv_post(self, base_widget):
        self.image_list_container = self.ids.get('image_list_container')
        print("KV posted; PostConnectionScreen ids:", list(self.ids.keys()))
        if not self.image_list_container:
            print("ERROR: id 'image_list_container' is NOT in the <PostConnectionScreen> of the KV")

    def _on_item_released(self, item):
        if item.state == 'down':
            self.selected_image_item = item
            print(f"[UI] Selected: {item.image_name}")
        else:
            if self.selected_image_item is item:
                self.selected_image_item = None
            print(f"[UI] Deselected: {item.image_name}")


    def _bind_kv_elements(self, instance, value):
        if 'image_list_container' in self.ids and self.ids.image_list_container:
            self.image_list_container = self.ids.image_list_container
        else:
            print("ERROR: BoxLayout with id 'image_list_container' not found in PostConnectionScreen KV.")


    def on_enter(self, *args):
        print("Entering PostConnectionScreen.")
        self.selected_image_item = None 
        
        if self.image_list_container:
            self.image_list_container.clear_widgets()
            self.image_list_container.add_widget(NormalLabel(text="Looking for information on Module BC...", size_hint_y=None, height=dp(30)))

        Clock.schedule_once(lambda dt: self._load_module_info_and_images(), 0)
        
    def _load_module_info_and_images(self):
        if not self._service_facade:
            print("ServiceFacade not set in PostConnectionScreen. Cannot load module info.")
            if self.image_list_container:
                self.image_list_container.clear_widgets()
                self.image_list_container.add_widget(NormalLabel(text="Services unavailable. Please reload the screen.", halign='center'))
            return

        try:
            self.hardware_pn = self._service_facade.connection_service.getConnectionHardwarePN()
            print(f"Hardware PN received: {self.hardware_pn}")

            self._load_compatible_images(use_test_data_on_error=self._is_test_mode())

        except Exception as e:
            print(f"Error getting hardware PN or loading images: {e}")
            if self.image_list_container:
                self.image_list_container.clear_widgets()
                self.image_list_container.add_widget(NormalLabel(text=f"Error retrieving information from the module.: {e}", halign='center'))
            
            if self.hardware_pn == 'N/A' or not self.hardware_pn:
                self.hardware_pn = "BCM_TEST_PN"
                self._load_compatible_images(use_test_data_on_error=True)

    def _load_compatible_images(self, use_test_data_on_error: bool = False):
        if not self.image_list_container:
            print("image_list_container not initialized.")
            return

        self.image_list_container.clear_widgets()
        self.image_list_container.add_widget(
            NormalLabel(text="Searching for compatible images...", size_hint_y=None, height=dp(30))
        )

        try:
            # [BST-314] 
            file_records = self._service_facade.listImportedFilesFiltered(self.hardware_pn)
            self._all_images_data = []
            for record in file_records:
                self._all_images_data.append({
                    'name': record.file.fileName,
                    'compatible': True, 
                    'record': record 
                })
            print(f"Filtered images received for {self.hardware_pn}: {len(self._all_images_data)} images")

            using_test_data = False
            if not self._all_images_data and (use_test_data_on_error or self._is_test_mode()):
                print("No real images found; displaying test data.")
                self._all_images_data = [
                    {'name': 'Firmware_BC_1.2.0.bin', 'compatible': True},
                    {'name': 'Firmware_BC_1.1.0_old.bin', 'compatible': False},
                    {'name': 'Firmware_BC_1.3.0_beta.bin', 'compatible': True},
                    {'name': 'Config_File_v2.cfg', 'compatible': True},
                    {'name': 'Log_Viewer_Tool.exe', 'compatible': False},
                    {'name': 'Another_Firmware_BC_1.4.0.bin', 'compatible': True},
                    {'name': 'Test_Image_001.img', 'compatible': True},
                    {'name': 'Old_Image_v1.img', 'compatible': False},
                    {'name': 'Firmware_BC_2.0.0.bin', 'compatible': True},
                    {'name': 'Backup_2023.zip', 'compatible': False},
                    {'name': 'My_Custom_Script.py', 'compatible': False},
                    {'name': 'Final_Release_1.5.0.bin', 'compatible': True},
                ]
                using_test_data = True


            self.image_list_container.clear_widgets() 

            if using_test_data:
                self.image_list_container.add_widget(NormalLabel(text="(Test Data)", halign='center'))
                self.image_list_container.add_widget(Label(size_hint_y=None, height=dp(5)))

            if not self._all_images_data:
                self.image_list_container.add_widget(
                    NormalLabel(text="No compatible images found.", halign='center')
                )
                return

            compatible_items = [d for d in self._all_images_data if d.get('compatible')]

            if not compatible_items:
                self.image_list_container.add_widget(
                    NormalLabel(text="No compatible images found.", halign='center')
                )
            else:
                for img_data in compatible_items:
                    item = SystemImageItem(
                        image_name=img_data['name'],
                        is_compatible=True,
                        on_selection=self.on_image_item_selected
                    )
                    item.allow_no_selection = True
                    item.bind(on_release=self._on_item_released)
                    self.image_list_container.add_widget(item)


        except Exception as e:
            print(f"Error loading compatible images: {e}")
            self.image_list_container.clear_widgets()
            self.image_list_container.add_widget(
                NormalLabel(text=f"Error loading images: {e}", halign='center')
            )


    def on_image_item_selected(self, selected_item: SystemImageItem):
        if selected_item.state == 'down': 
            self.selected_image_item = selected_item
            print(f"Selected image: {self.selected_image_item.image_name}, Compatible: {self.selected_image_item.is_compatible}")
        else: 
            if self.selected_image_item == selected_item: 
                self.selected_image_item = None
                print("Image deselected.")

    def load_selected_image(self):
        if self.selected_image_item and self.selected_image_item.is_compatible:
            image_name_to_load = self.selected_image_item.image_name
            print(f"Attempting to load image: {image_name_to_load}")
            
            selected_record = None
            for img_data in self._all_images_data:
                if img_data['name'] == image_name_to_load:
                    selected_record = img_data.get('record')
                    break
            
            if selected_record:
                try:
                    emit_event(Event(Event.EventType.NAVIGATE, properties={'target': ScreenName.FILE_TRANSFER.value}))
                    
                    emit_event(Event(Event.EventType.LOAD_IMAGE_REQUESTED, properties={
                        'file': selected_record.file,
                        'hardware_pn': self.hardware_pn
                    }))
                    
                except Exception as e:
                    print(f"Error preparing file for transfer: {e}")
                    self._show_error_popup(f"Error preparing file for transfer: {e}")
            else:
                self._show_error_popup("It was not possible to prepare the file for transfer.")
        else:
            print("No compatible image selected to load or selected image is incompatible.")
            self._show_error_popup("Please select a *compatible* image to upload..")

    def request_disconnect_confirmation(self):
        print("Requesting disconnect confirmation...")
        content = BoxLayout(orientation='vertical', spacing='10dp', padding='10dp')
        content.add_widget(Label(text="Are you sure you want to disconnect from the BC Module?", halign='center', valign='middle', size_hint_y=None, height='40dp'))
        
        buttons = BoxLayout(size_hint_y=None, height='40dp', spacing='10dp')
        btn_confirm = Button(text="Yes", background_color=(0.2, 0.7, 0.3, 1)) 
        btn_confirm.bind(on_release=lambda x: self._confirm_disconnect(popup))
        buttons.add_widget(btn_confirm)
        
        btn_cancel = Button(text="No", background_color=(0.9, 0.5, 0.1, 1)) 
        btn_cancel.bind(on_release=lambda x: popup.dismiss())
        buttons.add_widget(btn_cancel)
        
        content.add_widget(buttons)

        popup = Popup(title="Disconnection Confirmation", content=content, size_hint=(0.7, 0.4), auto_dismiss=False)
        popup.open()

    def _confirm_disconnect(self, popup: Popup):
        popup.dismiss()
        print("Disconnect confirmed. Disconnecting from Módulo BC...")
        if self._service_facade:
            try:
                self._service_facade.connection_service.disconnect()
                print("Disconnected successfully. Navigating to Main screen.")
                emit_event(Event(Event.EventType.NAVIGATE, properties={'target': ScreenName.MAIN.value}))
            except Exception as e:
                print(f"Error during disconnection: {e}")
                self._show_error_popup(f"Error during disconnection: {e}")
        else:
            print("ServiceFacade not set. Cannot disconnect.")
            self._show_error_popup("Services are unavailable. Disconnection was not possible.")

    def _show_error_popup(self, message: str, title: str = 'Error'):
        popup_content = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
        popup_content.add_widget(Label(text=message, halign='center', valign='middle'))
        close_button = Button(text='Fechar', size_hint_y=None, height='40dp')
        popup_content.add_widget(close_button)
        popup = Popup(title=title, content=popup_content, size_hint=(0.7, 0.4))
        close_button.bind(on_release=popup.dismiss)
        popup.open()

    def _handle_event(self, event: Event) -> None:
        pass

    def show_help(self):
        action_show_help()()
