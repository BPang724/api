from dataclasses import dataclass

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


@dataclass(frozen=True)
class YouTubeMetadata:
    title: str
    duration_seconds: int | None


class YouTubeMetadataError(Exception):
    pass


def extract_youtube_metadata(url: str) -> YouTubeMetadata:
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 15,
        "retries": 1,
    }

    try:
        with YoutubeDL(options) as youtube_dl:
            info = youtube_dl.extract_info(url, download=False)
    except DownloadError as error:
        raise YouTubeMetadataError(
            "Unable to retrieve metadata for this YouTube video."
        ) from error

    if not isinstance(info, dict):
        raise YouTubeMetadataError(
            "YouTube did not return metadata for this video."
        )

    title = info.get("title")
    if not isinstance(title, str) or not title.strip():
        raise YouTubeMetadataError(
            "YouTube did not return a title for this video."
        )

    duration = info.get("duration")
    duration_seconds = (
        int(duration)
        if isinstance(duration, (int, float)) and duration >= 0
        else None
    )
    return YouTubeMetadata(
        title=title.strip(),
        duration_seconds=duration_seconds,
    )
