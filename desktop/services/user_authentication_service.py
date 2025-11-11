import uuid
from datetime import datetime, timedelta
from typing import Optional
from services.logging_service import LoggingService
from data.classes import Session
from services.user_database_module import UserDatabase

# [BST-288]
INACTIVITY_TIMEOUT_MINUTES = 10

class UserAuthenticationService:
    def __init__(self, user_database: UserDatabase, logging_service = LoggingService('UserAuthenticationService')):
        self.user_database = user_database
        self.logging_service = logging_service
        self.currentSession: Optional[Session] = None

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
        else:
            # [BST-284]
            self.currentSession = None
            # [BST-286]
            self.logging_service.log(
                f"Failed authentication attempt for user {username}."
            )

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
