from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

@dataclass
class Event:
    class EventType(Enum):
        NAVIGATE = "navigate"
        ERROR = "error"
        LOGIN_ATTEMPT = "login_attempt"  
        LOGIN_SUCCESS = "login_success"  
        LOGIN_FAILURE = "login_failure" 
        LOGOUT = "logout"              
        SESSION_INVALIDATED = "session_invalidation"
        RECONNECTION = "reconnection"
        RECONNECTION_SUCCESS = "reconnection_success"
        NAVIGATE_TO_CONNECTION = "navigate_to_connection"
        NAVIGATE_TO_IMAGES = "navigate_to_images"
        BACK = "back"
        CANCEL = "cancel"
        CONNECTION_ATTEMPT = "connection_attempt"
        CONNECTION_SUCCESS = "connection_success"
        CONNECTION_FAILURE = "connection_failure"
        DISCONNECT = "disconnect"
        START_LOADING = "start_loading"
        LOADING_COMPLETE = "loading_complete"
        DISMISS_ERROR = "dismiss_error"
        LOAD_IMAGE_REQUESTED = "load_image_requested"
        
    type: EventType
    error: Optional[Exception] = None
    properties: dict[str, Any] = field(default_factory=dict)