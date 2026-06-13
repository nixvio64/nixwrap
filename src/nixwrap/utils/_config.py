"""PsyNet config API wrapper — playlists, maps, events from the game's own endpoint."""

from __future__ import annotations

import json
import re
import time
import urllib.request
from typing import Any

_CONFIG_URL = (
    "https://config.psynet.gg/v2/Config/BattleCars/"
    "{build_id}/Prod/Steam/{lang}/"
)

_cache: dict[str, dict[str, Any]] = {}


def fetch_psynet_config(build_id: int | str, lang: str = "INT") -> dict[str, Any]:
    """Fetch the PsyNet config JSON, cached in memory per build id + lang.

    Returns empty dict on failure.
    """
    cache_key = f"{build_id}:{lang}"
    if cache_key in _cache:
        return _cache[cache_key]

    url = _CONFIG_URL.format(build_id=build_id, lang=lang)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "nixwrap/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        data = {}

    _cache[cache_key] = data
    return data


# playlist stuff


def get_online_playlists(config: dict[str, Any]) -> dict[int, str]:
    """Get {playlist_id: title} from the config.

    When Title is null the section key name is used as fallback
    (e.g. "PrivateMatch" becomes "Private Match").
    Only sections with Class=PlaylistSettings_TA are considered.
    """
    result: dict[int, str] = {}
    for key, section in config.items():
        if not isinstance(section, dict):
            continue
        if section.get("Class") != "PlaylistSettings_TA":
            continue
        pid = section.get("PlaylistID")
        if pid is None:
            continue
        title = section.get("Title")
        if not title:
            title = _key_to_title(key)
        result[int(pid)] = title
    return result


def _key_to_title(key: str) -> str:
    """PrivateMatch -> Private Match, RankedSoloDuel -> Ranked Solo Duel."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key).strip()


def get_playlist_map_set_name(config: dict[str, Any], playlist_id: int) -> str | None:
    """MapSetName for a playlist id, if found."""
    for _key, section in config.items():
        if not isinstance(section, dict):
            continue
        if section.get("PlaylistID") == playlist_id:
            return section.get("MapSetName")
    return None


def get_playlist_player_count(config: dict[str, Any], playlist_id: int) -> int | None:
    """PlayerCount for a playlist id, if found."""
    for _key, section in config.items():
        if not isinstance(section, dict):
            continue
        if section.get("PlaylistID") == playlist_id:
            pc = section.get("PlayerCount")
            return int(pc) if pc is not None else None
    return None


def resolve_game_type_from_mapset(map_set_name: str | None) -> str | None:
    """SoccarStandard -> Soccar, RankedSoccarStandard -> Soccar, Hoops -> Hoops, etc."""
    if not map_set_name:
        return None

    _direct: dict[str, str] = {
        "SnowDay": "Snow Day",
        "Labs": "Rocket Labs",
        "GhostHunt": "Ghost Hunt",
        "BeachBall": "Beach Ball",
        "Heatseeker": "Heatseeker",
        "Knockout": "Knockout",
        "Gridiron": "Gridiron",
        "Volleyball": "Volleyball",
        "SuperCube": "Super Cube",
    }
    if map_set_name in _direct:
        return _direct[map_set_name]

    name = map_set_name
    if name.startswith("Ranked"):
        name = name[len("Ranked"):]
    for suffix in ("Standard", "Doubles", "Duel", "Quads", "Tournament"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    if name.startswith("Soccar"):
        name = "Soccar"

    return name if name else map_set_name


# map stuff


def get_maps_for_playlist(config: dict[str, Any], playlist_id: int) -> list[str]:
    """Internal map names for a playlist, MapList.Maps. prefix stripped."""
    map_set_name = get_playlist_map_set_name(config, playlist_id)
    if not map_set_name:
        return []

    maps_config = config.get("MapsConfig", {})
    if not isinstance(maps_config, dict):
        return []

    online_sets: list[dict[str, Any]] = maps_config.get("OnlineMapSets", [])
    for map_set in online_sets:
        if map_set.get("SetName") == map_set_name:
            return [
                _strip_map_prefix(m["Map"])
                for m in map_set.get("Maps", [])
                if "Map" in m
            ]

    return []


def _strip_map_prefix(full_name: str) -> str:
    """MapList.Maps.uf_day_p -> uf_day_p."""
    prefix = "MapList.Maps."
    if full_name.startswith(prefix):
        return full_name[len(prefix):]
    return full_name


# special events


def get_special_events(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Raw list of special events from the config (active and upcoming).

    Each event has keys like Title, Subtitle, StartTime, EndTime,
    LogoImage, BackgroundImage, EventID.
    """
    events_config = config.get("SpecialEventsConfig", {})
    if not isinstance(events_config, dict):
        return []
    events: list[dict[str, Any]] = events_config.get("Events", [])
    if not isinstance(events, list):
        return []
    return events


def get_active_events(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Special events that are currently active (StartTime <= now <= EndTime)."""
    now = int(time.time())
    return [
        e for e in get_special_events(config)
        if e.get("StartTime", 0) <= now <= e.get("EndTime", float("inf"))
    ]
