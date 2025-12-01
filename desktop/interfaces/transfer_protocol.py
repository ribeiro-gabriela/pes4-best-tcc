from abc import ABC, abstractmethod

from data.classes import FileRecord, TransferStatus

class ITransferProtocol(ABC):
    @abstractmethod
    def startTransfer(self, file: FileRecord) -> bool:
        pass

    # [BST-237]
    @abstractmethod
    def getProgress(self) -> TransferStatus:
        pass

    # [BST-245]
    @abstractmethod
    def cancel(self):
        pass