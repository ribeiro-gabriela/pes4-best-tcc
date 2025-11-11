from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.metrics import dp
import threading
from typing import Optional

from data.enums import ScreenName
from data.classes import File
from screens.actions import action_go_to_screen, action_show_help
from screens.components import ScreenLayout, TitleLabel, SecondaryButton, HelpButton
from ui.event_router import emit_event, event_router
from data.events import Event
from services.service_facade import ServiceFacade

class FileTransferScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.name = ScreenName.FILE_TRANSFER.value
        self._service_facade: Optional[ServiceFacade] = None
        self.selected_file: Optional[File] = None
        self.transfer_in_progress = False
        self.progress_event = None
        
        self._create_layout()
        
    def _create_layout(self):
        self.layout = ScreenLayout(orientation='vertical')
        self.layout.add_widget(TitleLabel(text='Loading Status'))
        
        btn_back = SecondaryButton(text='Return to Post-Connection')
        btn_back.on_press = action_go_to_screen(ScreenName.POST_CONNECTION)
        self.layout.add_widget(btn_back)
        
        self.selected_file_label = Label(
            text='No files being transferred',
            size_hint_y=None,
            height=40
        )
        self.layout.add_widget(self.selected_file_label)
        
        self.transfer_status_label = Label(
            text='Waiting the start of the transfer...',
            size_hint_y=None,
            height=40
        )
        self.layout.add_widget(self.transfer_status_label)
        
        self.progress_bar = ProgressBar(
            value=0,
            max=100,
            size_hint_y=None,
            height=30
        )
        self.layout.add_widget(self.progress_bar)
        
        self.progress_label = Label(
            text='0% - Waiting...',
            size_hint_y=None,
            height=40
        )
        self.layout.add_widget(self.progress_label)
        
        self.btn_cancel_transfer = SecondaryButton(text='Cancel Transfer')
        self.btn_cancel_transfer.bind(on_press=self.cancel_transfer)
        self.btn_cancel_transfer.disabled = True
        self.layout.add_widget(self.btn_cancel_transfer)
        
        root_layout = FloatLayout()
        root_layout.add_widget(self.layout)

        help_button = HelpButton(text="Help")
        help_button.size_hint = (None, None)
        help_button.size = (dp(100), dp(50))
        help_button.pos_hint = {'right': 0.98, 'bottom': 0.02}
        help_button.on_press = action_show_help()
        root_layout.add_widget(help_button)
        
        self.add_widget(root_layout)
        
    def on_enter(self):
        super().on_enter()
        event_router.register_callback(self._handle_file_preselection)
        
    def _handle_file_preselection(self, event: Event):
        if event.type == Event.EventType.LOAD_IMAGE_REQUESTED:
            file_obj = event.properties.get('file')
            hardware_pn = event.properties.get('hardware_pn')
            
            if file_obj:
                self.selected_file = file_obj
                self.selected_file_label.text = f'Transferring: {file_obj.fileName}'
                self.transfer_status_label.text = f'Connected to the module: {hardware_pn}'
                print(f"File pre-selected for transfer: {file_obj.fileName}")
                
                self.start_transfer()
        
    def start_transfer(self):
        if not self.selected_file or not self._service_facade:
            return
            
        self.transfer_in_progress = True
        self.btn_cancel_transfer.disabled = False
        self.transfer_status_label.text = 'Initiating transfer via ARINC 615-A...'
        self.progress_label.text = '0% - Starting...'
        self.progress_bar.value = 0
        
        def transfer_thread():
            try:
                # [BST-319] 
                result = self._service_facade.file_transfer_service.startTransfer(self.selected_file)
                
                if result:
                    self.progress_event = Clock.schedule_interval(self.update_progress, 2.0) 
                    
            except Exception as e:
                Clock.schedule_once(lambda dt: self.handle_transfer_error(e), 0)
                
        threading.Thread(target=transfer_thread, daemon=True).start()
        
    def update_progress(self, dt):
        if not self._service_facade or not self.transfer_in_progress:
            return False
            
        try:
            status = self._service_facade.file_transfer_service.getProgress()
            
            if isinstance(status, dict) and 'percentage' in status:
                percentage = status['percentage']
                self.progress_bar.value = percentage
                self.progress_label.text = f'{percentage:.1f}% - Transferring via ARINC 615-A...'
                self.transfer_status_label.text = 'Transfer in progress...'
                
            elif status == "TransferFinished":
                self.transfer_finished(success=True)
                return False  
                
            elif status in ["TransferFailed", "TransferCancelled"]:
                self.transfer_finished(success=False)
                return False  
                
        except Exception as e:
            Clock.schedule_once(lambda dt: self.handle_transfer_error(e), 0)
            return False
            
        return True 
        
    def transfer_finished(self, success: bool):
        self.transfer_in_progress = False
        self.btn_cancel_transfer.disabled = True
        
        if self.progress_event:
            self.progress_event.cancel()
            self.progress_event = None
            
        if success:
            self.progress_bar.value = 100
            self.progress_label.text = '100% - Transfer completed!'
            self.transfer_status_label.text = 'File successfully uploaded to the BC module.'
        else:
            self.progress_label.text = 'The transfer failed or was cancelled.'
            self.transfer_status_label.text = 'Error transferring via ARINC 615-A'
            
    def cancel_transfer(self, instance):
        if not self._service_facade or not self.transfer_in_progress:
            return
            
        try:
            self._service_facade.file_transfer_service.cancel()
            self.transfer_status_label.text = 'Canceling transfer...'
            self.progress_label.text = 'Canceling...'
        except Exception as e:
            self.handle_transfer_error(e)
            
    def handle_transfer_error(self, error):
        self.transfer_in_progress = False
        self.btn_cancel_transfer.disabled = True
        
        if self.progress_event:
            self.progress_event.cancel()
            self.progress_event = None
            
        self.transfer_status_label.text = f'Erro: {str(error)}'
        self.progress_label.text = 'Transfer interrupted by error'
        
        emit_event(Event(
            Event.EventType.NAVIGATE,
            properties={
                'target': ScreenName.ERROR.value,
                'error_message': str(error)
            }
        ))