from typing import Optional
import uuid
from data.classes import User

class UserDatabase:
    def validate_credentials(self, username: str, password: str) -> Optional[User]:
        # [BST-282]
        # (Implementação mockada da consulta ao banco de dados)
        if username == "admin" and password == "valid_password":
            return User(id=uuid.uuid4(), username=username)
        return None