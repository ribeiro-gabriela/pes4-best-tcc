from abc import ABC, abstractmethod
from typing import List

from data.classes import Connection, Package, Request, Response

class IConnectionTransport(ABC):
    @abstractmethod
    def scan(self) -> List[dict]: 
        pass

    @abstractmethod
    def connect(self, target: str, password: str|None = None) -> Connection:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass
    
    @abstractmethod
    def sendPackage(self, pkg: Package) -> None:
        pass
    
    @abstractmethod
    def receivePackage(self, file_name: str) -> Package:
        pass
    
    @abstractmethod
    def sendRequest(self, req: Request, target: str, timeout: int) -> Response: 
        pass