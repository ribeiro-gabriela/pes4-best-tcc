import logging
import sys

# [BST-296, BST-297, BST-298]
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# [BST-298]
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[logging.FileHandler("service.log"), logging.StreamHandler(sys.stdout)],
    force=True
)

class LoggingService:
    def __init__(self, service_name: str):
        # [BST-297]
        self.logger = logging.getLogger(service_name)

    def log(self, message: str) -> None:
        # [BST-294]
        self.logger.info(message)

    # [BST-295]
    def error(self, message: str, context: Exception | None = None) -> None:
        if context:
            self.logger.error(message, exc_info=context)
        else:
            self.logger.error(message)
