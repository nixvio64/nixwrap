"""Shared constants for the nixwrap SDK."""

# Rank tiers (index = tier_id)

RANK_TIERS: list[str] = [
    "Unranked",
    "Bronze I", "Bronze II", "Bronze III",
    "Silver I", "Silver II", "Silver III",
    "Gold I", "Gold II", "Gold III",
    "Platinum I", "Platinum II", "Platinum III",
    "Diamond I", "Diamond II", "Diamond III",
    "Champion I", "Champion II", "Champion III",
    "Grand Champion I", "Grand Champion II", "Grand Champion III",
    "Supersonic Legend",
]

# Divisions

DIVISIONS: dict[str, int] = {
    "Division I": 1,
    "Division II": 2,
    "Division III": 3,
    "Division IV": 4,
}

# Platform slugs (for tracker.gg API)

PLATFORM_SLUGS: dict[str, str] = {
    "steam": "steam",
    "epic": "epic",
    "xboxone": "xbl",
    "ps4": "psn",
    "switch": "switch",
}

PLATFORM_TAGS: dict[str, str] = {
    "steam": "[Steam]",
    "epic": "[Epic]",
    "xboxone": "[Xbox]",
    "ps4": "[PSN]",
    "switch": "[Switch]",
}

# Save file paths (relative to Documents)

SAVE_PATH_STEAM = "My Games/Rocket League/TAGame/SaveData/DBE_Production"
SAVE_PATH_EPIC  = "My Games/Rocket League/TAGame/SaveDataEpic/DBE_Production"
