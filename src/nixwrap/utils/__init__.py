"""Shared constants, rank helpers, platform utils, PsyNet config."""

from nixwrap.utils._constants import (
    RANK_TIERS,
    DIVISIONS,
    PLATFORM_SLUGS,
    PLATFORM_TAGS,
    SAVE_PATH_STEAM,
    SAVE_PATH_EPIC,
)
from nixwrap.utils._config import (
    fetch_psynet_config,
    get_active_events,
    get_maps_for_playlist,
    get_online_playlists,
    get_playlist_map_set_name,
    get_playlist_player_count,
    get_special_events,
)
from nixwrap.utils._ranks import (
    get_tier_id,
    get_div_id,
    get_tier_name,
    get_div_name,
    shorten_rank,
    get_div_color_id,
    rank_sort_key,
)
from nixwrap.utils._platforms import (
    is_bot,
    parse_primary_id,
    get_platform_tag,
    get_platform_slug,
)

__all__ = [
    # constants
    "RANK_TIERS",
    "DIVISIONS",
    "PLATFORM_SLUGS",
    "PLATFORM_TAGS",
    "SAVE_PATH_STEAM",
    "SAVE_PATH_EPIC",
    # psyNet config
    "fetch_psynet_config",
    "get_active_events",
    "get_maps_for_playlist",
    "get_online_playlists",
    "get_playlist_map_set_name",
    "get_playlist_player_count",
    "get_special_events",
    # ranks
    "get_tier_id",
    "get_div_id",
    "get_tier_name",
    "get_div_name",
    "shorten_rank",
    "get_div_color_id",
    "rank_sort_key",
    # platforms
    "is_bot",
    "parse_primary_id",
    "get_platform_tag",
    "get_platform_slug",
]
