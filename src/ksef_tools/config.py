from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path.cwd()


@dataclass
class Config:
    ksef_token: str
    context_type: str
    context_value: str
    base_url: str = "https://ksef-demo.mf.gov.pl"
    subject_type: str = "Subject1"
    date_type: str = "Issue"
    base_dir: Path = field(default_factory=_get_base_dir, repr=False)

    def __repr__(self) -> str:
        return (
            f"Config(context_type={self.context_type!r}, "
            f"context_value={self.context_value!r}, "
            f"base_url={self.base_url!r}, ksef_token=<redacted>)"
        )

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        if path is None:
            path = _get_base_dir() / "config.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Config file not found: {path}\n"
                "Copy config.json.example to config.json and fill in your values."
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = [k for k in ("ksef_token", "context_type", "context_value") if not data.get(k)]
        if missing:
            raise ValueError(f"Missing required config fields: {', '.join(missing)}")
        return cls(
            ksef_token=data["ksef_token"],
            context_type=data["context_type"],
            context_value=data["context_value"],
            base_url=data.get("base_url", "https://ksef-demo.mf.gov.pl"),
            subject_type=data.get("subject_type", "Subject1"),
            date_type=data.get("date_type", "Issue"),
            base_dir=path.parent,
        )
