import threading
import time
from datetime import datetime, timedelta
from typing import Optional
from data.events import Event
from services.logging_service import LoggingService
from data.classes import Session
from services.user_database_module import UserDatabase
from data.errors import IdentificationError
from ui.event_router import emit_event

# [BST-288]
INACTIVITY_TIMEOUT_MINUTES = 10

class UserAuthenticationService:
    def __init__(self, user_database: UserDatabase):
        self.user_database = user_database
        self.logging_service = LoggingService(UserAuthenticationService.__name__)
        self.currentSession: Optional[Session] = None
        # [BST-288]
        self._health_check_thread: threading.Thread = threading.Thread(target=self._check_inactivity_loop, daemon=True)
        self._health_check_thread.start()

    def login(self, username: str, password: str) -> None:
        # [BST-282]
        user = self.user_database.validate_credentials(username, password)

        if user:
            now = datetime.now()
            # [BST-283, BST-287, BST-288]
            self.currentSession = Session(
                user=user,
                lastActivityAt=now)
            # [BST-285]
            self.logging_service.log(f"User {username} authenticated successfully.")
            self.logging_service.log(f"currentSession created for user {username} at {now}.")
        else:
            # [BST-284]
            self.currentSession = None
            # [BST-286]
            self.logging_service.log(
                f"Failed authentication attempt for user {username}. currentSession is still {self.currentSession}."
            )
            raise IdentificationError("Invalid username or password. Please try again.")

    def _check_inactivity(self) -> None:
        if self.currentSession:
            time_since_last_activity = datetime.now() - self.currentSession.lastActivityAt
            # [BST-288]
            if time_since_last_activity > timedelta(
                minutes=INACTIVITY_TIMEOUT_MINUTES
            ):
                # [BST-289]
                self.logging_service.log(
                    f"Session for user {self.currentSession.user.username} invalidated due to inactivity."
                )
                # [BST-288]
                self.currentSession = None
                # [BST-289]
                self.logging_service.log(
                    f"currentSession set to {self.currentSession}."
                )
                raise Exception("Logout due to inactivity")
    
    # [BST-288]   
    def _check_inactivity_loop(self) -> None:
        while True:
            if self.currentSession:
                try:
                    self._check_inactivity()
                except Exception as e:
                    emit_event(Event(Event.EventType.ERROR, error=e))
            time.sleep(30)

    def isAuthenticated(self) -> bool:
        # [BST-288]
        self._check_inactivity()

        # [BST-291]
        if self.currentSession is None:
            return False
        else:
            # [BST-290]
            self.currentSession.lastActivityAt = datetime.now()
            return True

    def logout(self) -> None:
        if self.currentSession:
            # [BST-293]
            self.logging_service.log(
                f"User {self.currentSession.user.username} logged out."
            )

        # [BST-292]
        self.currentSession = None
