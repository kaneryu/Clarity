Refactor plan: Song data layer and provider-based frontend

Overview and goals
- Split the current monolithic Song implementation into:
  - SongData: an internal, provider-agnostic dataclass that stores song metadata and playback info
  - SongProvider protocol: a provider/frontend abstraction (YouTube, Local, Spotify, etc.) that fetches metadata, playback info, and downloads
  - Song (QObject): a thin wrapper that exposes QML properties/signals, owns a SongData instance, and delegates to a SongProvider
- Introduce structured IDs and provider detection; keep QML bindings stable and human-friendly
- Preserve thread-safety and Qt signal semantics; maintain backward compatibility for existing caches and queues

ID scheme and properties
- Full structured ID: provider:type:provider_id
  - Examples: youtube:song:dQw4w9WgXcQ, local:song:a3f2b8c9...
  - Type will start with song; future: album, playlist, podcast, episode
- Song properties (QML-exposed):
  - id: full structured ID (e.g., youtube:song:dQw4w9WgXcQ)
  - providerId: bare provider ID only (e.g., dQw4w9WgXcQ)
  - providerName: provider name (e.g., youtube)
  - displayId: alias to providerId (QML constructs human-readable text from title/artist)
- Behavior:
  - If a bare ID is passed (no colon), default to YouTube and auto-upgrade internally to youtube:song:{id}
  - If both a prefix and explicit provider are passed and they differ, raise ValueError

Architecture
1) SongData (src/innertube/data.py)
- A pure Python dataclass (no QObject) holding:
  - Identity: id, provider_id, provider_name, type ("song")
  - Core metadata: title, artist, duration, album, channelId/artistId, description, category, uploadDate, publishDate, views, tags
  - Thumbnails: list/dict with smallest/largest URLs
  - Playback: playbackInfo dict (audio/video arrays), downloadState enum, downloadProgress, dataStatus enum
  - Optional: lyrics, raw provider payloads (rawData, rawVideoDetails) for debugging
- Keep it mutable but only modified by the owning Song QObject from its own thread context

2) SongProvider protocol (src/innertube/provider.py)
- @runtime_checkable Protocol with:
  - NAME: str (e.g., "youtube", "local")
  - can_handle(full_id: str) -> bool
  - async fetch_metadata(provider_id: str) -> SongData
  - async fetch_playback_info(provider_id: str) -> dict
  - async fetch_lyrics(provider_id: str) -> dict | None
  - async download(song_data: SongData, quality: str | None = None) -> Path | None
- All methods accept provider_id (not full id) and return pure data structures; no QObject mutation

3) Provider registry (src/innertube/providers/__init__.py)
- register_provider(ProviderClass) decorator that adds to a registry
- get_provider(name: str) -> SongProvider instance
- detect_provider(full_or_bare_id: str) -> SongProvider
  - If id has a known prefix, return that provider; if bare, prefer YouTube
- Ensure this is initialized early in universal.py startup

4) Song QObject wrapper (src/innertube/song.py)
- Constructor: Song(id: str, provider: SongProvider | None = None, givenInfo: dict = {})
  - Parse id:
    - If structured: provider:type:provider_id; validate type == "song"; validate provider against explicit provider arg
    - If bare: provider arg or detect_provider(); synthesize full ID as {provider}:song:{id}
  - Singleton key: full structured ID
- Owns: self._data: SongData, self._provider: SongProvider
- Exposes QProperties and Qt Signals mirroring current usage:
  - idChanged, dataStatusChanged, playbackReadyChanged, songInfoFetched, playingStatusChanged, downloadStateChanged, downloadProgressChanged
  - Properties proxy to SongData values; signals emit when values change
- Methods delegate to provider:
  - async get_info(): provider.fetch_metadata(provider_id) -> update _data, emit songInfoFetched + dataStatusChanged
  - get_playback(): provider.fetch_playback_info(provider_id); update _data.playbackInfo; emit playbackReadyChanged
  - download(): provider.download(self._data, quality)
  - get_best_playback_mrl(): from SongData.playbackInfo or local file path if downloaded
- Preserve SongProxy and SongImageProvider; forward to new APIs with minimal changes

5) YouTubeSongProvider (src/innertube/providers/youtube.py)
- NAME = "youtube"; can_handle() handles youtube:song:* and bare IDs
- Move provider-specific logic from current Song:
  - ytmusicapi get_song, get_lyrics
  - yt_dlp extract_info, format normalization via FMT_DATA/FMT_DATA_HUMAN
  - Network checks, expiration TTLs
- Cache isolation per provider (see Cache and datastore strategy)
- Download writes metadata file (…_downloadMeta) and sets SongData.downloadState

Cache and datastore strategy (critical)
- Use separate caches and datastores per provider to avoid collisions:
  - youtube_songs_cache, local_songs_cache, …
  - youtube_song_datastore, local_song_datastore, …
- Within a provider, continue using provider_id as the key for backward compatibility
  - Example keys: dQw4w9WgXcQ_info, dQw4w9WgXcQ_playbackinfo
- One-time migration in universal.py:
  - Rename legacy songs_cache -> youtube_songs_cache
  - Relocate song_datastore -> song_datastore/youtube (or keep as default for YouTube and future providers use subdirs)

Singleton behavior
- Singleton key is full structured ID (provider:type:provider_id)
- Explicit provider argument behavior:
  - Bare ID + provider(arg) -> full ID derived from provider arg
  - Prefixed ID + mismatching provider(arg) -> ValueError (prevents accidental misuse)
  - Prefixed ID + matching provider(arg) -> returns existing singleton

QML integration
- Keep QML bindings stable; expose providerId for display/use in URLs
- Example bindings:
  - title/artist from Song properties; displayId uses providerId
  - Image provider: image://songimage/{song.providerId}/{radius}
  - External links: https://youtube.com/watch?v={song.providerId}

Migration and backward compatibility
- Bare IDs in saved queues auto-upgrade internally to youtube:song:{id}
- Persist new full IDs going forward in queue serialization
- Existing caches continue to work for YouTube after migration to provider-scoped caches
- Downloaded files in legacy datastore identified by provider_id (assumed YouTube); future providers use distinct subdirs

Potential issues and mitigations
- QML/UI display of id:
  - Issue: Full ID is verbose. Mitigation: expose displayId == providerId; QML renders title/artist for human-readable text
- Cache collisions across providers:
  - Issue: Same provider_id value could exist in different providers. Mitigation: provider-scoped caches/datastores
- Threading and data races in SongData:
  - Issue: Mutability across threads. Mitigation: Only modify SongData within Song’s thread (Qt affinity); background worker returns data to be applied on main thread
- Provider import/registration order:
  - Issue: detect_provider could fail if called before registration. Mitigation: register in universal.py early (post asyncBgworker init, before creating Songs)
- Explicit provider mismatch with prefixed ID:
  - Behavior: Raise ValueError to catch programming errors early
- Download state transitions:
  - Ensure downloadState and playbackReady signals are emitted identically to current behavior
- Lyrics availability and shape differences per provider:
  - Document contract as dict with best-effort fields; UI is tolerant to None

Local file provider: detailed design
1) ID format
- Full ID: local:song:{hash_of_path}
- Store original absolute file path in SongData.metadata["file_path"], since hash is not reversible
- providerId is the hash; displayId == providerId

2) Metadata extraction (fetch_metadata)
- Use mutagen (ID3/MP4/FLAC) to read tags and audio properties; duration from file info
- Fill title, artist, album, duration; default title to filename stem if missing
- Extract embedded cover art if present; save to a temp file or cache and expose via file:// URL as a thumbnail
- Return SongData with dataStatus = LOADED, downloadState = DOWNLOADED (local files are always present)

3) Playback info (fetch_playback_info)
- No streaming URLs; return a single audio entry with url=file:///absolute/path, ext from suffix, filesize
- Mark fromdownload=True to align with existing semantics
- get_best_playback_mrl() returns this file:// URL (immediate playback)

4) Download (download)
- Typically a no-op; optionally copy the file into the app-managed datastore if a setting requests consolidation
- If copying, write into local_song_datastore under provider_id; set/keep downloadState = DOWNLOADED

5) Lyrics (fetch_lyrics)
- Prefer embedded USLT/SYLT tags; fallback to co-located .lrc files (same basename)
- Return {"lyrics": str | None}

6) Discovery and registration
- UI adds folders/files to library; provider maintains id->path mapping in local_library_index.json
- On startup, provider loads mapping; optionally re-scans watched folders via watchdog
- Create Song instances with ids like local:song:{hash(path)}

7) Thumbnails and album art
- Extract embedded art (MP3 APIC, FLAC PICTURE); cache to disk under provider-scoped cache; expose via file:// URLs
- SongImageProvider loads image data via NetworkManager for remote images and from disk for local ones

8) Playback and Queue integration
- Works out of the box with VLCMediaPlayer: file:// URLs are supported
- Mixed queues across providers supported (YouTube, Local, etc.)

9) UI/UX
- QML displays title/artist; displayId stays providerId
- Optional provider badge per item (e.g., Local vs YouTube)

10) Error handling
- File not found -> remove from mapping, set dataStatus = ERROR, log clear message
- Permission errors -> log and surface a non-fatal error event

Requirements coverage
- Split into dataclass + frontend: SongData + SongProvider + Song QObject wrapper (Done by design)
- Protocol + consistent internal dataclass for all instances: SongProvider + SongData (Done by design)
- ID prefixing with displayId as providerId: Structured IDs; displayId = providerId (Done by design)
- Validate prefix format and provider override: Explicit validation and ValueError (Done by design)
- Singleton keyed by full structured ID: Ensures distinct songs per provider/source (Done by design)
- Refactors across Song consumers: No API break for common accessors; provider auto-detect for bare IDs; queue/VLC unaffected (Planned)
- Cache separation to avoid collisions: Provider-scoped caches and datastores + migration (Planned)

Next steps (implementation outline)
- Create SongData dataclass and SongProvider protocol files
- Implement provider registry and YouTubeSongProvider
- Refactor Song QObject to own SongData and delegate to provider
- Add provider-scoped caches/datastores and migration in universal.py
- Update instantiation sites (queuemanager, search, album, Interactions) to rely on auto-detection or pass providers as needed
- Smoke test: play a YouTube song end-to-end; ensure signals and queue behaviors unchanged
- Implement LocalFileSongProvider skeleton and wire basic library import

