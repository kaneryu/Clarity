import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional

from src import universal as universal
from src.providerInterface.globalModels import SimpleIdentifier
from src.providerInterface.song.models import (
    PlaybackData,
    FormatData,
    YoutubeFormatData,
    YoutubePlaybackData,
    DataFragment,
    HeatmapEntry,
    SongData,
    PlaybackUrl,
    PlaybackUrlHeader,
    PlaybackTracking,
    VideoDetails,
    PageOwnerDetails,
    MicroformatDataRenderer,
    ThumbnailSet,
    ThumbnailEntry,
    PlaybackDataThumbnail,
)

from src.providerInterface.song.providers.youtube.constants import FMT_DATA


def convert_to_timestamp(date_str: str) -> float:
    # Split the date and the timezone
    date_str, tz_str = date_str.split("T")
    date_str += "T" + tz_str.split("-")[0]

    # Parse the date string into a datetime object
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")

    # Calculate the timezone offset
    tz_hours, tz_minutes = map(int, tz_str.split("-")[1].split(":"))
    tz_delta = timedelta(hours=tz_hours, minutes=tz_minutes)

    # Subtract the timezone offset to get the UTC time
    dt -= tz_delta

    # Convert the datetime object to a timestamp
    timestamp = time.mktime(dt.timetuple())

    return timestamp


def run_sync(func, *args, **kwargs):
    coro = func(*args, **kwargs)
    if asyncio.iscoroutine(coro):
        future = asyncio.run_coroutine_threadsafe(
            coro, universal.asyncBgworker.event_loop
        )
        future.result()  # wait for the result
    else:
        return coro


def playback_from_raw(raw: dict) -> Optional[YoutubePlaybackData]:
    """
    Convert raw playback info (yt-dlp style) into a PlaybackData-like object.
    """
    if not raw:
        return None

    r = raw or {}

    # helper to coerce int-like safely
    def _int(v):
        try:
            return int(v) if v is not None and v != "" else None
        except Exception:
            return None

    # formats
    formats_raw = (r.get("formats") or [])[:]
    formats: list[FormatData] = []
    for f in formats_raw:
        fragments = None
        if f.get("fragments"):
            fragments = [
                DataFragment(url=frag.get("url"), duration=frag.get("duration"))
                for frag in (f.get("fragments") or [])
            ]

        # collect known keys to exclude from extra
        known_keys = {
            "format_id",
            "format_note",
            "source_preference",
            "ext",
            "protocol",
            "acodec",
            "vcodec",
            "url",
            "width",
            "height",
            "fps",
            "rows",
            "columns",
            "fragments",
            "audio_ext",
            "video_ext",
            "vbr",
            "abr",
            "tbr",
            "resolution",
            "aspect_ratio",
            "filesize_approx",
            "filesize",
            "http_headers",
            "format",
            "asr",
            "audio_channels",
            "quality",
            "has_drm",
            "available_at",
            "downloader_options",
            "container",
            "dynamic_range",
            "manifest_url",
            "manifest_index",
            "preference",
        }

        extra = {k: v for k, v in (f or {}).items() if k not in known_keys}

        formats.append(
            YoutubeFormatData(
                format_id=f.get("format_id"),
                format_note=f.get("format_note"),
                source_preference=f.get("source_preference"),
                ext=f.get("ext"),
                protocol=f.get("protocol"),
                acodec=f.get("acodec"),
                vcodec=f.get("vcodec"),
                url=f.get("url"),
                width=(
                    _int(f.get("width"))
                    if isinstance(f.get("width"), (int, str))
                    else f.get("width")
                ),
                height=(
                    _int(f.get("height"))
                    if isinstance(f.get("height"), (int, str))
                    else f.get("height")
                ),
                fps=f.get("fps"),
                rows=f.get("rows"),
                columns=f.get("columns"),
                fragments=fragments,
                audio_ext=f.get("audio_ext"),
                video_ext=f.get("video_ext"),
                vbr=f.get("vbr"),
                abr=f.get("abr"),
                tbr=f.get("tbr"),
                resolution=f.get("resolution"),
                aspect_ratio=f.get("aspect_ratio"),
                filesize_approx=_int(f.get("filesize_approx")),
                filesize=_int(f.get("filesize")),
                http_headers=f.get("http_headers"),
                format=f.get("format"),
                asr=f.get("asr"),
                audio_channels=f.get("audio_channels"),
                quality=f.get("quality"),
                has_drm=f.get("has_drm"),
                available_at=f.get("available_at"),
                downloader_options=f.get("downloader_options"),
                container=f.get("container"),
                dynamic_range=f.get("dynamic_range"),
                manifest_url=f.get("manifest_url"),
                manifest_index=f.get("manifest_index"),
                preference=f.get("preference"),
                extra=extra,
                clarity_quality=FMT_DATA.get(
                    f.get("format_id"), f.get("serverQuality")
                ),
                audio=f.get("acodec") != "none",
            )
        )

    # requested_formats
    requested_formats_raw = (r.get("requested_formats") or [])[:]
    requested_formats = []
    for f in requested_formats_raw:
        fragments = None
        if f.get("fragments"):
            fragments = [
                DataFragment(url=frag.get("url"), duration=frag.get("duration"))
                for frag in (f.get("fragments") or [])
            ]
        requested_formats.append(
            YoutubeFormatData(
                format_id=f.get("format_id"),
                ext=f.get("ext"),
                protocol=f.get("protocol"),
                url=f.get("url"),
                width=f.get("width"),
                height=f.get("height"),
                fps=f.get("fps"),
                fragments=fragments,
                extra={k: v for k, v in (f or {}).items()},
            )
        )

    # thumbnails
    thumbs_raw = (r.get("thumbnails") or [])[:]
    thumbnails = (
        [
            PlaybackDataThumbnail(
                url=t.get("url"),
                height=(
                    _int(t.get("height")) if t.get("height") not in (None, "") else None
                ),
                width=(
                    _int(t.get("width")) if t.get("width") not in (None, "") else None
                ),
                preference=t.get("preference"),
                id=t.get("id"),
                resolution=t.get("resolution"),
            )
            for t in thumbs_raw
        ]
        if thumbs_raw
        else None
    )

    # heatmap
    heat_raw = (r.get("heatmap") or [])[:]
    heatmap = (
        [
            HeatmapEntry(
                start_time=h.get("start_time"),
                end_time=h.get("end_time"),
                value=h.get("value"),
            )
            for h in heat_raw
        ]
        if heat_raw
        else None
    )

    # Build PlaybackData, keep raw dict in extra for future use
    pd = YoutubePlaybackData(
        id=SimpleIdentifier(str(r.get("id"))),
        title=r.get("title") or r.get("fulltitle") or r.get("display_id"),
        formats=formats or None,
        audio_formats=sorted(
            [fmt for fmt in formats if fmt.audio],
            key=lambda x: (x.clarity_quality if x.clarity_quality is not None else 0),
            reverse=True,
        ),
        video_formats=sorted(
            [fmt for fmt in formats if not fmt.audio],
            key=lambda x: (x.clarity_quality if x.clarity_quality is not None else 0),
            reverse=True,
        ),
        requested_formats=requested_formats or None,
        rawFormats=formats_raw or None,
        thumbnails=thumbnails,
        thumbnail=r.get("thumbnail"),
        description=r.get("description"),
        channel_id=r.get("channel_id"),
        channel_url=r.get("channel_url"),
        channel=r.get("channel"),
        channel_follower_count=_int(r.get("channel_follower_count")),
        channel_is_verified=r.get("channel_is_verified"),
        duration=_int(r.get("duration")),
        duration_string=r.get("duration_string"),
        view_count=_int(r.get("view_count")),
        like_count=_int(r.get("like_count")),
        comment_count=_int(r.get("comment_count")),
        average_rating=r.get("average_rating"),
        age_limit=_int(r.get("age_limit")),
        webpage_url=r.get("webpage_url"),
        webpage_url_basename=r.get("webpage_url_basename"),
        webpage_url_domain=r.get("webpage_url_domain"),
        original_url=r.get("original_url"),
        fulltitle=r.get("fulltitle"),
        display_id=r.get("display_id"),
        categories=r.get("categories"),
        tags=r.get("tags"),
        playable_in_embed=r.get("playable_in_embed"),
        live_status=r.get("live_status"),
        is_live=r.get("is_live"),
        was_live=r.get("was_live"),
        media_type=r.get("media_type"),
        release_timestamp=r.get("release_timestamp"),
        release_date=r.get("release_date"),
        release_year=_int(r.get("release_year")),
        album=r.get("album"),
        artists=r.get("artists"),
        track=r.get("track"),
        automatic_captions=r.get("automatic_captions"),
        subtitles=r.get("subtitles"),
        chapters=r.get("chapters"),
        heatmap=heatmap,
        uploader=r.get("uploader"),
        uploader_id=r.get("uploader_id"),
        uploader_url=r.get("uploader_url"),
        upload_date=r.get("upload_date"),
        timestamp=r.get("timestamp"),
        epoch=r.get("epoch"),
        creators=r.get("creators"),
        artist=r.get("artist"),
        creator=r.get("creator"),
        alt_title=r.get("alt_title"),
        availability=r.get("availability"),
        extractor=r.get("extractor"),
        extractor_key=r.get("extractor_key"),
        extractor_id=r.get("extractor_id"),
        format=r.get("format"),
        format_id=r.get("format_id"),
        format_note=r.get("format_note"),
        ext=r.get("ext"),
        protocol=r.get("protocol"),
        filesize_approx=_int(r.get("filesize_approx")),
        tbr=r.get("tbr"),
        width=_int(r.get("width")),
        height=_int(r.get("height")),
        resolution=r.get("resolution"),
        fps=r.get("fps"),
        dynamic_range=r.get("dynamic_range"),
        vcodec=r.get("vcodec"),
        vbr=r.get("vbr"),
        acodec=r.get("acodec"),
        abr=r.get("abr"),
        asr=r.get("asr"),
        audio_channels=r.get("audio_channels"),
        extra={k: v for k, v in r.items()},  # preserve raw block
    )

    return pd


def songdata_from_raw(rawData: dict, album: Optional[str] = None) -> Optional[SongData]:
    """
    Convert the raw JSON returned by the API (same shape as the 5RQBkK..._info file)
    into a SongData instance and attach it to self.songData. Also set a few
    convenience attributes on self (id, title, duration, author).

    Parameters:
    - rawData (dict): The raw data from the API.

    Returns:
    - SongData: The converted SongData instance.
    """
    rd = rawData or {}
    if not rd:
        return None

    if sid := rd.get("videoDetails", {}).get("videoId"):
        sd = SongData(id=sid)
    else:
        return None  # invalid data

    if not sd.id:
        return None  # invalid data

    sd.extra = {  # move all unknown top-level keys to extra
        k: v
        for k, v in rd.items()
        if k
        not in (
            "videoDetails",
            "microformat",
            "playbackTracking",
            "playabilityStatus",
            "streamingData",
        )
    }

    # playability / streaming raw blocks
    sd.playabilityStatus = rd.get("playabilityStatus", {})
    sd.playbackTracking = None
    if pt := rd.get("playbackTracking"):

        def _make_playback_url(d: dict | None) -> PlaybackUrl | None:
            if not d:
                return None
            headers = []
            for h in d.get("headers", []) or []:
                headers.append(PlaybackUrlHeader(headerType=h.get("headerType")))
            return PlaybackUrl(
                baseUrl=d.get("baseUrl"),
                headers=headers,
                elapsedMediaTimeSeconds=d.get("elapsedMediaTimeSeconds"),
            )

        sd.playbackTracking = PlaybackTracking(
            videostatsPlaybackUrl=_make_playback_url(pt.get("videostatsPlaybackUrl")),
            videostatsDelayplayUrl=_make_playback_url(pt.get("videostatsDelayplayUrl")),
            videostatsWatchtimeUrl=_make_playback_url(pt.get("videostatsWatchtimeUrl")),
            ptrackingUrl=_make_playback_url(pt.get("ptrackingUrl")),
            qoeUrl=_make_playback_url(pt.get("qoeUrl")),
            atrUrl=_make_playback_url(pt.get("atrUrl")),
            videostatsScheduledFlushWalltimeSeconds=pt.get(
                "videostatsScheduledFlushWalltimeSeconds", []
            )
            or [],
            videostatsDefaultFlushIntervalSeconds=pt.get(
                "videostatsDefaultFlushIntervalSeconds"
            ),
            extra={
                k: v
                for k, v in pt.items()
                if k
                not in (
                    "videostatsPlaybackUrl",
                    "videostatsDelayplayUrl",
                    "videostatsWatchtimeUrl",
                    "ptrackingUrl",
                    "qoeUrl",
                    "atrUrl",
                    "videostatsScheduledFlushWalltimeSeconds",
                    "videostatsDefaultFlushIntervalSeconds",
                )
            },
        )

    # videoDetails -> VideoDetails dataclass
    vd = rd.get("videoDetails", {}) or {}
    video_details_obj = VideoDetails(
        videoId=vd.get("videoId") or vd.get("externalVideoId"),
        title=vd.get("title"),
        lengthSeconds=(
            int(vd.get("lengthSeconds", ""))
            if vd.get("lengthSeconds") not in (None, "")
            else None
        ),
        channelId=vd.get("channelId"),
        author=vd.get("author"),
        viewCount=(
            int(vd.get("viewCount", "0"))
            if vd.get("viewCount") not in (None, "")
            else None
        ),
        isPrivate=vd.get("isPrivate"),
        isLiveContent=vd.get("isLiveContent"),
        allowRatings=vd.get("allowRatings"),
        thumbnail=None,
        extra={
            k: v
            for k, v in vd.items()
            if k
            not in (
                "videoId",
                "title",
                "lengthSeconds",
                "channelId",
                "author",
                "viewCount",
                "isPrivate",
                "isLiveContent",
                "allowRatings",
                "thumbnail",
            )
        },
    )
    # thumbnails from videoDetails
    thumbs = (vd.get("thumbnail") or {}).get("thumbnails", []) or []
    sd.thumbnails = {"videoDetails": thumbs}

    # convert thumbnails to typed ThumbnailSet if desired for microformat usage
    # pick smallest & largest by width (fallback to height then by length)
    def _pick_thumb(lst):
        if not lst:
            return {}
        sorted_by_w = sorted(
            lst, key=lambda x: (x.get("width") or x.get("height") or 0)
        )
        smallest = sorted_by_w[0]
        largest = sorted_by_w[-1]
        return smallest, largest

    smallest, largest = {}, {}
    if thumbs:
        smallest, largest = _pick_thumb(thumbs)
        sd.smallestThumbnail = smallest
        sd.largestThumbnail = largest
        sd.smallestThumbnailUrl = smallest.get("url")
        sd.largestThumbnailUrl = largest.get("url")

    sd.videoDetails = video_details_obj

    # microformat block
    mf_block = (rd.get("microformat") or {}).get("microformatDataRenderer", {}) or {}
    # description / tags / canonical url
    sd.fullUrl = mf_block.get("urlCanonical") or (
        f"https://www.youtube.com/watch?v={sd.videoDetails.videoId}"
        if sd.videoDetails and sd.videoDetails.videoId
        else None
    )
    sd.description = mf_block.get("description")
    sd.tags = mf_block.get("tags", []) or []
    sd.category = mf_block.get("category")
    sd.isFamilySafe = mf_block.get("familySafe")
    sd.allowRatings = sd.videoDetails.allowRatings if sd.videoDetails else None

    # microformat thumbnail (rectangle)
    mf_thumbs = (mf_block.get("thumbnail") or {}).get("thumbnails", []) or []
    sd.rectangleThumbnail = {"microformat": mf_thumbs}
    if mf_thumbs:
        sd.rectangleThumbnailUrl = mf_thumbs[0].get("url")

    # page owner details
    pod = mf_block.get("pageOwnerDetails") or {}
    if pod:
        sd.pageOwnerDetails = PageOwnerDetails(
            name=pod.get("name"),
            externalChannelId=pod.get("externalChannelId"),
            youtubeProfileUrl=pod.get("youtubeProfileUrl"),
        )
        sd.pageOwnerName = sd.pageOwnerDetails.name
        sd.pageOwnerChannelId = sd.pageOwnerDetails.externalChannelId

    # dates
    sd.publishDate = mf_block.get("publishDate")
    sd.uploadDate = mf_block.get("uploadDate")
    if sd.publishDate:
        try:
            sd.publishDateTimestamp = convert_to_timestamp(sd.publishDate)
        except Exception:
            sd.publishDateTimestamp = None
    if sd.uploadDate:
        try:
            sd.uploadDateTimestamp = convert_to_timestamp(sd.uploadDate)
        except Exception:
            sd.uploadDateTimestamp = None

    # views
    if sd.videoDetails and sd.videoDetails.viewCount is not None:
        sd.views = sd.videoDetails.viewCount
    else:
        # fallback to microformat viewCount
        try:
            sd.views = (
                int(mf_block.get("viewCount", "0"))
                if mf_block.get("viewCount") not in (None, "")
                else None
            )
        except Exception:
            sd.views = None

    # build MicroformatDataRenderer typed structure (partial)
    mfr = MicroformatDataRenderer(
        urlCanonical=mf_block.get("urlCanonical"),
        title=mf_block.get("title"),
        description=mf_block.get("description"),
        thumbnail=(
            ThumbnailSet(
                thumbnails=[
                    ThumbnailEntry(
                        url=t.get("url"), width=t.get("width"), height=t.get("height")
                    )
                    for t in mf_thumbs
                ]
            )
            if mf_thumbs
            else None
        ),
        siteName=mf_block.get("siteName"),
        appName=mf_block.get("appName"),
        ogType=mf_block.get("ogType"),
        tags=mf_block.get("tags", []) or [],
        availableCountries=mf_block.get("availableCountries", []) or [],
        pageOwnerDetails=sd.pageOwnerDetails,
        videoDetails=mf_block.get("videoDetails", {}) or {},
        viewCount=(
            int(mf_block.get("viewCount", "0"))
            if mf_block.get("viewCount") not in (None, "")
            else sd.views
        ),
        publishDate=mf_block.get("publishDate"),
        uploadDate=mf_block.get("uploadDate"),
        category=mf_block.get("category"),
        extra={
            k: v
            for k, v in mf_block.items()
            if k
            not in (
                "urlCanonical",
                "title",
                "description",
                "thumbnail",
                "siteName",
                "appName",
                "ogType",
                "tags",
                "availableCountries",
                "pageOwnerDetails",
                "videoDetails",
                "viewCount",
                "publishDate",
                "uploadDate",
                "category",
            )
        },
    )
    sd.microformat = mfr

    # core simple fields
    sd.id = SimpleIdentifier(sd.videoDetails.videoId) if sd.videoDetails else None  # type: ignore
    sd.title = sd.videoDetails.title if sd.videoDetails else sd.title or mfr.title
    sd.duration = sd.videoDetails.lengthSeconds if sd.videoDetails else None
    sd.author = sd.videoDetails.author if sd.videoDetails else None
    sd.artist = sd.author  # alias
    if album:
        sd.albumId = album

    if not sd.id:
        return None  # invalid data

    return sd
