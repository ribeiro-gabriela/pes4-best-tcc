import logging
import sys

# [BST-298]
# [BST-296]
# [BST-297]
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# [BST-298]
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[logging.FileHandler("service.log"), logging.StreamHandler(sys.stdout)],
)

class LoggingService:
    def __init__(self, service_name: str):
        # [BST-297]
        self.logger = logging.getLogger(service_name)

    # [BST-294]
    def log(self, message: str) -> None:
        # [BST-294]
        self.logger.info(message)

    # [BST-295]
    def error(self, message: str, context: Exception | None = None) -> None:
        if context:
            self.logger.error(message, exc_info=context)
        else:
            self.logger.error(message)
