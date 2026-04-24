__version__ = "2.0.0"
__Author__ = "Elias Rodkey"

from pleasant_loggers import configure_logging, LoggingMode, DirectoryLayout, LogReader
import logging
from .utils.file_utils import EDirectories

custom_mode = LoggingMode(
    stream=True,
    stream_level=logging.INFO,
    file=False,
    file_level=logging.DEBUG,
    json=True,
    json_level=logging.DEBUG,
    directory_layout=DirectoryLayout.DAILY,
)

configure_logging(
    log_directory=EDirectories.LOG_DIR,
    mode=custom_mode
)
