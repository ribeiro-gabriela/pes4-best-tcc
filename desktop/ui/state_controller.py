from data.enums import ScreenName
from data.events import Event
from services.logging_service import LoggingService
from ui.event_router import EventRouter
from ui.screen_manager import ScreenManager

from enum import Enum

class AppState(Enum):
    LOGIN = 'Login'
    MAIN = 'Main'
    CONNECTION = 'Connection'
    IMAGES = 'Images'
    POST_CONNECTION = 'PostConnection'
    LOADING = 'Loading'
    ERROR = 'Error'

    
class StateController:
    def __init__(self, event_router: EventRouter, screen_manager: ScreenManager):
        self.logging_service = LoggingService(StateController.__name__)
        self.current_state = AppState.LOGIN
        self.previous_state = AppState.LOGIN
        self.event_router = event_router
        self.screen_manager = screen_manager
        
        self.event_router.register_callback(self.print_event)
        self.event_router.register_callback(self.route_navigation_event)
        self.event_router.register_callback(self.process_event)

    # REMOVER
    def print_event(self, event :Event) -> None:
        print(event)

    # REMOVER
    def route_navigation_event(self,event :Event) -> None:
        if event.type != Event.EventType.NAVIGATE:
            return
        
        if not event.properties:
            raise Exception("Navigation error: missing target screen name on event properties")
        
        target = event.properties.get("target", "")

        try:
            self.screen_manager.navigate(target)
        except Exception as e:
            raise Exception("Navigation error") from e
        
    def process_event(self, event: Event) -> None:
        match self.current_state:
            case AppState.LOGIN:
                self._handle_login_state(event)
            case AppState.MAIN:
                self._handle_main_state(event)
            case AppState.CONNECTION:
                self._handle_connection_state(event)
            case AppState.IMAGES:
                self._handle_images_state(event)
            case AppState.POST_CONNECTION:
                self._handle_post_connection_state(event)
            case AppState.LOADING:
                self._handle_loading_state(event)
            case AppState.ERROR:
                self._handle_error_state(event)

    def _handle_login_state(self, event: Event) -> None:
        match event.type:
            case 'LOGIN_SUCCESS':
                # [E1] Login > Main
                self._transition_to(AppState.MAIN)
            case 'LOGIN_FAILURE':
                # [E2] Login > Erro
                self._transition_to_error()
            case _:
                self._handle_global_events(event)

    def _handle_main_state(self, event: Event) -> None:
        match event.type:
            case 'NAVIGATE_TO_CONNECTION':
                # [E5] Principal > Conexao
                self._transition_to(AppState.CONNECTION)
            case 'NAVIGATE_TO_IMAGES':
                # [E6] Principal > Imagens
                self._transition_to(AppState.IMAGES)
            case 'LOGOUT':
                # [E3] Logado > Login
                self._transition_to(AppState.LOGIN)
            case 'SESSION_INVALIDATED':
                # [E4] Logado > Login
                self._transition_to(AppState.LOGIN)
            case _:
                self._handle_global_events(event)

    def _handle_connection_state(self, event: Event) -> None:
        match event.type:
            case 'BACK' | 'CANCEL':
                # [E7] Conexao > Principal
                self._transition_to(AppState.MAIN)
            case 'CONNECTION_SUCCESS':
                # [E9] Conexao > PosConexao
                # [BST-311]
                self._transition_to(AppState.POST_CONNECTION)
            case 'LOGOUT':
                # [E3] Logado > Login
                self._transition_to(AppState.LOGIN)
            case 'SESSION_INVALIDATED':
                # [E4] Logado > Login
                self._transition_to(AppState.LOGIN)
            case _:
                self._handle_global_events(event)

    def _handle_images_state(self, event: Event) -> None:
        match event.type:
            case 'BACK':
                # [E8] Imagens > Principal
                self._transition_to(AppState.MAIN)
            case 'LOGOUT':
                # [E3] Logado > Login
                self._transition_to(AppState.LOGIN)
            case 'SESSION_INVALIDATED':
                # [E4] Logado > Login
                self._transition_to(AppState.LOGIN)
            case _:
                self._handle_global_events(event)

    def _handle_post_connection_state(self, event: Event) -> None:
        match event.type:
            case 'DISCONNECT':
                # [E10] PosConexao > Principal
                # [BST-317]
                self._transition_to(AppState.MAIN)
            case 'BACK':
                # [E11] PosConexao > Imagens
                self._transition_to(AppState.IMAGES)
            case 'START_LOADING':
                # [E12] PosConexao > Carregamento
                # [BST-318]
                self._transition_to(AppState.LOADING)
            case 'LOGOUT':
                # [E3] Logado > Login
                self._transition_to(AppState.LOGIN)
            case 'SESSION_INVALIDATED':
                # [E4] Logado > Login
                self._transition_to(AppState.LOGIN)
            case _:
                self._handle_global_events(event)

    def _handle_loading_state(self, event: Event) -> None:
        match event.type:
            case 'LOADING_COMPLETE':
                # [E13] Carregamento > PosConexao
                # [BST-334]
                self._transition_to(AppState.POST_CONNECTION)
            case 'LOGOUT':
                # [E3] Logado > Login
                self._transition_to(AppState.LOGIN)
            case 'SESSION_INVALIDATED':
                # [E4] Logado > Login
                self._transition_to(AppState.LOGIN)
            case _:
                self._handle_global_events(event)

    def _handle_error_state(self, event: Event) -> None:
        match event.type:
            case 'DISMISS_ERROR':
                # [E15] Erro > App (Anterior)
                self._transition_to(self.previous_state)
            case _:
                pass

    def _handle_global_events(self, event: Event) -> None:
        match event.type:
            case 'ERROR':
                # [E14] App (Qualquer) > Erro
                self._transition_to_error(event)

    def _transition_to(self, new_state: AppState) -> None:
        self.previous_state = self.current_state
        self.current_state = new_state
        self.screen_manager.navigate(self._map_state_to_screen(new_state))

    def _transition_to_error(self, event: Event) -> None:
        self.current_state = AppState.ERROR
        # [BST-335]
        if event.error:
            self.logging_service.error(f'Transition to Error state from {self.previous_state.value}', event.error)
        self.screen_manager.navigate(ScreenName.ERROR)

    def _map_state_to_screen(self, state: AppState) -> ScreenName:
        match state:
            case AppState.LOGIN:
                return ScreenName.LOGIN
            case AppState.MAIN:
                return ScreenName.MAIN
            case AppState.CONNECTION:
                return ScreenName.CONNECTION
            case AppState.IMAGES:
                return ScreenName.IMAGES
            case AppState.POST_CONNECTION:
                return ScreenName.POST_CONNECTION
            case AppState.LOADING:
                return ScreenName.FILE_TRANSFER
            case AppState.ERROR:
                return ScreenName.ERROR

    def get_current_state(self) -> AppState:
        return self.current_state