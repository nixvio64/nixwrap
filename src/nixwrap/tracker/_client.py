"""tracker.gg API client for fetching Rocket League player stats.

Uses curl_cffi for TLS fingerprint impersonation to avoid bot
detection.  Falls back to urllib if curl_cffi is not installed
(but may be rate-limited/blocked).
"""

from __future__ import annotations

import logging
import random
import time
import urllib.parse
import urllib.request
from typing import Any

from nixwrap.tracker._cache import TTLCache, DEFAULT_TTL
from nixwrap.tracker._models import (
    PlayerStats, PlaylistRank, LifetimeStats, PlaylistAverage,
)
from nixwrap.utils import get_platform_slug, is_bot

_log = logging.getLogger(__name__)

IMPERSONATE_OPTIONS = ["chrome120", "chrome124", "edge99", "edge101"]

_DIVISION_NAMES = {
    0: "Division I", 1: "Division II",
    2: "Division III", 3: "Division IV",
}

# TrackerClient

class TrackerClient:
    """HTTP client for the tracker.gg Rocket League API.

    Parameters
    impersonate:
        Browser fingerprint to impersonate.  One of the IMPERSONATE_OPTIONS.
        None (default) picks a random fingerprint per request.
    timeout:
        HTTP request timeout in seconds.
    cache_ttl:
        TTL for cached results in seconds (default 300 = 5 min).
    """

    def __init__(
        self,
        impersonate: str | None = None,
        timeout: float = 8.0,
        cache_ttl: float = DEFAULT_TTL,
    ) -> None:
        self._impersonate = impersonate
        self._timeout = timeout
        self._cache = TTLCache(ttl=cache_ttl)

        # Check for curl_cffi
        self._has_curl_cffi = False
        try:
            import curl_cffi  # noqa: F401
            self._has_curl_cffi = True
        except ImportError:
            _log.warning(
                "curl_cffi not installed: tracker.gg requests may be "
                "blocked by anti-bot detection.  Install with: "
                "pip install curl-cffi"
            )

    # Public API

    def fetch(self, primary_id: str, display_name: str) -> PlayerStats:
        """Fetch player stats from tracker.gg.

        Cached results are returned instantly if still fresh.

        Parameters
        primary_id:
            The player's PrimaryId (e.g. "Steam|123|0").
        display_name:
            The player's display name (used for API lookup on non-Steam
            platforms).

        Returns
        PlayerStats
            Always returns a PlayerStats object.  Check .error
            and .not_found to distinguish failures.

        Raises
        ValueError
            If primary_id is a bot or empty.
        """
        if is_bot(primary_id) or not primary_id:
            raise ValueError(f"Invalid primary_id: {primary_id!r}")

        # Check cache
        cached = self._cache.get(primary_id)
        if cached is not None:
            return cached

        # Parse platform info
        slug = get_platform_slug(primary_id)
        parts = primary_id.split("|")
        platform = parts[0].lower()
        user_id = parts[1] if len(parts) > 1 else ""

        # Non-Steam platforms look up by display name
        if slug == "steam":
            target_user = user_id
        else:
            target_user = urllib.parse.quote(display_name, safe="")

        try:
            data = self._request(slug, target_user)
            stats = _parse_response(data, primary_id, display_name, platform)
            self._cache.set(primary_id, stats)
            return stats
        except Exception as exc:
            err_msg = str(exc)
            not_found = "NOT_FOUND_404" in err_msg or "404" in err_msg
            stats = PlayerStats(
                primary_id=primary_id,
                display_name=display_name,
                platform=platform,
                error=err_msg,
                not_found=not_found,
                fetched_at=time.time(),
            )
            # Don't cache errors permanently: short TTL handled by cache layer
            if not_found:
                self._cache.set(primary_id, stats)
            return stats

    def get_cached(self, primary_id: str) -> PlayerStats | None:
        """Return cached stats without making a request."""
        return self._cache.get(primary_id)

    def clear_cache(self) -> None:
        """Clear all cached results."""
        self._cache.clear()

    # Internals

    def _request(self, slug: str, target_user: str) -> dict[str, Any]:
        url = (
            f"https://api.tracker.gg/api/v2/rocket-league/"
            f"standard/profile/{slug}/{target_user}"
        )

        if self._has_curl_cffi:
            return self._request_curl_cffi(url)
        else:
            return self._request_urllib(url)

    def _request_curl_cffi(self, url: str) -> dict[str, Any]:
        from curl_cffi import requests as cf_requests
        impersonate = self._impersonate or random.choice(IMPERSONATE_OPTIONS)
        resp = cf_requests.get(
            url,
            impersonate=impersonate,
            timeout=self._timeout,
        )
        if resp.status_code == 404:
            raise ValueError("NOT_FOUND_404: tracker.gg returned 404")
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data.get("data"), dict):
            raise ValueError("Tracker API returned unexpected structure")
        return data

    def _request_urllib(self, url: str) -> dict[str, Any]:
        import json
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read())
                if not isinstance(data.get("data"), dict):
                    raise ValueError("Tracker API returned unexpected structure")
                return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError("NOT_FOUND_404: tracker.gg returned 404")
            raise


# Response parser

def _parse_response(
    data: dict[str, Any],
    primary_id: str,
    display_name: str,
    platform: str,
) -> PlayerStats:
    inner = data.get("data", {})

    # Platform info
    pinfo = inner.get("platformInfo", {})
    platform_user_handle = pinfo.get("platformUserHandle", display_name)
    avatar_url = pinfo.get("avatarUrl", "")

    # Metadata
    meta = inner.get("metadata", {})
    player_id = meta.get("playerId", 0)
    current_season = meta.get("currentSeason", 0)
    last_updated_str = None
    lu = meta.get("lastUpdated", {})
    if isinstance(lu, dict):
        last_updated_str = lu.get("value")
    last_updated = None
    if last_updated_str:
        try:
            last_updated = __import__('datetime').datetime.fromisoformat(
                last_updated_str.replace('Z', '+00:00')
            )
        except Exception:
            pass

    ranks: dict[int, PlaylistRank] = {}
    lifetime: LifetimeStats | None = None
    averages: dict[int, PlaylistAverage] = {}

    for seg in inner.get("segments", []):
        stype = seg.get("type", "")
        if stype == "overview":
            lifetime = _parse_lifetime(seg.get("stats", {}))
        elif stype == "playlist":
            pid = seg.get("attributes", {}).get("playlistId", 0)
            ranks[pid] = _parse_playlist(pid, seg)
        elif stype == "playlistAverage":
            pid = seg.get("attributes", {}).get("playlist", 0)
            averages[pid] = _parse_average(pid, seg)
        elif stype == "peak-rating":
            pid = seg.get("attributes", {}).get("playlistId", 0)
            # Merge peak data into existing rank entry
            if pid in ranks:
                _merge_peak(ranks[pid], seg)

    return PlayerStats(
        primary_id=primary_id,
        display_name=display_name,
        platform=platform,
        platform_user_handle=platform_user_handle,
        avatar_url=avatar_url,
        player_id=player_id,
        ranks=ranks,
        lifetime=lifetime,
        averages=averages,
        last_updated=last_updated,
        current_season=current_season,
        fetched_at=time.time(),
    )


def _parse_playlist(pid: int, seg: dict) -> PlaylistRank:
    meta = seg.get("metadata", {})
    stats = seg.get("stats", {})

    tier_data = stats.get("tier", {})
    tier_meta = tier_data.get("metadata", {})
    tier_value = tier_data.get("value", 0)

    div_data = stats.get("division", {})
    div_meta = div_data.get("metadata", {})
    div_value = div_data.get("value", 0)

    rating_data = stats.get("rating", {})
    peak_rating_data = stats.get("peakRating", {})
    peak_tier_data = stats.get("peakTier", {})
    peak_div_data = stats.get("peakDivision", {})

    ws_data = stats.get("winStreak", {})
    ws_meta = ws_data.get("metadata", {})

    return PlaylistRank(
        playlist_id=pid,
        playlist_name=meta.get("name", ""),
        tier_id=tier_value,
        tier_name=tier_meta.get("name", "Unranked"),
        division_id=div_value + 1,  # 0-based -> 1-based
        division_name=div_meta.get("name", "Division I"),
        mmr=rating_data.get("value", 0),
        matches_played=stats.get("matchesPlayed", {}).get("value", 0),
        peak_mmr=peak_rating_data.get("value", 0),
        peak_tier_id=peak_tier_data.get("value", 0),
        peak_div_id=peak_div_data.get("value", 0),
        delta_up=div_meta.get("deltaUp", 0),
        delta_down=div_meta.get("deltaDown", 0),
        win_streak=ws_data.get("value", 0),
        win_streak_type=ws_meta.get("type", ""),
        rank_percentile=rating_data.get("percentile", 0.0),
    )


def _parse_lifetime(stats: dict) -> LifetimeStats:
    return LifetimeStats(
        wins=_safe_int(stats, "wins"),
        goals=_safe_int(stats, "goals"),
        mvps=_safe_int(stats, "mVPs"),
        saves=_safe_int(stats, "saves"),
        assists=_safe_int(stats, "assists"),
        shots=_safe_int(stats, "shots"),
        goal_shot_ratio=_safe_float(stats, "goalShotRatio"),
        trn_score=_safe_float(stats, "score"),
        season_reward_level=_safe_int(stats, "seasonRewardLevel"),
        season_reward_wins=_safe_int(stats, "seasonRewardWins"),
    )


def _parse_average(pid: int, seg: dict) -> PlaylistAverage:
    meta = seg.get("metadata", {})
    stats = seg.get("stats", {})
    return PlaylistAverage(
        playlist_id=pid,
        playlist_name=meta.get("playlistName", ""),
        matches=_safe_int(stats, "matches"),
        rating=_safe_int(stats, "rating"),
        avg_goals_per_game=_safe_float(stats, "avgGoalsPerGame"),
        avg_shots_per_game=_safe_float(stats, "avgShotsPerGame"),
        avg_saves_per_game=_safe_float(stats, "avgSavesPerGame"),
        avg_assists_per_game=_safe_float(stats, "avgAssistsPerGame"),
        avg_mvps_per_game=_safe_float(stats, "avgMVPsPerGame"),
        goals_shots_ratio=_safe_float(stats, "goalsShotsRatio"),
        goals_saves_ratio=_safe_float(stats, "goalsSavesRatio"),
        assists_goals_ratio=_safe_float(stats, "assistsGoalsRatio"),
    )


def _merge_peak(rank: PlaylistRank, seg: dict) -> None:
    stats = seg.get("stats", {})
    peak = stats.get("peakRating", {})
    meta = peak.get("metadata", {})
    rank.peak_mmr = peak.get("value", rank.peak_mmr)
    if meta.get("name"):
        rank.peak_tier_id = _tier_name_to_id(meta.get("name", ""))
    div_str = meta.get("division", "")
    if div_str:
        div_map = {"Division I": 1, "Division II": 2,
                   "Division III": 3, "Division IV": 4}
        rank.peak_div_id = div_map.get(div_str, rank.peak_div_id)


def _tier_name_to_id(name: str) -> int:
    from nixwrap.utils._constants import RANK_TIERS
    try:
        return RANK_TIERS.index(name)
    except ValueError:
        return 0


def _safe_int(stats: dict, key: str) -> int:
    val = stats.get(key, {})
    if isinstance(val, dict):
        return int(val.get("value", 0) or 0)
    return 0


def _safe_float(stats: dict, key: str) -> float:
    val = stats.get(key, {})
    if isinstance(val, dict):
        return float(val.get("value", 0.0) or 0.0)
    return 0.0
