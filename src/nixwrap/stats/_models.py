"""Typed dataclasses for every Rocket League Stats API event.

Based on the StatsAPI.md documentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Primitives

@dataclass(slots=True)
class PlayerRef:
    name: str = ""
    shortcut: int = 0
    team_num: int = 0


@dataclass(slots=True)
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass(slots=True)
class BallState:
    speed: float = 0.0
    team_num: int = 255


@dataclass(slots=True)
class TeamState:
    name: str = ""
    team_num: int = 0
    score: int = 0
    color_primary: str = "0000FF"
    color_secondary: str = "0000AA"


@dataclass(slots=True)
class TargetState:
    name: str = ""
    shortcut: int = 0
    team_num: int = 0


@dataclass(slots=True)
class BallTouch:
    player: PlayerRef = field(default_factory=PlayerRef)
    speed: float = 0.0


# Player (UpdateState)

@dataclass(slots=True)
class PlayerState:
    name: str = ""
    primary_id: str = ""
    shortcut: int = 0
    team_num: int = 0
    score: int = 0
    goals: int = 0
    shots: int = 0
    assists: int = 0
    saves: int = 0
    touches: int = 0
    car_touches: int = 0
    demos: int = 0
    # spectator-only
    has_car: bool = False
    speed: float = 0.0
    boost: int = 0
    boosting: bool = False
    on_ground: bool = False
    on_wall: bool = False
    powersliding: bool = False
    demolished: bool = False
    supersonic: bool = False
    attacker: PlayerRef | None = None


# Game (UpdateState)

@dataclass(slots=True)
class GameState:
    teams: list[TeamState] = field(default_factory=list)
    time_seconds: int = 300
    overtime: bool = False
    ball: BallState = field(default_factory=BallState)
    replay: bool = False
    has_winner: bool = False
    winner: str = ""
    arena: str = ""
    has_target: bool = False
    target: TargetState | None = None
    frame: int = 0
    elapsed: float = 0.0


# Event base

@dataclass(slots=True)
class StatsEvent:
    """Base for all Stats API events."""
    event_type: str = ""
    match_guid: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


# Specific events

@dataclass(slots=True)
class UpdateStateEvent(StatsEvent):
    players: list[PlayerState] = field(default_factory=list)
    game: GameState = field(default_factory=GameState)


@dataclass(slots=True)
class BallHitEvent(StatsEvent):
    players: list[PlayerRef] = field(default_factory=list)
    ball_pre_hit_speed: float = 0.0
    ball_post_hit_speed: float = 0.0
    ball_location: Vector3 = field(default_factory=Vector3)


@dataclass(slots=True)
class CrossbarHitEvent(StatsEvent):
    ball_speed: float = 0.0
    impact_force: float = 0.0
    ball_location: Vector3 = field(default_factory=Vector3)
    ball_last_touch: BallTouch = field(default_factory=BallTouch)


@dataclass(slots=True)
class ClockUpdatedSecondsEvent(StatsEvent):
    time_seconds: int = 0
    overtime: bool = False


@dataclass(slots=True)
class GoalScoredEvent(StatsEvent):
    goal_speed: float = 0.0
    goal_time: float = 0.0
    impact_location: Vector3 = field(default_factory=Vector3)
    scorer: PlayerRef = field(default_factory=PlayerRef)
    assister: PlayerRef | None = None
    ball_last_touch: BallTouch = field(default_factory=BallTouch)


@dataclass(slots=True)
class StatfeedEventData(StatsEvent):
    stat_name: str = ""        # e.g. "Demolish"
    stat_type: str = ""         # e.g. "Demolition"
    main_target: PlayerRef = field(default_factory=PlayerRef)
    secondary_target: PlayerRef | None = None


@dataclass(slots=True)
class MatchEndedEvent(StatsEvent):
    winner_team_num: int = -1


# Simple events (no extra data beyond MatchGuid):
# CountdownBegin, GoalReplayStart, GoalReplayEnd, GoalReplayWillEnd,
# MatchCreated, MatchInitialized, MatchDestroyed, MatchPaused,
# MatchUnpaused, PodiumStart, ReplayCreated, RoundStarted
