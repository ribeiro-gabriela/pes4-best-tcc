from typing import Optional
from data.classes import User 

class UserDatabase:
    def __init__(self):
        self.users = {
            "usuario": User("usuario", "senha123"),
            "admin": User("admin", "admin")
        }

    def validate_credentials(self, username: str, password: str) -> Optional[User]:
        from services.logging_service import LoggingService
        logging_service = LoggingService("UserDatabase")

        logging_service.log(f"[UserDB] Validating user credentials: {username}")
        user = self.users.get(username)

        if user:
            logging_service.log(f"[UserDB] User '{username}' found. Comparing passwords.")
            if user.password_hash == password:
                logging_service.log(f"[UserDB] Correct password for '{username}'.")
                return user
            else:
                logging_service.log(f"[UserDB] Incorrect password for '{username}'.")
        else:
            logging_service.log(f"[UserDB] User '{username}' NOT found.")
        
        return None