import uuid
from datetime import datetime, timedelta
from typing import Optional

# [BST-298]
from services.logging_service import LoggingService
from data.classes import Session, User
from services.user_database_module import UserDatabase
from data.errors import IdentificationError

from ui.event_router import emit_event
from data.events import Event

class UserAuthenticationService:
    def __init__(self, user_database: UserDatabase, logging_service = LoggingService('UserAuthenticationService')):
        self.user_database = user_database
        self.logging_service = logging_service
        self.currentSession: Optional[Session] = None
        # [BST-288]
        self._last_activity_time: Optional[datetime] = None
        # [BST-288]
        self._INACTIVITY_TIMEOUT_MINUTES = 10

    def login(self, username: str, password: str) -> None:
        # [BST-282]
        user = self.user_database.validate_credentials(username, password)

        if user:
            now = datetime.now()
            # [BST-283]
            # [BST-287]
            self.currentSession = Session(
                user=user,
                createdAt=now,
                expiresAt=now + timedelta(hours=8),  # (Expirar em 8 horas)
            )
            # [BST-288]
            self._last_activity_time = now
            # [BST-285]
            self.logging_service.log(f"User {username} authenticated successfully.")
        else:
            # [BST-284]
            self.currentSession = None
            self._last_activity_time = None
            # [BST-286]
            self.logging_service.log(
                f"Failed authentication attempt for user {username}."
            )
            raise IdentificationError("Invalid username or password. Please try again.")

    def _check_inactivity(self) -> None:
        # [BST-288]
        if self._last_activity_time and self.currentSession:
            time_since_last_activity = datetime.now() - self._last_activity_time
            # [BST-288]
            if time_since_last_activity > timedelta(
                minutes=self._INACTIVITY_TIMEOUT_MINUTES
            ):
                # [BST-289]
                self.logging_service.log(
                    f"Session for user {self.currentSession.user.username} invalidated due to inactivity."
                )
                # [BST-288]
                self.currentSession = None
                self._last_activity_time = None
                emit_event(Event(Event.EventType.SESSION_INVALIDATED))

    def isAuthenticated(self) -> bool:
        # [BST-288]
        self._check_inactivity()

        # [BST-291]
        if self.currentSession is None:
            return False

        # [BST-291]
        if self.currentSession.is_expired():
            self.logging_service.log(
                f"Session for user {self.currentSession.user.username} expired."
            )
            self.currentSession = None
            self._last_activity_time = None
            emit_event(Event(Event.EventType.SESSION_INVALIDATED))
            return False

        # [BST-290]
        # [BST-288]
        self._last_activity_time = datetime.now()
        return True

    def logout(self) -> None:
        if self.currentSession:
            # [BST-293]
            self.logging_service.log(
                f"User {self.currentSession.user.username} logged out."
            )

        # [BST-292]
        self.currentSession = None
        # [BST-288]
        self._last_activity_time = None