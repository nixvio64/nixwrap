"""Shared constants, rank helpers, platform utils."""

from nixwrap.utils._constants import (
    PLAYLISTS,
    PLAYLIST_IMAGE_MAP,
    ALL_PLAYLIST_IDS,
    RANK_TIERS,
    DIVISIONS,
    PLATFORM_SLUGS,
    PLATFORM_TAGS,
    SAVE_PATH_STEAM,
    SAVE_PATH_EPIC,
    CACHE_TTL,
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
    "PLAYLISTS",
    "PLAYLIST_IMAGE_MAP",
    "ALL_PLAYLIST_IDS",
    "RANK_TIERS",
    "DIVISIONS",
    "PLATFORM_SLUGS",
    "PLATFORM_TAGS",
    "SAVE_PATH_STEAM",
    "SAVE_PATH_EPIC",
    "CACHE_TTL",
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
