"""Shared constants for the nixwrap SDK."""

# Playlist IDs

PLAYLISTS: dict[int, str] = {
    0: "Casual",
    10: "Ranked Duel 1v1",
    11: "Ranked Doubles 2v2",
    13: "Ranked Standard 3v3",
    27: "Hoops",
    28: "Rumble",
    29: "Dropshot",
    30: "Snowday",
    34: "Tournament Matches",
    61: "Ranked 4v4 Quads",
    63: "Heatseeker",
}

PLAYLIST_IMAGE_MAP: dict[int, str] = {
    10: "0.png",
    11: "1.png",
    13: "2.png",
    27: "3.png",
    28: "4.png",
    29: "5.png",
    30: "6.png",
    34: "7.png",
}

ALL_PLAYLIST_IDS: list[int] = [10, 11, 13, 27, 28, 29, 30, 34, 61, 63]

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

# Tracker cache

CACHE_TTL = 300  # seconds (tracker.gg updates every ~5 min)
