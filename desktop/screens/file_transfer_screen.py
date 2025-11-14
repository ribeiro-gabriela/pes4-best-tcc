from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.metrics import dp
import threading
from typing import Optional

from data.enums import ScreenName
from data.classes import File
from screens.actions import action_go_to_screen, action_show_help 
from ui.event_router import emit_event, event_router
from data.events import Event
from services.service_facade import ServiceFacade

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

    def on_enter(self):
        super().on_enter()
        event_router.register_callback(self._handle_file_preselection)
        self.reset_transfer_state()

        self._selected_file = File(
            fileName='firmware_v1.3.0_beta.bin',
            path='/simulated/path/to/firmware_v1.3.0_beta.bin'
        )
        self.transfer_status_text = 'Simulating connection to module: SIM-TEST-MODULE'
        self.selected_file_text = f'Transferring: {self._selected_file.fileName}'
        
        self.start_transfer()

    def on_leave(self):
        super().on_leave()
        event_router.unregister_callback(self._handle_file_preselection)
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
            file_obj = event.properties.get('file')
            hardware_pn = event.properties.get('hardware_pn')
            
            if file_obj:
                self._selected_file = file_obj
                self.selected_file_text = f'Transferring: {file_obj.fileName}'
                self.transfer_status_text = f'Connected to the module: {hardware_pn}'
                print(f"File pre-selected for transfer: {file_obj.fileName}")
                
                self.start_transfer()
        
    def start_transfer(self):
        if not self._selected_file or not self._service_facade:
            self.transfer_status_text = 'Error: No file selected or service not ready.'
            return
            
        self.transfer_in_progress = True 
        self.transfer_started = True
        self.transfer_status_text = 'Initiating transfer via ARINC 615-A...'
        self.progress_text = '0% - Starting...'
        self.progress_value = 0
        
        def transfer_thread():
            try:
                # [BST-319] 
                #result = self._service_facade.file_transfer_service.startTransfer(self._selected_file)
                # CÓDIGO PARA SIMULAÇÃO, REMOVER PARA TESTAR O CASO REAL 
                result = True 
                
                if result:
                    self._progress_event = Clock.schedule_interval(self.update_progress, 2.0) 
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
            # status = self._service_facade.file_transfer_service.getProgress()
            # SIMULAÇÃO, REMOVER PARA TESTAR O CASO REAL
            
            current_progress = self.progress_value
            if current_progress < 100:
                percentage = min(current_progress + 10, 100) 
                if percentage == 100:
                    status = "TransferFinished"
                else:
                    status = {'percentage': percentage}
            else:
                status = "TransferFinished" 

            if isinstance(status, dict) and 'percentage' in status:
                percentage = status['percentage']
                self.progress_value = percentage
                self.progress_text = f'{percentage:.1f}% - Transferring via ARINC 615-A...'
                self.transfer_status_text = 'Transfer in progress...'
                
            elif status == "TransferFinished":
                self.transfer_finished(success=True)
                
            elif status in ["TransferFailed", "TransferCancelled"]:
                self.transfer_finished(success=False)
                return False  
                
        except Exception as e:
            Clock.schedule_once(lambda dt: self.handle_transfer_error(e), 0)
            return False 
            
        return True 
        
    def transfer_finished(self, success: bool):
        self.transfer_in_progress = False 
        
        if self._progress_event:
            self._progress_event.cancel()
            self._progress_event = None
            
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
            # self._service_facade.file_transfer_service.cancel() 
            # DESCOMENTAR PARA USAR O SERVIÇO REAL
            Clock.schedule_once(lambda dt: self.transfer_finished(success=False), 0)
        except Exception as e:
            self.handle_transfer_error(e)

    def cancel_transfer(self):
        self.cancel_transfer_internal()

    def go_to_post_connection(self):
        action_go_to_screen(ScreenName.POST_CONNECTION)()
            
    def handle_transfer_error(self, error):
        self.transfer_in_progress = False
        
        if self._progress_event:
            self._progress_event.cancel()
            self._progress_event = None
            
        self.transfer_status_text = f'Error: {str(error)}'
        self.progress_text = 'Transfer interrupted by error'
        self.progress_value = 0 

        emit_event(Event(Event.EventType.NAVIGATE,properties={'target': ScreenName.ERROR.value,'error_message': str(error)}))