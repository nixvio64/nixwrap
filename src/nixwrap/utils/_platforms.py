"""Platform identifier helpers for Rocket League PrimaryId strings."""

from __future__ import annotations

from nixwrap.utils._constants import PLATFORM_TAGS, PLATFORM_SLUGS


def is_bot(primary_id: str) -> bool:
    """
    Check if a PrimaryId belongs to a bot (not a real player).

    Bots have no PrimaryId, contain "unknown", or lack the "|" separator.
    """
    if not primary_id:
        return True
    if "unknown" in primary_id.lower():
        return True
    if "|" not in primary_id:
        return True
    return False


def parse_primary_id(primary_id: str) -> tuple[str, str, str] | None:
    """
    Parse a PrimaryId into (platform, user_id, splitscreen_id).

    Example:
        "Steam|123456789|0" -> ("steam", "123456789", "0")
        "Epic|abc123|0"     -> ("epic", "abc123", "0")
        "XboxOne|xyz|0"     -> ("xboxone", "xyz", "0")

    Returns None if the format is unrecognised.
    """
    if is_bot(primary_id):
        return None
    parts = primary_id.split("|")
    if len(parts) < 2:
        return None
    platform = parts[0].lower()
    uid = parts[1]
    ss = parts[2] if len(parts) > 2 else "0"
    return (platform, uid, ss)


def get_platform_tag(primary_id: str) -> str:
    """
    Get a short display tag for the platform.

    Returns "[Steam]", "[Epic]", "[Xbox]", "[PSN]", "[Switch]", "[BOT]", or "[?]".
    """
    if is_bot(primary_id):
        return "[BOT]"
    plat = primary_id.split("|")[0].lower()
    return PLATFORM_TAGS.get(plat, "[?]")


def get_platform_slug(primary_id: str) -> str:
    """
    Get the tracker.gg API slug for a PrimaryId's platform.

    Returns "steam", "epic", "xbl", "psn", "switch", or "epic" as fallback.
    """
    if is_bot(primary_id):
        return "epic"
    plat = primary_id.split("|")[0].lower()
    return PLATFORM_SLUGS.get(plat, "epic")
