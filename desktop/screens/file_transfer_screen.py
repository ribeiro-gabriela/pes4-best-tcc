from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp
import threading
from typing import Callable, Optional

from data.enums import ScreenName
from data.classes import File
from ui.event_router import emit_event, event_router
from data.events import Event
from services.service_facade import ServiceFacade

# [BST-332]
def check_authentication(screen_instance, action: Callable, *args, **kwargs):
    service_facade = screen_instance._service_facade
    if service_facade and service_facade.isAuthenticated():
        action(*args, **kwargs)
    else:
        emit_event(Event(Event.EventType.LOGOUT))

class FileTransferScreen(Screen):
    selected_file_text = StringProperty('No files being transferred')
    transfer_status_text = StringProperty('Waiting the start of the transfer...')
    progress_value = NumericProperty(0)
    progress_text = StringProperty('0% - Waiting...')
    transfer_in_progress = BooleanProperty(False) 
    transfer_started = BooleanProperty(False)

    _service_facade: Optional[ServiceFacade] = None
    _selected_file: Optional[File] = None
    _progress_event = None 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = ScreenName.FILE_TRANSFER.value
        event_router.register_callback(self._handle_file_preselection)

    def on_enter(self, *args):
        super().on_enter(*args)
        # self.reset_transfer_state()

        # SIMULAÇÃO
        # self._selected_file = File(
        #     fileName='firmware_v1.3.0_beta.bin',
        #     path='/simulated/path/to/firmware_v1.3.0_beta.bin'
        # )
        # self.transfer_status_text = 'Simulating connection to module: SIM-TEST-MODULE'
        # self.selected_file_text = f'Transfering file: {self._selected_file.fileName}'
        
        # [BST-332]
        # [BST-322]
        check_authentication(self, self.confirm_transfer, file_name=self._selected_file.fileName)

    def on_leave(self, *args):
        super().on_leave(*args)
        # event_router.unregister_callback(self._handle_file_preselection)
        self.cancel_transfer_internal() 
        self.reset_transfer_state() 

    def reset_transfer_state(self):
        self.selected_file_text = 'No files being transferred'
        self.transfer_status_text = 'Waiting the start of the transfer...'
        self.progress_value = 0
        self.progress_text = '0% - Waiting...'
        self.transfer_in_progress = False
        self._selected_file = None
        if self._progress_event:
            self._progress_event.cancel()
            self._progress_event = None

    def _handle_file_preselection(self, event: Event):
        if event.type == Event.EventType.LOAD_IMAGE_REQUESTED:
            # [BST-323]
            file_obj = event.properties.get('file')
            hardware_pn = event.properties.get('hardware_pn')
            
            if file_obj:
                self._selected_file = file_obj
                self.selected_file_text = f'Transferring: {file_obj.fileName}'
                self.transfer_status_text = f'Connected to the module: {hardware_pn}'
                print(f"File pre-selected for transfer: {file_obj.fileName}")
                
                self.start_transfer()

    def yes_button_clicked(self, popup: Popup):
        popup.dismiss()
        check_authentication(self, self.start_transfer)

    def start_transfer(self):
        if not self._service_facade:
            self.transfer_status_text = 'Error: Service not ready'
            return
        file = self._selected_file
        if not file:
            self.transfer_status_text = 'Error: No file selected'
            return
            
        self.transfer_in_progress = True 
        self.transfer_started = True
        self.transfer_status_text = 'Initiating transfer via ARINC 615-A...'
        self.progress_text = '0% - Starting...'
        self.progress_value = 0
        
        def transfer_thread():
            try:
                # [BST-319] 
                result = self._service_facade.startTransfer(file)
                # CÓDIGO PARA SIMULAÇÃO, REMOVER PARA TESTAR O CASO REAL 
                # result = True 
                
                if result:
                    # [BST-320]
                    self._progress_event = Clock.schedule_interval(self.update_progress, 0.5) 
                else:
                    Clock.schedule_once(lambda dt: self.transfer_finished(success=False), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.handle_transfer_error(e), 0)
                
        threading.Thread(target=transfer_thread, daemon=True).start()
        
    def update_progress(self, dt):
        if not self._service_facade or not self.transfer_in_progress:
            if self._progress_event:
                self._progress_event.cancel()
            return False 
            
        try:
            # [BST-320]
            status = self._service_facade.file_transfer_service.getProgress()
            # SIMULAÇÃO, REMOVER PARA TESTAR O CASO REAL
            
            # current_progress = self.progress_value
            # if current_progress < 100:
            #     percentage = min(current_progress + 10, 100) 
            #     if percentage == 100:
            #         status = "TransferFinished"
            #     else:
            #         status = {'percentage': percentage}
            # else:
            #     status = "TransferFinished" 

            # [BST-325]
            if isinstance(status, dict) and 'percentage' in status:
                percentage = status['percentage']
                self.progress_value = percentage
                self.progress_text = f'{percentage:.1f}% - Transferring via ARINC 615-A...'
                self.transfer_status_text = 'Transfer in progress...'

            # [BST-324]    
            elif status == "TransferFinished":
                self.transfer_finished(success=True)

            #[BST-324]     
            elif status in ["TransferFailed", "TransferCancelled"]:
                self.transfer_finished(success=False)
                return False  
                
        except Exception as e:
            # [BST-321]
            Clock.schedule_once(lambda dt: self.handle_transfer_error(e), 0)
            return False 
            
        return True 
        
    def transfer_finished(self, success: bool):
        self.transfer_in_progress = False 
        
        if self._progress_event:
            self._progress_event.cancel()
            self._progress_event = None

        # [BST-324]    
        if success:
            self.progress_value = 100
            self.progress_text = '100% - Transfer completed!'
            self.transfer_status_text = 'File successfully uploaded to the BC module.'
        else:
            self.progress_text = 'The transfer failed or was cancelled.'
            self.transfer_status_text = 'Error transferring via ARINC 615-A'
            
    def cancel_transfer_internal(self):
        if not self._service_facade or not self.transfer_in_progress:
            return
            
        try:
            self._service_facade.file_transfer_service.cancel() 
            # DESCOMENTAR PARA USAR O SERVIÇO REAL
            Clock.schedule_once(lambda dt: self.transfer_finished(success=False), 0)
        except Exception as e:
            self.handle_transfer_error(e)

    def cancel_transfer(self):
        self.cancel_transfer_internal()

    def return_clicked(self):
        # [BST-332]
        check_authentication(self, self.go_to_post_connection)

    def go_to_post_connection(self):
        # [BST-334]
        emit_event(Event(Event.EventType.NAVIGATE, properties={'target': ScreenName.POST_CONNECTION.value}))
            
    def handle_transfer_error(self, error):
        self.transfer_in_progress = False
        
        if self._progress_event:
            self._progress_event.cancel()
            self._progress_event = None
            
        self.transfer_status_text = f'Error: {str(error)}'
        self.progress_text = 'Transfer interrupted by error'
        self.progress_value = 0 
        # [BST-321]
        emit_event(Event(Event.EventType.NAVIGATE,properties={'target': ScreenName.ERROR.value,'error_message': str(error)}))

    def confirm_transfer(self, file_name: str):
        # [BST-322]
        content = BoxLayout(orientation='vertical', spacing='10dp', padding='10dp')
        content.add_widget(Label(text=f"Are you sure you want to transfer {file_name}?", halign='center', valign='middle', size_hint_y=None, height='40dp'))
        
        # [BST-319]
        buttons = BoxLayout(size_hint_y=None, height='40dp', spacing='10dp')
        btn_confirm = Button(text="Yes") 
        btn_confirm.bind(on_release=lambda x: self.yes_button_clicked(popup))
        buttons.add_widget(btn_confirm)
        
        btn_cancel = Button(text="No") 
        btn_cancel.bind(on_release=lambda x: self.transfer_not_confirmed(popup))
        buttons.add_widget(btn_cancel)
        
        content.add_widget(buttons)

        popup = Popup(title="Transfer Confirmation", content=content, size_hint=(0.7, 0.4), auto_dismiss=False)
        popup.open()

    def transfer_not_confirmed(self, popup: Popup):
        popup.dismiss()
        self.go_to_post_connection()