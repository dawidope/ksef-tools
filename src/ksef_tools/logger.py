from __future__ import annotations

import logging
import sys
from datetime import date
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
    log_file = log_dir / f"ksef-tools-{date.today().isoformat()}.log"
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
    )
    logger.addHandler(handler)
    return logger
