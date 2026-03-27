# ================================================================
#  love_core.utils.logger
#  ----------------------------------------------------------------
#  Provides a pre-configured logger factory for every module in
#  the framework.  All loggers write to:
#    • stdout (INFO and above)
#    • love_core.log file (DEBUG and above, rotated at 1 MB)
#
#  Usage
#  -----
#      from love_core.utils.logger import get_logger
#      log = get_logger(__name__)
#      log.info("Ready.")
# ================================================================

from __future__ import annotations

import logging
import logging.handlers
import os
import sys

# ── Constants ────────────────────────────────────────────────
_LOG_FILE    = os.path.join(os.path.expanduser("~"), ".love_core", "love_core.log")
_LOG_FORMAT  = "[%(asctime)s] [%(levelname)-8s] %(name)s — %(message)s"
_DATE_FORMAT = "%H:%M:%S"
_MAX_BYTES   = 1_048_576   # 1 MB
_BACKUP_COUNT = 3

_initialised = False


def _init_root_logger() -> None:
    """Initialise the root 'love_core' logger exactly once."""
    global _initialised
    if _initialised:
        return

    root = logging.getLogger("love_core")
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Console handler — INFO+
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    root.addHandler(console)

    # Rotating file handler — DEBUG+
    try:
        os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            _LOG_FILE,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # Non-fatal — fall back to console-only
        root.warning("Could not create log file at %s", _LOG_FILE)

    _initialised = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger of 'love_core' namespaced by *name*.

    Parameters
    ----------
    name : str
        Typically ``__name__`` of the calling module.

    Returns
    -------
    logging.Logger
    """
    _init_root_logger()
    # Normalise external module names to sit under love_core namespace
    if not name.startswith("love_core"):
        name = f"love_core.ext.{name}"
    return logging.getLogger(name)
