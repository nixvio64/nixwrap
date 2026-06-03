"""JSON message extraction and Stats API event parsing."""

from __future__ import annotations

import json
from typing import Any

from nixwrap.stats._models import (
    PlayerRef, Vector3, BallState, TeamState, TargetState, BallTouch,
    PlayerState, GameState,
    StatsEvent,
    UpdateStateEvent, BallHitEvent, CrossbarHitEvent,
    ClockUpdatedSecondsEvent, GoalScoredEvent, StatfeedEventData,
    MatchEndedEvent,
)


# TCP stream extraction

def extract_json_objects(buf: bytes) -> tuple[list[bytes], bytes]:
    """Extract complete JSON objects from a raw TCP buffer.

    Returns a list of raw JSON byte-strings and the remaining unparsed
    data.  Handles nested braces and escaped quotes.
    """
    objects: list[bytes] = []
    i = 0
    while i < len(buf):
        if buf[i:i + 1] == b"{":
            depth, in_str, escape = 0, False, False
            j = i
            while j < len(buf):
                c = buf[j:j + 1]
                if escape:
                    escape = False
                elif c == b"\\":
                    escape = True
                elif c == b'"' and not escape:
                    in_str = not in_str
                elif not in_str:
                    if c == b"{":
                        depth += 1
                    elif c == b"}":
                        depth -= 1
                        if depth == 0:
                            objects.append(buf[i:j + 1])
                            i = j + 1
                            break
                j += 1
            else:
                break
        else:
            i += 1
    return objects, buf[i:]


# Event parsing

def parse_message(raw: str | bytes) -> StatsEvent:
    """Parse a single JSON Stats API message into a typed event.

    Parameters
    raw:
        Raw JSON string or bytes.

    Returns
    StatsEvent
        The parsed event (specific subclass like UpdateStateEvent).
    """
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    msg: dict = json.loads(raw)
    evt = msg.get("Event", "")
    data: dict = msg.get("Data", {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            data = {}

    match_guid = data.get("MatchGuid")

    if evt == "UpdateState":
        return _parse_update_state(data, match_guid)
    elif evt == "BallHit":
        return _parse_ball_hit(data, match_guid)
    elif evt == "CrossbarHit":
        return _parse_crossbar_hit(data, match_guid)
    elif evt == "ClockUpdatedSeconds":
        return _parse_clock_updated(data, match_guid)
    elif evt == "GoalScored":
        return _parse_goal_scored(data, match_guid)
    elif evt == "StatfeedEvent":
        return _parse_statfeed(data, match_guid)
    elif evt == "MatchEnded":
        return _parse_match_ended(data, match_guid)
    else:
        # Simple event (CountdownBegin, MatchCreated, etc.)
        return StatsEvent(
            event_type=evt,
            match_guid=match_guid,
            raw_data=data,
        )


# Internal parsers

def _parse_player_ref(d: dict) -> PlayerRef:
    return PlayerRef(
        name=d.get("Name", ""),
        shortcut=d.get("Shortcut", 0),
        team_num=d.get("TeamNum", 0),
    )


def _parse_vector3(d: dict) -> Vector3:
    return Vector3(
        x=d.get("X", 0.0),
        y=d.get("Y", 0.0),
        z=d.get("Z", 0.0),
    )


def _parse_update_state(data: dict, match_guid: str | None) -> UpdateStateEvent:
    players = []
    for p in data.get("Players", []):
        attacker = None
        if p.get("Attacker"):
            attacker = _parse_player_ref(p["Attacker"])
        players.append(PlayerState(
            name=p.get("Name", ""),
            primary_id=p.get("PrimaryId", ""),
            shortcut=p.get("Shortcut", 0),
            team_num=p.get("TeamNum", 0),
            score=p.get("Score", 0),
            goals=p.get("Goals", 0),
            shots=p.get("Shots", 0),
            assists=p.get("Assists", 0),
            saves=p.get("Saves", 0),
            touches=p.get("Touches", 0),
            car_touches=p.get("CarTouches", 0),
            demos=p.get("Demos", 0),
            has_car=p.get("bHasCar", False),
            speed=p.get("Speed", 0.0),
            boost=p.get("Boost", 0),
            boosting=p.get("bBoosting", False),
            on_ground=p.get("bOnGround", False),
            on_wall=p.get("bOnWall", False),
            powersliding=p.get("bPowersliding", False),
            demolished=p.get("bDemolished", False),
            supersonic=p.get("bSupersonic", False),
            attacker=attacker,
        ))

    game = data.get("Game", {})
    teams = []
    for t in game.get("Teams", []):
        teams.append(TeamState(
            name=t.get("Name", ""),
            team_num=t.get("TeamNum", 0),
            score=t.get("Score", 0),
            color_primary=t.get("ColorPrimary", ""),
            color_secondary=t.get("ColorSecondary", ""),
        ))

    ball = game.get("Ball", {})
    ball_state = BallState(
        speed=ball.get("Speed", 0.0),
        team_num=ball.get("TeamNum", 255),
    )

    target = None
    tgt = game.get("Target")
    if tgt:
        target = TargetState(
            name=tgt.get("Name", ""),
            shortcut=tgt.get("Shortcut", 0),
            team_num=tgt.get("TeamNum", 0),
        )

    return UpdateStateEvent(
        event_type="UpdateState",
        match_guid=match_guid,
        raw_data=data,
        players=players,
        game=GameState(
            teams=teams,
            time_seconds=game.get("TimeSeconds", 300),
            overtime=game.get("bOvertime", False),
            ball=ball_state,
            replay=game.get("bReplay", False),
            has_winner=game.get("bHasWinner", False),
            winner=game.get("Winner", ""),
            arena=game.get("Arena", ""),
            has_target=game.get("bHasTarget", False),
            target=target,
            frame=game.get("Frame", 0),
            elapsed=game.get("Elapsed", 0.0),
        ),
    )


def _parse_ball_hit(data: dict, match_guid: str | None) -> BallHitEvent:
    players = [_parse_player_ref(p) for p in data.get("Players", [])]
    ball = data.get("Ball", {})
    loc = ball.get("Location", {})
    return BallHitEvent(
        event_type="BallHit",
        match_guid=match_guid,
        raw_data=data,
        players=players,
        ball_pre_hit_speed=ball.get("PreHitSpeed", 0.0),
        ball_post_hit_speed=ball.get("PostHitSpeed", 0.0),
        ball_location=_parse_vector3(loc),
    )


def _parse_crossbar_hit(data: dict, match_guid: str | None) -> CrossbarHitEvent:
    bt = data.get("BallLastTouch", {})
    p = bt.get("Player", {})
    loc = data.get("BallLocation", {})
    return CrossbarHitEvent(
        event_type="CrossbarHit",
        match_guid=match_guid,
        raw_data=data,
        ball_speed=data.get("BallSpeed", 0.0),
        impact_force=data.get("ImpactForce", 0.0),
        ball_location=_parse_vector3(loc),
        ball_last_touch=BallTouch(
            player=_parse_player_ref(p),
            speed=bt.get("Speed", 0.0),
        ),
    )


def _parse_clock_updated(data: dict, match_guid: str | None) -> ClockUpdatedSecondsEvent:
    return ClockUpdatedSecondsEvent(
        event_type="ClockUpdatedSeconds",
        match_guid=match_guid,
        raw_data=data,
        time_seconds=data.get("TimeSeconds", 0),
        overtime=data.get("bOvertime", False),
    )


def _parse_goal_scored(data: dict, match_guid: str | None) -> GoalScoredEvent:
    assister = None
    if data.get("Assister"):
        assister = _parse_player_ref(data["Assister"])
    bt = data.get("BallLastTouch", {})
    p = bt.get("Player", {})
    loc = data.get("ImpactLocation", {})
    return GoalScoredEvent(
        event_type="GoalScored",
        match_guid=match_guid,
        raw_data=data,
        goal_speed=data.get("GoalSpeed", 0.0),
        goal_time=data.get("GoalTime", 0.0),
        impact_location=_parse_vector3(loc),
        scorer=_parse_player_ref(data.get("Scorer", {})),
        assister=assister,
        ball_last_touch=BallTouch(
            player=_parse_player_ref(p),
            speed=bt.get("Speed", 0.0),
        ),
    )


def _parse_statfeed(data: dict, match_guid: str | None) -> StatfeedEventData:
    st = None
    if data.get("SecondaryTarget"):
        st = _parse_player_ref(data["SecondaryTarget"])
    return StatfeedEventData(
        event_type="StatfeedEvent",
        match_guid=match_guid,
        raw_data=data,
        stat_name=data.get("EventName", ""),
        stat_type=data.get("Type", ""),
        main_target=_parse_player_ref(data.get("MainTarget", {})),
        secondary_target=st,
    )


def _parse_match_ended(data: dict, match_guid: str | None) -> MatchEndedEvent:
    return MatchEndedEvent(
        event_type="MatchEnded",
        match_guid=match_guid,
        raw_data=data,
        winner_team_num=data.get("WinnerTeamNum", -1),
    )
