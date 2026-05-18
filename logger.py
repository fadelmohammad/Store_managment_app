# logger.py
# Central logging configuration for OmniPOS.
# Call setup_logging() once at app startup (main.py).
# All other modules just use: import logging; logging.getLogger(__name__)

import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR  = "logs"
_LOG_FILE = "omnipos.log"
_MAX_BYTES    = 5 * 1024 * 1024   # 5 MB per file
_BACKUP_COUNT = 3                  # keep omnipos.log + 3 rotated files


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger to write to logs/omnipos.log only.
    No output goes to the terminal.
    Rotating file handler: 5 MB max, 3 backups kept.
    """
    os.makedirs(_LOG_DIR, exist_ok=True)

    log_path = os.path.join(_LOG_DIR, _LOG_FILE)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  —  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    root = logging.getLogger()
    root.setLevel(level)

    # Remove any existing handlers (e.g. default StreamHandler added by basicConfig)
    root.handlers.clear()
    root.addHandler(handler)
