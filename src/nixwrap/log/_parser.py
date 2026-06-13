"""Launch.log parser for Rocket League.

Extracts session info (username, steam id, rich presence, ...) and match info
(playlist, game mode, map, server ip/port) when verified via the Stats API.

Playlist names come from the PsyNet config API. Game type is derived from the
playlist's MapSetName. Map names are returned as internal ids, no pretty names.
"""

from __future__ import annotations

import os
import re
import socket
import time
from pathlib import Path
from typing import TYPE_CHECKING

from nixwrap.log._models import LogGameInfo, LogInfo, LogSessionInfo
from nixwrap.utils._config import (
    fetch_psynet_config,
    get_online_playlists,
)

if TYPE_CHECKING:
    pass

# regex patterns

_RE_USERNAME = re.compile(r"DevOnline: Logged in as '([^']+)'")
_RE_STEAM_ID = re.compile(r"DevOnline: Steam ID: (\d+)")
_RE_PLATFORM = re.compile(r"ScriptLog: Detected platform: (\w+)")
_RE_RICH_PRESENCE = re.compile(
    r"DevOnline: Set rich presence to: (.+?) data: (.+?)\s*$", re.MULTILINE,
)
_RE_WELCOMED = re.compile(
    r"DevNet: Welcomed by server "
    r"\(Level: ([^,]+), Game: ([^,]+), GameTags: ([^)]+)\)"
)
_RE_PLAYLIST_ID = re.compile(r"PlaylistId=(\d+)")
_RE_PLAYLIST = re.compile(r"Playlist=(\d+)")
_RE_SERVER_NAME = re.compile(r'ServerName="([^"]+)"')
_RE_REGION = re.compile(r'Region="([^"]+)"')
_RE_BROWSE_REMOTE = re.compile(r"DevNet: Browse: ([\d.]+):(\d+)/(\S+)")
_RE_BROWSE_LOCAL = re.compile(
    r"DevNet: Browse: (?![\d.]+:\d+/)(\S+)"
)
_RE_BUILD_ID = re.compile(r"Log: BuildID: (\d+) from GPsyonixBuildID")
_RE_BROWSE_GAME = re.compile(r"[?&]Game=([^?&]+)")
_RE_BROWSE_TAGS = re.compile(r"[?&]GameTags=([^?&]+)")

_STATS_HOST = "127.0.0.1"
_STATS_PORT = 49123
_STATS_VERIFY_TIMEOUT = 3.0


# helpers

def _find_last_match(pattern: re.Pattern, text: str) -> re.Match | None:
    last: re.Match | None = None
    for m in pattern.finditer(text):
        last = m
    return last


def _find_first_match(pattern: re.Pattern, text: str) -> re.Match | None:
    return pattern.search(text)


# stats api verification

def _verify_via_stats_api(
    timeout: float = _STATS_VERIFY_TIMEOUT,
) -> tuple[bool | None, bool]:
    """Quick check if player is in a live match via the stats api tcp socket.

    Returns (in_game, api_available).
    in_game: True in match, False not, None indeterminate.
    api_available: True if port accepted the connection.
    """
    sock: socket.socket | None = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect((_STATS_HOST, _STATS_PORT))
        sock.sendall(
            b"GET / HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Connection: keep-alive\r\n"
            b"\r\n"
        )
        api_available = True
        sock.settimeout(timeout)
        buf = b""
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            try:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
                text = buf.decode("utf-8", errors="ignore")

                if '"UpdateState"' in text or '"event":"UpdateState"' in text:
                    return True, api_available
                if '"MatchEnded"' in text or '"event":"MatchEnded"' in text:
                    return False, api_available
                if '"MatchDestroyed"' in text or '"event":"MatchDestroyed"' in text:
                    return False, api_available
                if '"RoundStarted"' in text or '"event":"RoundStarted"' in text:
                    return True, api_available

            except socket.timeout:
                return None, api_available
            except OSError:
                return None, api_available

        return None, api_available

    except (OSError, ConnectionError):
        return None, False
    finally:
        if sock:
            try:
                sock.close()
            except OSError:
                pass


# main entry point

def parse_launch_log(
    log_path: str | Path | None = None,
    *,
    verify: bool = True,
    verify_timeout: float = _STATS_VERIFY_TIMEOUT,
    lang: str = "INT",
) -> LogInfo:
    """Parse Launch.log and return session + game info.

    verify=True checks the stats api before returning game data.
    Session data (username, rich presence, ...) is always returned.
    """
    if log_path is None:
        log_path = _find_launch_log()

    log_path = Path(log_path)
    if not log_path.is_file():
        return LogInfo(log_path=str(log_path))

    text = log_path.read_text(encoding="utf-8", errors="replace")

    # psyNet config for playlist names
    build_id = _extract_build_id(text)
    psynet_config: dict = {}
    online_playlists: dict[int, str] = {}
    if build_id:
        psynet_config = fetch_psynet_config(build_id, lang=lang)
        online_playlists = get_online_playlists(psynet_config)

    # session info (always parsed)

    session = LogSessionInfo()

    m = _find_last_match(_RE_USERNAME, text)
    if m:
        session.username = m.group(1)

    m = _find_first_match(_RE_STEAM_ID, text)
    if m:
        session.steam_id = m.group(1)

    m = _find_first_match(_RE_PLATFORM, text)
    if m:
        session.platform = m.group(1)

    m = _find_last_match(_RE_RICH_PRESENCE, text)
    if m:
        session.rich_presence = m.group(1).strip()
        session.rich_presence_data = m.group(2).strip()

    # game info (only after verification)

    game: LogGameInfo | None = None
    stats_available = False
    verified = False

    if verify:
        result, stats_available = _verify_via_stats_api(timeout=verify_timeout)
        verified = result is True
    else:
        stats_available = _check_stats_port()

    if verified or not verify:
        game = _parse_game_info(text, verified, online_playlists)

        # if in-game but map/ip missing, wait a sec and re-read
        # (log gets written progressively during join)
        if verified and game and not game.map_name and not game.server_ip:
            time.sleep(1.0)
            try:
                text2 = log_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text2 = text
            if text2 != text:
                game = _parse_game_info(
                    text2, verified, online_playlists, psynet_config
                )

    return LogInfo(
        session=session,
        game=game,
        log_path=str(log_path),
        parse_time=time.time(),
        stats_api_available=stats_available,
    )


# game info sub-parser

def _parse_game_info(
    text: str,
    verified: bool,
    online_playlists: dict[int, str],
) -> LogGameInfo:
    game = LogGameInfo(verified=verified)

    # playlist id
    m = _find_last_match(_RE_PLAYLIST_ID, text)
    if m:
        game.playlist_id = int(m.group(1))
    else:
        m = _find_last_match(_RE_PLAYLIST, text)
        if m:
            game.playlist_id = int(m.group(1))

    if game.playlist_id is not None:
        game.playlist_name = online_playlists.get(game.playlist_id)

    # welcomed by server (map + game class + tags)
    m = _find_last_match(_RE_WELCOMED, text)
    game_class = ""
    if m:
        game.map_name = m.group(1)
        game_class = m.group(2)
        game.game_tags = m.group(3) or None

    # browse urls (server ip/port for online, map for training/freeplay)
    m_remote = _find_last_match(_RE_BROWSE_REMOTE, text)
    if m_remote:
        game.server_ip = m_remote.group(1)
        try:
            game.server_port = int(m_remote.group(2))
        except ValueError:
            pass

    # no welcomed-by-server map? try the browse url path
    # (covers training/freeplay/exhibition which skip matchmaking)
    if not game.map_name:
        if m_remote:
            path = m_remote.group(3)
            game.map_name = _extract_map_from_browse_path(path)
            if not game_class:
                game_class = _extract_from_browse_query(path, _RE_BROWSE_GAME) or ""
            if not game.game_tags:
                game.game_tags = _extract_from_browse_query(path, _RE_BROWSE_TAGS)

        if not game.map_name or game.map_name.startswith("JoinGameTransition"):
            m_local = _find_last_match(_RE_BROWSE_LOCAL, text)
            if m_local:
                path = m_local.group(1)
                map_name = _extract_map_from_browse_path(path)
                if map_name and map_name != path:
                    game.map_name = map_name
                if not game_class:
                    game_class = _extract_from_browse_query(path, _RE_BROWSE_GAME) or ""
                if not game.game_tags:
                    game.game_tags = _extract_from_browse_query(path, _RE_BROWSE_TAGS)

    # raw game class from the log (TAGame.GameInfo_Soccar_TA etc.)
    if game_class:
        game.game_class = game_class

    # server name / region
    m = _find_last_match(_RE_SERVER_NAME, text)
    if m:
        game.server_name = m.group(1)

    m = _find_last_match(_RE_REGION, text)
    if m:
        game.region = m.group(1)

    return game


def _extract_map_from_browse_path(path: str) -> str | None:
    """Extract map name from a browse url path."""
    path_only = path.split("?")[0]
    if path_only.lower().startswith("joingametransition"):
        return None
    if path_only.lower().startswith("menu_"):
        return None
    if not path_only or (":" in path_only and "/" not in path_only):
        return None
    return path_only


def _extract_from_browse_query(path: str, pattern: re.Pattern) -> str | None:
    m = pattern.search(path)
    return m.group(1) if m else None


# misc

def _extract_build_id(text: str) -> str | None:
    """Extract the numeric build id from Log: BuildID: NNN from GPsyonixBuildID."""
    m = _RE_BUILD_ID.search(text)
    return m.group(1) if m else None


def _find_launch_log() -> str:
    return os.path.join(
        os.environ.get("USERPROFILE", ""),
        "Documents",
        "My Games",
        "Rocket League",
        "TAGame",
        "Logs",
        "Launch.log",
    )


def _check_stats_port() -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex((_STATS_HOST, _STATS_PORT))
        sock.close()
        return result == 0
    except OSError:
        return False
