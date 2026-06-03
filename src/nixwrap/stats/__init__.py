"""RL Stats API client. Connects to game local TCP socket for live match events."""

from nixwrap.stats._models import (       # noqa: F401
    PlayerRef, Vector3, BallState, TeamState, TargetState, BallTouch,
    PlayerState, GameState,
    StatsEvent, UpdateStateEvent, BallHitEvent, CrossbarHitEvent,
    ClockUpdatedSecondsEvent, GoalScoredEvent, StatfeedEventData,
    MatchEndedEvent,
)
from nixwrap.stats._client import StatsClient  # noqa: F401

__all__ = [
    "StatsClient",
    "StatsEvent",
    "UpdateStateEvent",
    "BallHitEvent",
    "CrossbarHitEvent",
    "ClockUpdatedSecondsEvent",
    "GoalScoredEvent",
    "StatfeedEventData",
    "MatchEndedEvent",
    "PlayerState",
    "GameState",
    "PlayerRef",
]
