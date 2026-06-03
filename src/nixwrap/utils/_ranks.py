"""Rank helper functions."""

from nixwrap.utils._constants import RANK_TIERS, DIVISIONS


def get_tier_id(rank_name: str) -> int:
    """Convert a rank name (e.g. "Diamond I") to its tier_id (0-22)."""
    try:
        return RANK_TIERS.index(rank_name)
    except ValueError:
        return 0


def get_div_id(div_name: str) -> int:
    """Convert a division name (e.g. "Division III") to its id (1-4)."""
    return DIVISIONS.get(div_name, 0)


def get_tier_name(tier_id: int) -> str:
    """Convert a tier_id to its display name."""
    if 0 <= tier_id < len(RANK_TIERS):
        return RANK_TIERS[tier_id]
    return "Unranked"


def get_div_name(div_id: int) -> str:
    """Convert a division id (1-4) to its display name."""
    for name, did in DIVISIONS.items():
        if did == div_id:
            return name
    return "Division I"


def shorten_rank(rank_str: str) -> str:
    """
    Shorten a rank name for compact display.

    Examples:
        "Grand Champion II" -> "GC2"
        "Diamond III" -> "D3"
        "Supersonic Legend" -> "SSL"
    """
    if not rank_str:
        return "Unranked"
    s = rank_str.strip()
    if s.lower() == "supersonic legend":
        return "SSL"
    if s.lower() == "unranked":
        return "Unranked"
    roman_map = {"I": "1", "II": "2", "III": "3"}
    parts = s.split()
    if len(parts) >= 2:
        num = roman_map.get(parts[-1].upper(), parts[-1])
        if "Grand Champion" in s:
            return f"GC{num}"
        else:
            return f"{parts[0][0].upper()}{num}"
    return s


def get_div_color_id(tier_id: int) -> int:
    """
    Get the division icon color set for a tier.

    1 = Bronze, 2 = Silver, 3 = Gold, 4 = Platinum,
    5 = Diamond, 6 = Champion, 7 = GC/SSL.
    """
    if tier_id <= 0:
        return 7
    if 1 <= tier_id <= 3:
        return 1
    elif 4 <= tier_id <= 6:
        return 2
    elif 7 <= tier_id <= 9:
        return 3
    elif 10 <= tier_id <= 12:
        return 4
    elif 13 <= tier_id <= 15:
        return 5
    elif 16 <= tier_id <= 18:
        return 6
    else:
        return 7


def rank_sort_key(tier_id: int, div_id: int) -> tuple[int, int]:
    """Return a sortable key for ranking (higher = better)."""
    return (tier_id, div_id)
