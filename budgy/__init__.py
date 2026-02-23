# Configure root logger
from loggers import configure_logging, clear_logs
from .utils.file_utils import EDirectories

handler_controller = configure_logging(log_directory=EDirectories.LOG_DIR)
# clear_logs(EDirectories.LOG_DIR)

# Define package-level variables
__version__ = "2.0.0"
__Author__ = "Elias Rodkey"