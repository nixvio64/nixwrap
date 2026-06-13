"""Dataclasses for parsed Launch.log data."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class LogSessionInfo:
    """Session info that's always available regardless of match state."""

    username: str | None = None
    steam_id: str | None = None
    platform: str | None = None
    rich_presence: str | None = None
    rich_presence_data: str | None = None


@dataclass(slots=True)
class LogGameInfo:
    """Match info only valid when Stats API confirms in-game."""

    verified: bool = False
    playlist_id: int | None = None
    playlist_name: str | None = None
    game_class: str | None = None
    map_name: str | None = None
    game_tags: str | None = None
    server_name: str | None = None
    region: str | None = None
    server_ip: str | None = None
    server_port: int | None = None


@dataclass(slots=True)
class LogInfo:
    """Top level container for everything extracted from the log."""

    session: LogSessionInfo = field(default_factory=LogSessionInfo)
    game: LogGameInfo | None = None
    log_path: str | None = None
    parse_time: float = 0.0
    stats_api_available: bool = False
