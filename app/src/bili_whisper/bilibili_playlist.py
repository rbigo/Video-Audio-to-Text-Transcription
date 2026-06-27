from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .paths import BILIBILI_COOKIE_FILE

BILIBILI_VIEW_API = "https://api.bilibili.com/x/web-interface/view"
BILIBILI_VIDEO_URL = "https://www.bilibili.com/video/{bvid}/"


@dataclass(frozen=True)
class PlaylistEpisode:
    index: int
    section_title: str
    bvid: str
    aid: int | None
    cid: int | None
    title: str
    duration: int | None
    url: str


@dataclass(frozen=True)
class BilibiliPlaylist:
    id: int | None
    title: str
    intro: str
    owner_name: str
    owner_mid: int | None
    source_bvid: str
    episodes: list[PlaylistEpisode]


def extract_bvid(value: str) -> str:
    match = re.search(r"(BV[0-9A-Za-z]{10,})", value.strip())
    if not match:
        raise ValueError("No Bilibili BV id was found in the URL or input.")
    return match.group(1)


def fetch_bilibili_playlist(url_or_bvid: str) -> BilibiliPlaylist:
    bvid = extract_bvid(url_or_bvid)
    payload = _fetch_video_view(bvid, referer=_episode_url(bvid))
    data = payload.get("data") or {}
    owner = data.get("owner") or {}
    season = data.get("ugc_season") or {}
    if season:
        episodes = _season_episodes(season)
        if episodes:
            return BilibiliPlaylist(
                id=_optional_int(season.get("id")),
                title=str(season.get("title") or data.get("title") or bvid),
                intro=str(season.get("intro") or ""),
                owner_name=str(owner.get("name") or ""),
                owner_mid=_optional_int(owner.get("mid")),
                source_bvid=bvid,
                episodes=episodes,
            )
    return _single_video_playlist(data, bvid)


def playlist_to_dict(playlist: BilibiliPlaylist) -> dict[str, Any]:
    return asdict(playlist)


def format_playlist_text(playlist: BilibiliPlaylist) -> str:
    lines = [
        f"Playlist: {playlist.title}",
        f"Owner: {playlist.owner_name or 'unknown'}"
        + (f" ({playlist.owner_mid})" if playlist.owner_mid is not None else ""),
        f"Source: {playlist.source_bvid}",
        f"Episodes: {len(playlist.episodes)}",
        "",
    ]
    for episode in playlist.episodes:
        duration = _format_duration(episode.duration)
        suffix = f" [{duration}]" if duration else ""
        lines.append(f"{episode.index:02d}. {episode.bvid} {episode.title}{suffix}")
        lines.append(f"    {episode.url}")
    return "\n".join(lines).rstrip() + "\n"


def _fetch_video_view(bvid: str, *, referer: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"bvid": bvid})
    request = urllib.request.Request(
        f"{BILIBILI_VIEW_API}?{query}",
        headers=_request_headers(referer),
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Bilibili playlist API request failed: {exc}") from exc
    if int(payload.get("code", -1)) != 0:
        message = payload.get("message") or payload.get("msg") or "unknown error"
        raise RuntimeError(f"Bilibili playlist API returned an error: {message}")
    return payload


def _request_headers(referer: str) -> dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
        ),
        "Referer": referer,
        "Accept": "application/json, text/plain, */*",
    }
    cookie = _cookie_header(BILIBILI_COOKIE_FILE)
    if cookie:
        headers["Cookie"] = cookie
    return headers


def _cookie_header(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return ""
    pairs: list[str] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or (line.startswith("#") and not line.startswith("#HttpOnly_")):
            continue
        if line.startswith("#HttpOnly_"):
            line = line.removeprefix("#HttpOnly_")
        parts = line.split("\t")
        if len(parts) >= 7 and "bilibili.com" in parts[0].lower():
            pairs.append(f"{parts[5]}={parts[6]}")
    return "; ".join(pairs)


def _season_episodes(season: dict[str, Any]) -> list[PlaylistEpisode]:
    episodes: list[PlaylistEpisode] = []
    for section in season.get("sections") or []:
        section_title = str(section.get("title") or "")
        for raw_episode in section.get("episodes") or []:
            episode = _episode_from_season(raw_episode, len(episodes) + 1, section_title)
            if episode:
                episodes.append(episode)
    return episodes


def _episode_from_season(raw: dict[str, Any], index: int, section_title: str) -> PlaylistEpisode | None:
    bvid = str(raw.get("bvid") or "")
    aid = _optional_int(raw.get("aid"))
    if not bvid and aid is None:
        return None
    page = raw.get("page") or {}
    arc = raw.get("arc") or {}
    title = str(raw.get("title") or page.get("part") or arc.get("title") or bvid or f"av{aid}")
    duration = _optional_int(page.get("duration")) or _optional_int(arc.get("duration"))
    cid = _optional_int(raw.get("cid")) or _optional_int(page.get("cid"))
    return PlaylistEpisode(
        index=index,
        section_title=section_title,
        bvid=bvid,
        aid=aid,
        cid=cid,
        title=title,
        duration=duration,
        url=_episode_url(bvid, aid=aid),
    )


def _single_video_playlist(data: dict[str, Any], bvid: str) -> BilibiliPlaylist:
    owner = data.get("owner") or {}
    pages = data.get("pages") or []
    duration = _optional_int(data.get("duration"))
    cid = _optional_int(data.get("cid"))
    if pages:
        page = pages[0] or {}
        duration = _optional_int(page.get("duration")) or duration
        cid = _optional_int(page.get("cid")) or cid
    episode = PlaylistEpisode(
        index=1,
        section_title="",
        bvid=bvid,
        aid=_optional_int(data.get("aid")),
        cid=cid,
        title=str(data.get("title") or bvid),
        duration=duration,
        url=_episode_url(bvid),
    )
    return BilibiliPlaylist(
        id=None,
        title=str(data.get("title") or bvid),
        intro=str(data.get("desc") or ""),
        owner_name=str(owner.get("name") or ""),
        owner_mid=_optional_int(owner.get("mid")),
        source_bvid=bvid,
        episodes=[episode],
    )


def _episode_url(bvid: str, *, aid: int | None = None) -> str:
    if bvid:
        return BILIBILI_VIDEO_URL.format(bvid=bvid)
    if aid is not None:
        return f"https://www.bilibili.com/video/av{aid}/"
    return ""


def _optional_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _format_duration(seconds: int | None) -> str:
    if not seconds:
        return ""
    minutes, second = divmod(seconds, 60)
    hour, minute = divmod(minutes, 60)
    if hour:
        return f"{hour}:{minute:02d}:{second:02d}"
    return f"{minute}:{second:02d}"
