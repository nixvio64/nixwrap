"""Typed dataclass models for tracker.gg API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class PlaylistRank:
    """A player's rank in a single playlist."""
    playlist_id: int = 0
    playlist_name: str = ""
    tier_id: int = 0
    tier_name: str = "Unranked"
    division_id: int = 0        # 1-4
    division_name: str = "Division I"
    mmr: int = 0
    matches_played: int = 0
    peak_mmr: int = 0
    peak_tier_id: int = 0
    peak_div_id: int = 0
    delta_up: int = 0           # MMR needed to promote
    delta_down: int = 0         # MMR needed to demote
    win_streak: int = 0
    win_streak_type: str = ""   # "win" or "loss"
    rank_percentile: float = 0.0


@dataclass(slots=True)
class LifetimeStats:
    """Aggregated lifetime stats from the overview segment."""
    wins: int = 0
    goals: int = 0
    mvps: int = 0
    saves: int = 0
    assists: int = 0
    shots: int = 0
    goal_shot_ratio: float = 0.0
    trn_score: float = 0.0
    season_reward_level: int = 0
    season_reward_wins: int = 0


@dataclass(slots=True)
class PlaylistAverage:
    """Per-playlist average stats."""
    playlist_id: int = 0
    playlist_name: str = ""
    matches: int = 0
    rating: int = 0
    avg_goals_per_game: float = 0.0
    avg_shots_per_game: float = 0.0
    avg_saves_per_game: float = 0.0
    avg_assists_per_game: float = 0.0
    avg_mvps_per_game: float = 0.0
    goals_shots_ratio: float = 0.0
    goals_saves_ratio: float = 0.0
    assists_goals_ratio: float = 0.0


@dataclass(slots=True)
class PlayerStats:
    """Complete player profile from tracker.gg."""
    primary_id: str = ""
    display_name: str = ""
    platform: str = ""
    platform_user_handle: str = ""
    avatar_url: str = ""
    player_id: int = 0
    ranks: dict[int, PlaylistRank] = field(default_factory=dict)
    lifetime: LifetimeStats | None = None
    averages: dict[int, PlaylistAverage] = field(default_factory=dict)
    last_updated: datetime | None = None
    current_season: int = 0
    fetched_at: float = 0.0
    error: str | None = None
    not_found: bool = False
