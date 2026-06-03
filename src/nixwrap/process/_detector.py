"""Rocket League process detection and platform identification.

Detects whether the running RL is the Steam or Epic Games version
by inspecting the game's root directory for tell-tale files.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path

import psutil


class RLPlatform(Enum):
    STEAM = "steam"
    EPIC = "epic"
    UNKNOWN = "unknown"


def _find_root_dir(exe_path: Path) -> Path | None:
    """Walk up from exe_path to find the game root directory.

    The root is the folder that contains Binaries/ and
    (Engine/ or TAGame/).
    """
    current = exe_path.parent
    for _ in range(10):  # safety cap
        bins = current / "Binaries"
        engine = current / "Engine"
        tagame = current / "TAGame"
        if bins.is_dir() and (engine.is_dir() or tagame.is_dir()):
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def detect_platform(root_dir: Path) -> RLPlatform:
    """Determine the platform (Steam / Epic) from the game root directory.

    Detection heuristics (checked in order):

    1. appinfo.vdf file in root -> Steam
    2. .egstore folder in root -> Epic
    3. Path contains steamapps or steamlibrary -> Steam
    4. Path contains Epic Games or Epic -> Epic
    """
    root_str = str(root_dir).lower()

    # File/folder markers
    if (root_dir / "appinfo.vdf").exists():
        return RLPlatform.STEAM
    if (root_dir / ".egstore").is_dir():
        return RLPlatform.EPIC

    # Path heuristics
    if "steamapps" in root_str or "steamlibrary" in root_str:
        return RLPlatform.STEAM
    if "epic games" in root_str or "epicgames" in root_str:
        return RLPlatform.EPIC

    return RLPlatform.UNKNOWN


def get_save_data_path(platform: RLPlatform) -> Path | None:
    """Return the full path to DBE_Production/ for the given platform.

    Uses the standard Documents location:
    - Steam: Documents/My Games/Rocket League/TAGame/SaveData/DBE_Production/
    - Epic:  Documents/My Games/Rocket League/TAGame/SaveDataEpic/DBE_Production/
    """
    from nixwrap.utils._constants import SAVE_PATH_STEAM, SAVE_PATH_EPIC

    docs = Path(os.path.expanduser("~")) / "Documents"
    if platform == RLPlatform.STEAM:
        return docs / SAVE_PATH_STEAM
    elif platform == RLPlatform.EPIC:
        return docs / SAVE_PATH_EPIC
    else:
        # Try both
        for rel in (SAVE_PATH_STEAM, SAVE_PATH_EPIC):
            candidate = docs / rel
            if candidate.is_dir():
                return candidate
        return docs / SAVE_PATH_STEAM  # best guess


# Main public function

class RLProcessInfo:
    """Information about a running Rocket League process."""

    __slots__ = ("pid", "exe_path", "root_dir", "platform", "save_data_path")

    def __init__(self, pid: int, exe_path: Path, root_dir: Path,
                 platform: RLPlatform, save_data_path: Path):
        self.pid = pid
        self.exe_path = exe_path
        self.root_dir = root_dir
        self.platform = platform
        self.save_data_path = save_data_path

    def __repr__(self) -> str:
        return (
            f"RLProcessInfo(pid={self.pid}, "
            f"platform={self.platform.value}, "
            f"root={self.root_dir})"
        )


def find_rocket_league() -> RLProcessInfo | None:
    """Find the running Rocket League process and return its info.

    Returns None if Rocket League is not running.
    """
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            name = proc.info.get('name', '')
            if 'rocketleague' not in name.lower():
                continue
            exe_path = proc.info.get('exe')
            if not exe_path:
                continue
            exe = Path(exe_path)
            if not exe.exists():
                continue

            root = _find_root_dir(exe)
            if root is None:
                continue

            platform = detect_platform(root)
            save_path = get_save_data_path(platform)

            return RLProcessInfo(
                pid=proc.pid,
                exe_path=exe,
                root_dir=root,
                platform=platform,
                save_data_path=save_path or Path("."),
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied,
                 ProcessLookupError):
            continue

    return None
