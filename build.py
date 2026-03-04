"""Local build script - creates ksef-tools.exe with PyInstaller."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
VERSION_FILE = ROOT / "src" / "ksef_tools" / "version.py"
ORIGINAL_CONTENT = VERSION_FILE.read_text(encoding="utf-8")


def get_git_version() -> str:
    try:
        out = subprocess.check_output(
            ["git", "describe", "--tags", "--always"], cwd=ROOT, text=True
        ).strip()
        return out.lstrip("v")
    except Exception:
        return "0.0.0-dev"


def inject_version(version: str) -> None:
    VERSION_FILE.write_text(f'_VERSION = "{version}"\n', encoding="utf-8")


def build_exe() -> None:
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--name",
            "ksef-tools",
            "--hidden-import", "ksef_tools.commands",
            "--hidden-import", "ksef_tools.commands.send",
            "--hidden-import", "ksef_tools.commands.list",
            str(ROOT / "src" / "ksef_tools" / "__main__.py"),
        ],
        cwd=ROOT,
    )


def main() -> None:
    version = get_git_version()
    print(f"Building ksef-tools {version}")
    inject_version(version)
    try:
        build_exe()
    finally:
        VERSION_FILE.write_text(ORIGINAL_CONTENT, encoding="utf-8")

    exe = ROOT / "dist" / "ksef-tools.exe"
    if exe.exists():
        print(f"Built: {exe}")
    else:
        print("Build failed - exe not found", file=sys.stderr)
        sys.exit(1)

    # Clean up build artifacts
    for d in (ROOT / "build", ROOT / "ksef-tools.spec"):
        if d.is_dir():
            shutil.rmtree(d)
        elif d.is_file():
            d.unlink()


if __name__ == "__main__":
    main()
