import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def configure_logging():
    """Configure basic structured logging for the application.

    Uses a simple format including level, module, and message. In production you
    could swap to JSON logging or integrate with OpenTelemetry.
    """
    if logging.getLogger().handlers:
        # Already configured (avoid duplicate handlers in reload / dev)
        return
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    logging.basicConfig(level=LOG_LEVEL, format=fmt)


def get_logger(name: str):
    configure_logging()
    return logging.getLogger(name)
