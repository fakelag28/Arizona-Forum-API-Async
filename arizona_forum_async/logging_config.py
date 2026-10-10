import logging
import sys
from typing import Optional, TextIO


LOGGER_NAME = "arizona_forum_async"
LOGGER = logging.getLogger(LOGGER_NAME)
LOGGER.addHandler(logging.NullHandler())


def configure_logging(
    level: int = logging.INFO,
    stream: Optional[TextIO] = None,
    formatter: Optional[logging.Formatter] = None,
    handler: Optional[logging.Handler] = None,
) -> logging.Logger:
    LOGGER.setLevel(level)

    for handler in LOGGER.handlers:
        if getattr(handler, "_arizona_configured", False):
            return LOGGER

    handler = handler or logging.StreamHandler(stream or sys.stderr)
    handler._arizona_configured = True
    handler.setFormatter(
        formatter
        or logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )
    LOGGER.addHandler(handler)
    return LOGGER
