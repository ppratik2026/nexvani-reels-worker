import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def chromium_path() -> str | None:
    """A Chrome/Chromium to use instead of Playwright's download (CHROMIUM_PATH), if one is set or preinstalled."""
    for candidate in (os.environ.get("CHROMIUM_PATH"), "/opt/pw-browsers/chromium"):
        if candidate and Path(candidate).exists():
            return candidate
    return None


def require_tool(name: str) -> None:
    if not shutil.which(name):
        raise SystemExit(f"{name} is not installed (needed to make the reel video).")
