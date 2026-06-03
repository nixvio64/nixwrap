"""Decrypt and extract data from RL .save files. Read-only, see README for usage."""

from nixwrap.save_file._models import (     # noqa: F401
    SaveHeader,
    ParsedObject,
    ProfileStats,
    ClientXP,
    CameraSettings,
    ControlsSettings,
    GamepadBindings,
    PlaylistSkill,
    PlayerLoadout,
    LoadoutSet,
    PlayerBanner,
    PlayerAvatarBorder,
    OnlineProduct,
    GameplaySettings,
    VideoSettings,
    SoundSettings,
    MatchmakingSettings,
    NetworkSettings,
    QuickChatBinding,
    SeasonProgress,
    AchievementProgress,
    TutorialProgress,
    TrainingProgress,
    PlayerProfile,
    BanInfo,
    MusicPlaylist,
    Notification,
    CrumbTrail,
    MapPreferences,
)
from nixwrap.save_file._accessors import SaveData  # noqa: F401
from nixwrap.save_file._file_io import (    # noqa: F401
    parse_savedata,
    assemble_savedata,
)

import sys
from pathlib import Path


def load(filepath: str | Path, *, check_crc: bool = True) -> SaveData:
    """Decrypt and parse a .save file, returning a fully typed
    SaveData container.

    All data accessors are lazy -- they only parse on first access.

    Parameters
    filepath:
        Path to the .save file.
    check_crc:
        If True (default), warns on CRC mismatch via stderr.

    Returns
    SaveData
        Container with .camera, .stats, .controls,
        .skills, .xp, .inventory, and many more
        cached_property accessors.
    """
    raw = parse_savedata(str(filepath), check_crc=check_crc)
    return _raw_to_savedata(raw, Path(filepath))


def load_raw(filepath: str | Path, *, check_crc: bool = True) -> dict:
    """Low-level: decrypt and parse, returning the raw dict.

    Use this when you need direct access to the full property tree.
    """
    return parse_savedata(str(filepath), check_crc=check_crc)


def save(data: SaveData | dict, filepath: str | Path) -> None:
    """EXPERIMENTAL -- Re-encrypt and write a .save file.

    Round-tripped files may differ in size from the original.
    It is not guaranteed that the game will accept the re-encrypted file.
    """
    if isinstance(data, SaveData):
        raw = {
            "header": {
                "foosball": data.header.foosball,
                "magic": data.header.magic,
                "version_info": {
                    "engine_version": data.header.engine_version,
                    "licensee_version": data.header.licensee_version,
                    "type_version": data.header.type_version,
                },
            },
            "object_types": _rebuild_object_types(data),
            "properties": data.raw_properties,
            "objects": data.objects,
        }
    else:
        raw = data
    assemble_savedata(raw, str(filepath))


def find_save_file(save_data_path: str | Path | None = None) -> Path | None:
    """Find the latest-modified *.save in the DBE_Production directory.

    Parameters
    save_data_path:
        Path to DBE_Production/. If None, auto-detects via
        detect_save_data_path.

    Returns
    Path | None
        The path to the most recent .save file, or None if no
        files were found.
    """
    if save_data_path is None:
        save_data_path = detect_save_data_path()
    if save_data_path is None:
        return None
    dbe = Path(save_data_path)
    if not dbe.is_dir():
        return None
    saves = sorted(
        dbe.glob("*.save"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return saves[0] if saves else None


def detect_save_data_path() -> Path | None:
    """Auto-detect the correct save data path (Steam or Epic).

    Tries to find a running RocketLeague.exe process and determine
    the platform, then returns the corresponding DBE_Production path.

    If no process is running, checks both Steam and Epic save paths
    and returns the one whose most recent .save file was modified
    latest -- this is the best heuristic for "which install do they
    actually play on?"

    Returns None if no save path exists at all.

    Returns
    Path | None
    """
    # Try process detection first (RL is running: we know the platform)
    try:
        from nixwrap.process import find_rocket_league
        rl = find_rocket_league()
        if rl is not None:
            return rl.save_data_path
    except ImportError:
        pass

    # RL not running: compare both paths by most-recent-save heuristics
    from nixwrap.utils._constants import SAVE_PATH_STEAM, SAVE_PATH_EPIC
    import os
    docs = Path(os.path.expanduser("~")) / "Documents"

    best_path: Path | None = None
    best_mtime: float = 0.0

    for rel in (SAVE_PATH_STEAM, SAVE_PATH_EPIC):
        candidate = docs / rel
        if not candidate.is_dir():
            continue
        saves = sorted(
            candidate.glob("*.save"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if saves and saves[0].stat().st_mtime > best_mtime:
            best_mtime = saves[0].stat().st_mtime
            best_path = candidate

    return best_path


# Internals

def _raw_to_savedata(raw: dict, filepath: Path) -> SaveData:
    hdr = raw.get("header", {})
    vi = hdr.get("version_info", {})
    return SaveData(
        source_file=filepath,
        header=SaveHeader(
            engine_version=vi.get("engine_version", 0),
            licensee_version=vi.get("licensee_version", 0),
            type_version=vi.get("type_version", 0),
            foosball=hdr.get("foosball", ""),
            magic=hdr.get("magic", ""),
        ),
        raw_properties=raw.get("properties", {}),
        objects=raw.get("objects", []),
    )


def _rebuild_object_types(data: SaveData) -> list[dict]:
    """Minimal object type table rebuild for experimental save()."""
    ot = []
    obj_index = 0
    for obj in data.objects:
        ot.append({
            "type": obj.get("__type", "Unknown"),
            "object_index": obj_index,
            "file_position": 0,  # will be recalculated by assemble_savedata
        })
        obj_index += 1
    return ot
