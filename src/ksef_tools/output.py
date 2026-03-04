from __future__ import annotations

import json
import sys
from typing import Any

STATUS_ERROR = "ERROR"
STATUS_SUCCESS = "SUCCESS"
STATUS_REFUSED = "REFUSED"

CODE_ERROR = -10
CODE_SUCCESS = 20
CODE_REFUSED = 30


def success(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"status": STATUS_SUCCESS, "status_code": CODE_SUCCESS}
    if extra:
        result.update(extra)
    return result


def error(message: str, response: Any = None) -> dict[str, Any]:
    return {
        "status": STATUS_ERROR,
        "status_code": CODE_ERROR,
        "error": message,
        "response": response or {},
    }


def refused(message: str, response: Any = None) -> dict[str, Any]:
    return {
        "status": STATUS_REFUSED,
        "status_code": CODE_REFUSED,
        "error": message,
        "response": response or {},
    }


def print_json(data: dict[str, Any]) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2, default=str)
    sys.stdout.write("\n")
    sys.stdout.flush()
