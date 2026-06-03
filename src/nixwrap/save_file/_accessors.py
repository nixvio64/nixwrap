"""Typed extraction functions and the SaveData container.

Maps raw parse dicts from parse_savedata() into the typed dataclass
models defined in _models.py, using the real property names
observed in Rocket League save files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

from nixwrap.save_file._models import (
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


# Helpers

def _get_object(objects: list[dict], type_name: str) -> dict | None:
    for obj in objects:
        if obj.get("__type") == type_name:
            return obj
    return None


def _get_objects(objects: list[dict], type_name: str) -> list[dict]:
    return [obj for obj in objects if obj.get("__type") == type_name]


def _safe_int(obj: dict, key: str, default: int = 0) -> int:
    try:
        return int(obj.get(key, default))
    except (TypeError, ValueError):
        return default


def _safe_float(obj: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(obj.get(key, default))
    except (TypeError, ValueError):
        return default


def _safe_str(obj: dict, key: str, default: str = "") -> str:
    val = obj.get(key, default)
    return str(val) if val is not None else default


def _safe_bool(obj: dict, key: str, default: bool = False) -> bool:
    val = obj.get(key, default)
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return bool(val)
    return default


def _resolve_ref(objects: list[dict], index: int) -> dict | None:
    """Resolve an object reference (integer index) from the objects list."""
    if 0 <= index < len(objects):
        return objects[index]
    return None


# Typed extractors

def parse_profile_stats(raw: dict | None) -> ProfileStats | None:
    """Parse ProfileStatsSave_TA.

    Stats are stored as StatValues: a list of {Id: str, Values: [online, offline, training]}.
    We extract the online value (index 0) for each known stat.
    """
    if raw is None:
        return None
    stat_values = raw.get("StatValues", [])
    if not isinstance(stat_values, list):
        return ProfileStats(raw=raw)

    # Build lookup: stat_id -> online_value
    lookup: dict[str, int] = {}
    for sv in stat_values:
        if isinstance(sv, dict):
            sid = sv.get("Id", "")
            vals = sv.get("Values", [])
            if isinstance(vals, list) and vals:
                lookup[str(sid).lower()] = int(vals[0]) if vals[0] else 0

    def _s(key: str) -> int:
        return lookup.get(key.lower(), 0)

    return ProfileStats(
        wins=_s("Win"),
        mvps=_s("MVP"),
        goals=_s("Goal"),
        saves=_s("Save"),
        shots=_s("Shot"),
        assists=_s("Assist"),
        demos=_s("Demolish"),
        exterminations=_s("Extermination"),
        first_touches=_s("FirstTouch"),
        clears=_s("Clear"),
        centers=_s("Center"),
        epic_saves=_s("EpicSave"),
        aerial_goals=_s("AerialGoal"),
        backwards_goals=_s("BackwardsGoal"),
        bicycle_goals=_s("BicycleGoal"),
        long_goals=_s("LongGoal"),
        hat_tricks=_s("HatTrick"),
        overtime_goals=_s("OvertimeGoal"),
        pool_shots=_s("PoolShot"),
        turtle_goals=_s("TurtleGoal"),
        raw=raw,
    )


def parse_client_xp(raw: dict | None) -> ClientXP | None:
    """Parse ClientXPSave_TA."""
    if raw is None:
        return None
    return ClientXP(
        level=_safe_int(raw, "Level", 1),
        xp=0,  # not stored directly
        total_xp=_safe_int(raw, "TotalXP"),
        current_threshold=_safe_int(raw, "CurrentLevelXPThreshold"),
        next_threshold=_safe_int(raw, "NextLevelXPThreshold"),
    )


def parse_camera_settings(raw: dict | None) -> CameraSettings | None:
    """Parse ProfileCameraSave_TA.

    Camera settings are nested in a Camera struct property.
    """
    if raw is None:
        return None
    cam = raw.get("Camera", {})
    if not isinstance(cam, dict):
        cam = {}
    return CameraSettings(
        fov=_safe_float(cam, "FOV", 90.0),
        height=_safe_float(cam, "Height", 100.0),
        angle=_safe_float(cam, "Angle", -3.0),
        distance=_safe_float(cam, "Distance", 270.0),
        stiffness=_safe_float(cam, "Stiffness", 0.5),
        swivel_speed=_safe_float(cam, "SwivelSpeed", 2.5),
        transition_speed=_safe_float(cam, "TransitionSpeed", 1.0),
        invert_swivel=_safe_bool(raw, "bInvertSwivelPitch"),
        enable_camera_shake=_safe_bool(raw, "bEnableCameraShake", True),
        ball_cam_indicator=True,
        raw=raw,
    )


def _parse_bindings_array(bindings: list[dict]) -> dict[str, str]:
    """Convert a GamepadBindings/PCBindings array to a flat {action: key} dict."""
    result: dict[str, str] = {}
    for b in bindings:
        if isinstance(b, dict):
            action = _safe_str(b, "Action")
            key = _safe_str(b, "Key")
            if action:
                result[action] = key
    return result


def parse_controls_settings(raw: dict | None) -> ControlsSettings | None:
    """Parse ProfilePCSave_TA (keyboard/mouse bindings).

    Keyboard bindings are in the PCBindings array.
    """
    if raw is None:
        return None
    bindings = raw.get("PCBindings", [])
    if not isinstance(bindings, list):
        bindings = []
    bm = _parse_bindings_array(bindings)
    return ControlsSettings(
        throttle=bm.get("Throttle", ""),
        steer_left=bm.get("SteerLeft", ""),
        steer_right=bm.get("SteerRight", ""),
        jump=bm.get("Jump", ""),
        boost=bm.get("Boost", ""),
        powerslide=bm.get("Powerslide", bm.get("Handbrake", "")),
        air_roll=bm.get("AirRoll", ""),
        air_roll_left=bm.get("AirRollLeft", ""),
        air_roll_right=bm.get("AirRollRight", ""),
        focus_on_ball=bm.get("FocusOnBall", bm.get("BallCam", "")),
        rear_view=bm.get("RearView", bm.get("LookBack", "")),
        scoreboard=bm.get("Scoreboard", ""),
        skip_music=bm.get("SkipMusic", ""),
        voice_chat=bm.get("VoiceChat", ""),
        push_to_talk=bm.get("PushToTalk", ""),
        use_item=bm.get("UseItem", ""),
        secondary_use_item=bm.get("SecondaryUseItem", ""),
        raw=raw,
        raw_bindings=bindings,
    )


def parse_gamepad_bindings(raw: dict | None) -> GamepadBindings | None:
    """Parse ProfileGamepadSave_TA (controller bindings)."""
    if raw is None:
        return None
    bindings = raw.get("GamepadBindings", [])
    if not isinstance(bindings, list):
        bindings = []
    bm = _parse_bindings_array(bindings)
    return GamepadBindings(
        throttle=bm.get("Throttle", ""),
        steer_left=bm.get("SteerLeft", ""),
        steer_right=bm.get("SteerRight", ""),
        jump=bm.get("Jump", ""),
        boost=bm.get("Boost", ""),
        powerslide=bm.get("Powerslide", bm.get("Handbrake", "")),
        air_roll=bm.get("AirRoll", ""),
        air_roll_left=bm.get("AirRollLeft", ""),
        air_roll_right=bm.get("AirRollRight", ""),
        focus_on_ball=bm.get("FocusOnBall", bm.get("BallCam", "")),
        rear_view=bm.get("RearView", bm.get("LookBack", "")),
        scoreboard=bm.get("Scoreboard", ""),
        skip_music=bm.get("SkipMusic", ""),
        voice_chat=bm.get("VoiceChat", ""),
        push_to_talk=bm.get("PushToTalk", ""),
        use_item=bm.get("UseItem", ""),
        raw=raw,
        raw_bindings=bindings,
    )


def parse_playlist_skills(raw: dict | None) -> dict[int, PlaylistSkill]:
    """Parse PlaylistSkillDataSave_TA.

    Skill data is in the SkillData array with
    {Playlist, Tier, MatchesPlayed} per entry.
    """
    if raw is None:
        return {}
    skills: dict[int, PlaylistSkill] = {}
    skill_data = raw.get("SkillData", [])
    if isinstance(skill_data, list):
        for item in skill_data:
            if not isinstance(item, dict):
                continue
            pid = _safe_int(item, "Playlist")
            skills[pid] = PlaylistSkill(
                playlist_id=pid,
                mu=0.0,
                sigma=0.0,
                matches_played=_safe_int(item, "MatchesPlayed"),
                tier=_safe_int(item, "Tier"),
                last_played_timestamp=0,
            )
    return skills


def parse_player_loadout(raw: dict | None) -> PlayerLoadout | None:
    """Parse a Loadout_TA object into PlayerLoadout."""
    if raw is None:
        return None
    # Loadout items reference OnlineProduct objects
    equipped = raw.get("EquippedProducts", [])
    if not isinstance(equipped, list):
        equipped = []
    # Build a slot -> product_id map
    slot_map: dict[int, int] = {}
    for item in equipped:
        if isinstance(item, dict):
            slot = _safe_int(item, "SlotIndex")
            pid = _safe_int(item, "ProductID")
            slot_map[slot] = pid

    return PlayerLoadout(
        body=slot_map.get(0, 0),
        decal=slot_map.get(1, 0),
        wheels=slot_map.get(2, 0),
        boost=slot_map.get(3, 0),
        trail=slot_map.get(4, 0),
        goal_explosion=slot_map.get(5, 0),
        topper=slot_map.get(6, 0),
        antenna=slot_map.get(7, 0),
        engine_audio=slot_map.get(8, 0),
        raw=raw,
    )


def parse_online_product(raw: dict) -> OnlineProduct:
    inst = raw.get("InstanceID", {})
    instance_id = None
    if isinstance(inst, dict):
        lb = inst.get("LowerBits")
        if lb is not None:
            instance_id = str(lb)
    elif isinstance(inst, str):
        instance_id = inst

    return OnlineProduct(
        product_id=_safe_int(raw, "ProductID"),
        instance_id=instance_id,
        series_id=_safe_int(raw, "SeriesID"),
        added_timestamp=_safe_int(raw, "AddedTimestamp"),
        attributes={k: v for k, v in raw.items()
                    if k not in ("__type", "ProductID", "InstanceID",
                                  "SeriesID", "AddedTimestamp")},
        raw=raw,
    )


def parse_gameplay_settings(raw: dict | None) -> GameplaySettings | None:
    """Parse GameplaySettingsSave_TA and ProfileGamepadSave_TA."""
    if raw is None:
        return None
    return GameplaySettings(
        controller_deadzone=_safe_float(raw, "ControllerDeadzone", 0.3),
        dodge_deadzone=_safe_float(raw, "DodgeInputThreshold", 0.5),
        steering_sensitivity=_safe_float(raw, "SteeringSensitivity", 1.0),
        aerial_sensitivity=_safe_float(raw, "AirControlSensitivity", 1.0),
        vibration=True,
        camera_shake=True,
        raw=raw,
    )


def parse_video_settings(raw: dict | None) -> VideoSettings | None:
    if raw is None:
        return None
    return VideoSettings(
        res_width=_safe_int(raw, "ResolutionWidth", 1920),
        res_height=_safe_int(raw, "ResolutionHeight", 1080),
        fullscreen=_safe_bool(raw, "Fullscreen"),
        vsync=_safe_bool(raw, "VSync"),
        render_quality=_safe_int(raw, "RenderQuality"),
        texture_quality=_safe_int(raw, "TextureQuality"),
        world_quality=_safe_int(raw, "WorldQuality"),
        raw=raw,
    )


def parse_sound_settings(raw: dict | None) -> SoundSettings | None:
    if raw is None:
        return None
    return SoundSettings(
        master_volume=_safe_float(raw, "MasterVolume", 0.5),
        music_volume=_safe_float(raw, "MusicVolume", 0.5),
        sfx_volume=_safe_float(raw, "SFXVolume", 0.5),
        voice_chat_volume=_safe_float(raw, "VoiceChatVolume", 0.5),
        raw=raw,
    )


def parse_matchmaking_settings(raw: dict | None) -> MatchmakingSettings | None:
    if raw is None:
        return None
    regions = raw.get("Regions", [])
    if isinstance(regions, list):
        return MatchmakingSettings(regions=[str(r) for r in regions], raw=raw)
    return MatchmakingSettings(raw=raw)


def parse_quick_chats(raw: dict | None) -> list[QuickChatBinding]:
    """Parse ProfileQuickChatSave_TA.

    Bindings are stored as an array of strings like "Group1Message1".
    """
    if raw is None:
        return []
    binds = raw.get("QuickChatBindings", [])
    if not isinstance(binds, list):
        return []
    result: list[QuickChatBinding] = []
    for i, msg in enumerate(binds):
        result.append(QuickChatBinding(slot=i, message_id=str(msg), raw={"message": str(msg)}))
    return result


def parse_season_progress(raw: dict | None) -> SeasonProgress | None:
    if raw is None:
        return None
    return SeasonProgress(
        season_level=_safe_int(raw, "SeasonLevel"),
        season_xp=_safe_int(raw, "SeasonXP"),
        season_id=_safe_int(raw, "SeasonID"),
        raw=raw,
    )


def parse_player_profile(raw: dict | None) -> PlayerProfile | None:
    if raw is None:
        return None
    return PlayerProfile(
        title_id=raw.get("TitleID"),
        raw=raw,
    )


def parse_music_playlist(raw: dict | None) -> MusicPlaylist | None:
    if raw is None:
        return None
    songs = raw.get("Songs", [])
    if isinstance(songs, list):
        return MusicPlaylist(
            songs=[_safe_int({"v": s}, "v") for s in songs],
            volume=_safe_float(raw, "Volume", 0.5),
            raw=raw,
        )
    return MusicPlaylist(raw=raw)


def parse_notifications(raw: dict | None) -> list[Notification]:
    if raw is None:
        return []
    notifs = raw.get("Notifications", [])
    if not isinstance(notifs, list):
        return []
    result: list[Notification] = []
    for n in notifs:
        if isinstance(n, dict):
            result.append(Notification(
                id=_safe_str(n, "ID"),
                read=_safe_bool(n, "Read"),
                raw=n,
            ))
    return result


def parse_map_prefs(raw: dict | None) -> MapPreferences | None:
    if raw is None:
        return None
    liked = raw.get("LikedMaps", [])
    disliked = raw.get("DislikedMaps", [])
    return MapPreferences(
        liked=list(liked) if isinstance(liked, list) else [],
        disliked=list(disliked) if isinstance(disliked, list) else [],
        raw=raw,
    )


# SaveData container

@dataclass
class SaveData:
    """Fully typed container for parsed Rocket League save data.

    All accessors are lazy cached_property -- they only parse their
    specific object type on first access.

    Usage:

        save = load("myfile.save")
        print(save.camera.fov)
        print(save.stats.wins)
        print(save.controls.jump)
    """

    source_file: Path
    header: SaveHeader
    raw_properties: dict[str, Any]
    objects: list[dict[str, Any]]

    # Player Stats

    @cached_property
    def stats(self) -> ProfileStats | None:
        raw = _get_object(self.objects, "TAGame.ProfileStatsSave_TA")
        return parse_profile_stats(raw)

    @cached_property
    def xp(self) -> ClientXP | None:
        raw = _get_object(self.objects, "TAGame.ClientXPSave_TA")
        return parse_client_xp(raw)

    # Camera & Controls

    @cached_property
    def camera(self) -> CameraSettings | None:
        raw = _get_object(self.objects, "TAGame.ProfileCameraSave_TA")
        return parse_camera_settings(raw)

    @cached_property
    def controls(self) -> ControlsSettings | None:
        """Keyboard/mouse bindings from ProfilePCSave_TA."""
        raw = _get_object(self.objects, "TAGame.ProfilePCSave_TA")
        return parse_controls_settings(raw)

    @cached_property
    def gamepad_bindings(self) -> GamepadBindings | None:
        raw = _get_object(self.objects, "TAGame.ProfileGamepadSave_TA")
        return parse_gamepad_bindings(raw)

    # Skill / MMR

    @cached_property
    def skills(self) -> dict[int, PlaylistSkill]:
        raw = _get_object(self.objects, "TAGame.PlaylistSkillDataSave_TA")
        return parse_playlist_skills(raw)

    # Loadout & Cosmetics

    @cached_property
    def loadout(self) -> PlayerLoadout | None:
        """Currently equipped loadout from the active Loadout_TA object."""
        # ProfileLoadoutSave_TA has EquippedLoadoutSet: references a LoadoutSet_TA
        # LoadoutSet_TA has LoadoutRef: references a Loadout_TA
        profile_lo = _get_object(self.objects, "TAGame.ProfileLoadoutSave_TA")
        if profile_lo is None:
            return None
        # Get the equipped LoadoutSet ref
        set_ref = profile_lo.get("EquippedLoadoutSet")
        if not isinstance(set_ref, int):
            return None
        set_obj = _resolve_ref(self.objects, set_ref)
        if set_obj is None:
            return None
        # Get the Loadout ref from the set
        lo_ref = set_obj.get("LoadoutRef")
        if isinstance(lo_ref, int):
            lo_obj = _resolve_ref(self.objects, lo_ref)
            if lo_obj:
                return parse_player_loadout(lo_obj)
        return None

    @cached_property
    def loadout_sets(self) -> list[LoadoutSet]:
        raw_sets = _get_objects(self.objects, "TAGame.LoadoutSet_TA")
        result: list[LoadoutSet] = []
        for rset in raw_sets:
            name = _safe_str(rset, "SetName", "?")
            team = _safe_int(rset, "SetColor")
            loadout = None
            lo_ref = rset.get("LoadoutRef")
            if isinstance(lo_ref, int):
                lo_obj = _resolve_ref(self.objects, lo_ref)
                if lo_obj:
                    loadout = parse_player_loadout(lo_obj)
            result.append(LoadoutSet(
                name=name,
                team=team,
                loadout=loadout or PlayerLoadout(),
            ))
        return result

    @cached_property
    def banner(self) -> PlayerBanner | None:
        raw = _get_object(self.objects, "TAGame.PlayerBannerSave_TA")
        if raw is None:
            return None
        return PlayerBanner(
            banner_id=_safe_int(raw, "BannerID"),
            title_id=_safe_int(raw, "TitleID"),
            raw=raw,
        )

    @cached_property
    def avatar_border(self) -> PlayerAvatarBorder | None:
        raw = _get_object(self.objects, "TAGame.PlayerAvatarBorderSave_TA")
        if raw is None:
            return None
        return PlayerAvatarBorder(
            border_id=_safe_int(raw, "BorderID"),
            raw=raw,
        )

    # Inventory

    @cached_property
    def inventory(self) -> list[OnlineProduct]:
        products = _get_objects(self.objects, "TAGame.OnlineProduct_TA")
        return [parse_online_product(p) for p in products]

    @cached_property
    def archived_products(self) -> list[OnlineProduct]:
        raw = _get_object(self.objects, "TAGame.ProductsArchiveSave_TA")
        if raw is None:
            return []
        arch = raw.get("ArchivedProducts", [])
        if not isinstance(arch, list):
            return []
        return [parse_online_product(p) for p in arch if isinstance(p, dict)]

    @cached_property
    def favorite_products(self) -> list[int]:
        raw = _get_object(self.objects, "TAGame.ProductsFavoriteSave_TA")
        if raw is None:
            return []
        favs = raw.get("FavoritedProducts", [])
        if isinstance(favs, list):
            return [_safe_int({"v": f}, "v") for f in favs]
        return []

    # Settings

    @cached_property
    def gameplay(self) -> GameplaySettings | None:
        """Gamepad settings from ProfileGamepadSave_TA."""
        raw = _get_object(self.objects, "TAGame.ProfileGamepadSave_TA")
        return parse_gameplay_settings(raw)

    @cached_property
    def video(self) -> VideoSettings | None:
        raw = _get_object(self.objects, "TAGame.VideoSettingsSavePC_TA")
        return parse_video_settings(raw)

    @cached_property
    def sound(self) -> SoundSettings | None:
        raw = _get_object(self.objects, "TAGame.SoundSettingsSave_TA")
        return parse_sound_settings(raw)

    @cached_property
    def matchmaking(self) -> MatchmakingSettings | None:
        raw = _get_object(self.objects, "TAGame.MatchmakingSettingsSave_TA")
        return parse_matchmaking_settings(raw)

    @cached_property
    def network(self) -> NetworkSettings | None:
        raw = _get_object(self.objects, "TAGame.NetworkSave_TA")
        if raw is None:
            return None
        return NetworkSettings(raw=raw)

    # Quick Chat

    @cached_property
    def quick_chats(self) -> list[QuickChatBinding]:
        raw = _get_object(self.objects, "TAGame.ProfileQuickChatSave_TA")
        return parse_quick_chats(raw)

    # Season / Progression

    @cached_property
    def season(self) -> SeasonProgress | None:
        raw = _get_object(self.objects, "TAGame.SeasonSave_TA")
        return parse_season_progress(raw)

    @cached_property
    def achievements(self) -> AchievementProgress | None:
        raw = _get_object(self.objects, "TAGame.AchievementSave_TA")
        if raw is None:
            return None
        return AchievementProgress(raw=raw)

    @cached_property
    def tutorial(self) -> TutorialProgress | None:
        raw = _get_object(self.objects, "TAGame.TutorialSave_TA")
        if raw is None:
            return None
        return TutorialProgress(raw=raw)

    @cached_property
    def training(self) -> TrainingProgress | None:
        raw = _get_object(self.objects, "TAGame.TrainingProgressSave_TA")
        if raw is None:
            return None
        return TrainingProgress(raw=raw)

    # Profile

    @cached_property
    def profile(self) -> PlayerProfile | None:
        raw = _get_object(self.objects, "TAGame.Profile_TA")
        return parse_player_profile(raw)

    @cached_property
    def recent_players(self) -> list[str]:
        raw = self.raw_properties.get("OnlinePlayers")
        if isinstance(raw, list):
            return [str(p) for p in raw]
        return []

    @cached_property
    def ban_info(self) -> BanInfo | None:
        raw = _get_object(self.objects, "TAGame.BanSave_TA")
        if raw is None:
            return None
        return BanInfo(raw=raw)

    # Other

    @cached_property
    def music(self) -> MusicPlaylist | None:
        raw = _get_object(self.objects, "TAGame.MusicPlayerSave_TA")
        return parse_music_playlist(raw)

    @cached_property
    def notifications(self) -> list[Notification]:
        raw = _get_object(self.objects, "TAGame.NotificationSave_TA")
        return parse_notifications(raw)

    @cached_property
    def crumb_trail(self) -> CrumbTrail | None:
        raw = _get_object(self.objects, "TAGame.CrumbTrailSave_TA")
        if raw is None:
            return None
        return CrumbTrail(raw=raw)

    @cached_property
    def ui_values(self) -> dict[str, Any]:
        raw = _get_object(self.objects, "TAGame.UISavedValues_TA")
        if raw is None:
            return {}
        return {k: v for k, v in raw.items() if k != "__type"}

    @cached_property
    def map_prefs(self) -> MapPreferences | None:
        raw = _get_object(self.objects, "TAGame.MapPrefsSave_TA")
        return parse_map_prefs(raw)

    # Parsed objects (for custom access)

    @cached_property
    def parsed_objects(self) -> list[ParsedObject]:
        result: list[ParsedObject] = []
        for obj in self.objects:
            type_name = obj.get("__type", "Unknown")
            parse_error = obj.get("__parse_error")
            props = {k: v for k, v in obj.items()
                     if not k.startswith("__")}
            result.append(ParsedObject(
                type_name=type_name,
                properties=props,
                parse_error=parse_error,
            ))
        return result

    def object_by_type(self, type_name: str) -> dict | None:
        """Return the first raw object dict matching type_name."""
        return _get_object(self.objects, type_name)

    def objects_by_type(self, type_name: str) -> list[dict]:
        """Return all raw object dicts matching type_name."""
        return _get_objects(self.objects, type_name)

    def __repr__(self) -> str:
        return (
            f"SaveData(source={self.source_file.name!r}, "
            f"objects={len(self.objects)}, "
            f"engine_v={self.header.engine_version})"
        )
