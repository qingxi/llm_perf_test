"""Logging setup for llm_perf_test."""
import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging():
    """Setup logging to console and rotating file handler."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "ai_perf_test.log")

    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"

    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    root.setLevel(level)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(fmt))

    file_handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(fmt))

    root.addHandler(console)
    root.addHandler(file_handler)

def log(message:str, level:str="info"):
    """Log a message at the specified level."""
    logger = logging.getLogger(__name__)
    if level.lower() == "debug":
        logger.debug(message)
    elif level.lower() == "warning":
        logger.warning(message)
    elif level.lower() == "error":
        logger.error(message)
    else:
        logger.info(message)

setup_logging()