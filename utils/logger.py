import logging
import sys
def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    return logging.getLogger("Codex2050")
def get_logger(name):
    return logging.getLogger(name)
