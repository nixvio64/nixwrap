"""Typed dataclass models for Rocket League save file data.

Every known save object type has a corresponding dataclass with default
values for every field -- this ensures forward/backward compatibility when
the save format changes.

The SaveData container provides lazy cached_property accessors
for every category of data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any


# Top-level containers

@dataclass(slots=True)
class SaveHeader:
    engine_version: int = 0
    licensee_version: int = 0
    type_version: int = 0
    foosball: str = ""
    magic: str = ""


@dataclass(slots=True)
class ParsedObject:
    """A single parsed save object -- always available for all objects,
    including types we don't have typed models for.
    """
    type_name: str
    properties: dict[str, Any] = field(default_factory=dict)
    parse_error: str | None = None


# Player Stats

@dataclass(slots=True)
class ProfileStats:
    wins: int = 0
    mvps: int = 0
    goals: int = 0
    saves: int = 0
    shots: int = 0
    assists: int = 0
    demos: int = 0
    exterminations: int = 0
    first_touches: int = 0
    clears: int = 0
    centers: int = 0
    epic_saves: int = 0
    aerial_goals: int = 0
    backwards_goals: int = 0
    bicycle_goals: int = 0
    long_goals: int = 0
    hat_tricks: int = 0
    overtime_goals: int = 0
    pool_shots: int = 0
    turtle_goals: int = 0
    # Raw fields dict for custom extraction
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ClientXP:
    level: int = 1
    xp: int = 0
    total_xp: int = 0
    current_threshold: int = 0
    next_threshold: int = 0


# Camera & Controls

@dataclass(slots=True)
class CameraSettings:
    fov: float = 90.0
    height: float = 100.0
    angle: float = -3.0
    distance: float = 270.0
    stiffness: float = 0.5
    swivel_speed: float = 2.5
    transition_speed: float = 1.0
    invert_swivel: bool = False
    enable_camera_shake: bool = True
    ball_cam_indicator: bool = True
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ControlsSettings:
    throttle: str = ""
    steer_left: str = ""
    steer_right: str = ""
    jump: str = ""
    boost: str = ""
    powerslide: str = ""
    air_roll: str = ""
    air_roll_left: str = ""
    air_roll_right: str = ""
    focus_on_ball: str = ""
    rear_view: str = ""
    scoreboard: str = ""
    skip_music: str = ""
    voice_chat: str = ""
    push_to_talk: str = ""
    use_item: str = ""
    secondary_use_item: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    raw_bindings: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class GamepadBindings:
    throttle: str = ""
    steer_left: str = ""
    steer_right: str = ""
    jump: str = ""
    boost: str = ""
    powerslide: str = ""
    air_roll: str = ""
    air_roll_left: str = ""
    air_roll_right: str = ""
    focus_on_ball: str = ""
    rear_view: str = ""
    scoreboard: str = ""
    skip_music: str = ""
    voice_chat: str = ""
    push_to_talk: str = ""
    use_item: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    raw_bindings: list[dict[str, Any]] = field(default_factory=list)


# Skill / MMR

@dataclass(slots=True)
class PlaylistSkill:
    playlist_id: int = 0
    mu: float = 0.0
    sigma: float = 0.0
    matches_played: int = 0
    tier: int = 0
    last_played_timestamp: int = 0


# Loadout & Cosmetics

@dataclass(slots=True)
class PlayerLoadout:
    body: int = 0
    decal: int = 0
    wheels: int = 0
    boost: int = 0
    trail: int = 0
    goal_explosion: int = 0
    topper: int = 0
    antenna: int = 0
    engine_audio: int = 0
    primary_color: str | None = None
    secondary_color: str | None = None
    primary_finish: int = 0
    secondary_finish: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LoadoutSet:
    name: str = ""
    team: int = 0
    loadout: PlayerLoadout = field(default_factory=PlayerLoadout)


@dataclass(slots=True)
class PlayerBanner:
    banner_id: int = 0
    title_id: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PlayerAvatarBorder:
    border_id: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


# Inventory

@dataclass(slots=True)
class OnlineProduct:
    product_id: int = 0
    instance_id: str | None = None
    series_id: int = 0
    added_timestamp: int = 0
    attributes: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


# Settings

@dataclass(slots=True)
class GameplaySettings:
    controller_deadzone: float = 0.3
    dodge_deadzone: float = 0.5
    steering_sensitivity: float = 1.0
    aerial_sensitivity: float = 1.0
    vibration: bool = True
    camera_shake: bool = True
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VideoSettings:
    res_width: int = 1920
    res_height: int = 1080
    fullscreen: bool = True
    vsync: bool = False
    render_quality: int = 0
    texture_quality: int = 0
    world_quality: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SoundSettings:
    master_volume: float = 0.5
    music_volume: float = 0.5
    sfx_volume: float = 0.5
    voice_chat_volume: float = 0.5
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MatchmakingSettings:
    regions: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NetworkSettings:
    raw: dict[str, Any] = field(default_factory=dict)


# Quick Chat

@dataclass(slots=True)
class QuickChatBinding:
    slot: int = 0
    message_id: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


# Season / Progression

@dataclass(slots=True)
class SeasonProgress:
    season_level: int = 0
    season_xp: int = 0
    season_id: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AchievementProgress:
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TutorialProgress:
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TrainingProgress:
    raw: dict[str, Any] = field(default_factory=dict)


# Profile

@dataclass(slots=True)
class PlayerProfile:
    title_id: int | None = None
    persona: dict[str, Any] | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BanInfo:
    raw: dict[str, Any] = field(default_factory=dict)


# Other

@dataclass(slots=True)
class MusicPlaylist:
    songs: list[int] = field(default_factory=list)
    volume: float = 0.5
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Notification:
    id: str = ""
    read: bool = False
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CrumbTrail:
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MapPreferences:
    liked: list[str] = field(default_factory=list)
    disliked: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
