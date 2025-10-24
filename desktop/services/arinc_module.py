from typing import Any
from data.classes import File


class ArincModule:
    # [BST-235]
    def startTransfer(self, file: File) -> bool:
        # [BST-238]
        return True
    
    # [BST-237]
    def getProgress(self) -> Any:
        return "TransferFinished"
    
    # [BST-245]
    def cancel(self):
        pass