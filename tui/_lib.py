"""Path bootstrap for the TUI: makes the framework's config core importable."""

import sys
from pathlib import Path

INSTALL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(INSTALL_ROOT / "lib"))

import config  # noqa: E402
import models  # noqa: E402
import schedule_fmt  # noqa: E402

__all__ = ["config", "models", "schedule_fmt", "INSTALL_ROOT"]
