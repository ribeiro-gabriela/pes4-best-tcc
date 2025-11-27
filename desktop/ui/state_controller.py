from data.enums import ScreenName, AppState
from data.events import Event
from services.logging_service import LoggingService
from ui.event_router import EventRouter, emit_event
from ui.screen_manager import ScreenManager as KivyAppScreenManager
from services.service_facade import ServiceFacade 
from data.errors import IdentificationError
from screens.error_screen import ErrorScreen

    
class StateController:
    def __init__(self, event_router: EventRouter, screen_manager: KivyAppScreenManager, service_facade: ServiceFacade):
        self.logging_service = LoggingService(StateController.__name__)
        # [BST-299]
        self.current_state = AppState.LOGIN
        self.previous_state = AppState.LOGIN
        self.event_router = event_router
        self.screen_manager = screen_manager
        self.service_facade = service_facade
        
        self.event_router.register_callback(self.route_navigation_event)
        self.event_router.register_callback(self.process_event)

        self.logging_service.log(f"Application initialization. Transitioning to {AppState.LOGIN.value}.")
        self._transition_to(AppState.LOGIN) 

    def route_navigation_event(self,event :Event) -> None:
        if event.type != Event.EventType.NAVIGATE:
            return
        
        target_screen_name_str = event.properties.get("target", "")
        if not target_screen_name_str:
            # [BST-335]
            self.logging_service.error("Navigation error: empty target screen name")
            emit_event(Event(Event.EventType.ERROR, error=Exception("Navigation error: empty target screen name")))
            return

        try:
            target_app_state = self._map_screen_to_state(ScreenName(target_screen_name_str))
            self._transition_to(target_app_state)
        except Exception as e:
            # [BST-335]
            self.logging_service.error(f"Navigation error: {target_screen_name_str}", context=e)
            emit_event(Event(Event.EventType.ERROR, error=e, properties={'message': f"Navigation error to {target_screen_name_str}"}))
    def process_event(self, event: Event) -> None:
        if event.type == Event.EventType.ERROR and self.current_state != AppState.ERROR:
            self._transition_to_error(event)
            return

        # [BST-302]
        if (event.type == Event.EventType.LOGOUT or event.type == Event.EventType.SESSION_INVALIDATED) \
           and self.current_state != AppState.LOGIN:
            # [E3] e [E4] LoggedIn > Login
            self.logging_service.log(f"Global event {event.type.value} received. Logging out and transitioning to {AppState.LOGIN.value}.")
            # [BST-301]
            self.service_facade.logout() 
            self._transition_to(AppState.LOGIN)
            return
         
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
            case Event.EventType.LOGIN_ATTEMPT:
                username = event.properties.get('username', '')
                password = event.properties.get('password', '')
                
                try:
                    # [BST-331]
                    success, message = self.service_facade.login(username, password)
                
                    if success:
                        emit_event(Event(Event.EventType.LOGIN_SUCCESS))
                    else:
                        # [BST-300]
                        self.logging_service.log(f"Login failed for '{username}': {message}")
                        emit_event(Event(Event.EventType.LOGIN_FAILURE, properties={'message': message}))
                except Exception as e:
                    # [BST-335]
                    self.logging_service.error(f"[StateController] Unexpected error during login for '{username}': {e}", context=e)
                    emit_event(Event(Event.EventType.LOGIN_FAILURE, properties={'message': f"Internal error: {e}"})) 

            case Event.EventType.LOGIN_SUCCESS:
                # [E1] Login > Main
                self.logging_service.log(f"Login successful. Transitioning to {AppState.MAIN.value}.")
                self._transition_to(AppState.MAIN)
            
            case Event.EventType.ERROR:
                # [E2] Login > Erro
                self._transition_to_error(event)
            
            case _:
                self._handle_global_events(event)

    def _handle_main_state(self, event: Event) -> None:
        match event.type:
            case Event.EventType.NAVIGATE_TO_CONNECTION:
                # [E5] Main > Connection
                self._transition_to(AppState.CONNECTION)
            case Event.EventType.NAVIGATE_TO_IMAGES:
                # [E6] Main > Images
                self._transition_to(AppState.IMAGES)
            case _:
                self._handle_global_events(event)

    def _handle_connection_state(self, event: Event) -> None:
        match event.type:
            case Event.EventType.BACK | Event.EventType.CANCEL:
                # [E7] Connection > Main
                self._transition_to(AppState.MAIN)
            case Event.EventType.CONNECTION_ATTEMPT:
                target_network = event.properties.get('target', '')
                password = event.properties.get('password')
                try:
                    self.logging_service.log(f"StateController: Trying to connect to '{target_network}'...")
                    self.service_facade.connectToWifi(target_network, password)
                    emit_event(Event(Event.EventType.CONNECTION_SUCCESS, properties={'target': target_network}))
                except Exception as e:
                    self.logging_service.error(f"StateController: Failed to connect to '{target_network}': {e}", context=e)
                    emit_event(Event(Event.EventType.CONNECTION_FAILURE, properties={'message': str(e)}))
            case Event.EventType.CONNECTION_SUCCESS:
                # [E9] Connection . PostConnection
                # [BST-311]
                self._transition_to(AppState.POST_CONNECTION)
            case Event.EventType.CONNECTION_FAILURE:
                self._transition_to_error(event)
            case Event.EventType.RECONNECTION_SUCCESS:
                self._transition_to(AppState.POST_CONNECTION)
            case _:
                self._handle_global_events(event)

    def _handle_images_state(self, event: Event) -> None:
        match event.type:
            case Event.EventType.BACK:
                # [E8] Images > Main
                self._transition_to(AppState.MAIN)
            case _:
                self._handle_global_events(event)

    def _handle_post_connection_state(self, event: Event) -> None:
        match event.type:
            case Event.EventType.DISCONNECT:
                # [E10] PostConnection > Main
                # [BST-317]
                self._transition_to(AppState.MAIN)
            case Event.EventType.BACK:
                # [E11] PostConnection > Images
                self._transition_to(AppState.IMAGES)
            case Event.EventType.START_LOADING:
                # [E12] PostConnection > Loading
                # [BST-318]
                self._transition_to(AppState.LOADING)
            case Event.EventType.RECONNECTION:
                self._transition_to(AppState.CONNECTION)
            case _:
                self._handle_global_events(event)

    def _handle_loading_state(self, event: Event) -> None:
        match event.type:
            case Event.EventType.LOADING_COMPLETE:
                # [E13] Loading > PostConnection
                # [BST-334]
                self._transition_to(AppState.POST_CONNECTION)
            case _:
                self._handle_global_events(event)

    def _handle_error_state(self, event: Event) -> None:
        match event.type:
            case Event.EventType.DISMISS_ERROR:
                # [E15] Error > App 
                self.logging_service.log(f"Error dismissed. Returning to the previous state: {self.previous_state.value}.")
                self._transition_to(self.previous_state)
            case Event.EventType.ERROR:
                # [BST-335]
                self.logging_service.error(f"New error received in error state: {event.error}", context=event.error)
            case _:
                pass

    def _handle_global_events(self, event: Event) -> None:
        match event.type:
            case Event.EventType.ERROR:
                # [E14] App > Error
                self._transition_to_error(event)

    def _transition_to(self, new_state: AppState) -> None:
        if self.current_state != new_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            self.logging_service.log(f"State transition: {self.previous_state.value} -> {new_state.value}")
            
            menu_visible = (new_state != AppState.LOGIN)
            self.screen_manager.toggle_menu_bar_visibility(menu_visible)

            self.screen_manager.navigate(self._map_state_to_screen(new_state).value)
            
            if self.screen_manager.navigator and \
               self.screen_manager.navigator.screen_manager.has_screen(ScreenName.ERROR.value):
                error_screen = self.screen_manager.navigator.screen_manager.get_screen(ScreenName.ERROR.value)
                if isinstance(error_screen, ErrorScreen): 
                    error_screen.error_message = "An unexpected error occurred in the application." 
        else:
            self.logging_service.log(f"Attempt to transition to the same state: {new_state.value}. No action taken.")

    def _transition_to_error(self, event: Event) -> None:
        if self.current_state != AppState.ERROR:
            self.previous_state = self.current_state
        self.current_state = AppState.ERROR

        error_message = "Unexpected error"

        # [BST-335]
        if event and event.error:
            error_message = str(event.error)
            if event.properties.get("message"):
                error_message = event.properties.get("message")

        if self.screen_manager.navigator and \
           self.screen_manager.navigator.screen_manager.has_screen(ScreenName.ERROR.value):
            error_screen = self.screen_manager.navigator.screen_manager.get_screen(ScreenName.ERROR.value)
            if isinstance(error_screen, ErrorScreen):
                error_screen.error_message = error_message      
                  
        # [BST-335]          
        self.logging_service.error(f'Transition to the error state of {self.previous_state.value}.', context=event.error)
        self.screen_manager.navigate(ScreenName.ERROR.value)

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
        raise ValueError(f"Unknown AppState: {state}. No mapping for ScreenName.")

    def _map_screen_to_state(self, screen_name: ScreenName) -> AppState:
        match screen_name:
            case ScreenName.LOGIN:
                return AppState.LOGIN
            case ScreenName.MAIN:
                return AppState.MAIN
            case ScreenName.CONNECTION:
                return AppState.CONNECTION
            case ScreenName.IMAGES:
                return AppState.IMAGES
            case ScreenName.POST_CONNECTION:
                return AppState.POST_CONNECTION
            case ScreenName.FILE_TRANSFER:
                return AppState.LOADING
            case ScreenName.ERROR:
                return AppState.ERROR
        raise ValueError(f"Unknown ScreenName: {screen_name}. No mapping to AppState.")


    def get_current_state(self) -> AppState:
        return self.current_state