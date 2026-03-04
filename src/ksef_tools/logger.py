from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logger(base_dir: Path | None = None) -> logging.Logger:
    if base_dir is None:
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path.cwd()

    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("ksef_tools")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    handler = TimedRotatingFileHandler(
        log_dir / "ksef-tools.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
    )
    logger.addHandler(handler)
    return logger
