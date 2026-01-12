## Plan: Split Song into SongData + provider-backed Song

We’ll separate immutable, provider-agnostic data (SongData) from a provider-driven Song manager class. Song becomes a thin QObject that adapts to providers (YouTube, Local, etc.), preserves QML properties/signals and queue semantics, and enforces a strict identity scheme. We’ll add a provider registry and protocols, maintain backward compatibility for bare YouTube IDs, and document a testing matrix, edge cases, and a phased rollout with rollback.

### Steps
1. Define identity scheme and validation; normalize fullId/providerId in `src/innertube/song.py`.
2. Finalize provider Protocol/registry; register default provider in `src/universal.py`.
3. Complete SongData contract and normalization; map SongData -> legacy attributes.
4. Delegate metadata/playback/download/lyrics to providers; preserve QML signals/properties.
5. Sweep usages (`src/playback/queuemanager.py`, QML) for unchanged behavior and id semantics.
6. Add Local provider design, tests, migration notes, and phased rollout + rollback plan.

### 1) Goals and design

- Identity scheme
  - fullId = "provider:type:provider_id" (example: "youtube:song:abc123").
  - Display id for UI/cache is provider_id only (bare).
  - QML exposes providerId and providerName; Song.id returns bare provider_id.
  - Legacy bare ids default to provider "youtube" and type "song".
  - Strict validation when prefix present:
    - Must match "<provider>:song:<provider_id>" exactly (3 segments).
    - Error on wrong type or malformed segments.
    - Normalize: store providerName, providerId, fullId; id property returns providerId.

- Provider registry
  - SongProvider protocol with async methods:
    - fetch_metadata(provider_id, cache_only=False) -> SongData
    - fetch_playback_info(provider_id) -> dict
    - fetch_lyrics(provider_id) -> Optional[dict]
    - download(SongData, quality=None) -> Optional[Path or str]
    - purge_playback_cache(provider_id) -> None
  - Registry supports register(name, provider), get(name|default), set_default(name), detect(full_or_bare_id).
  - Default provider: "youtube" registered at startup.

- SongData fields and normalization
  - Identity: id (fullId), provider_id, provider_name, type="song".
  - Source/state: source ("search"|"full"…), dataStatus enum.
  - Core metadata: title, artist, channel, channelId, artistId, duration, views.
  - Dates: uploadDate/publishDate (ISO8601 or None) + timestamps; if parse fails → None.
  - Thumbnails: thumbnails list; smallestThumbnailUrl/largestThumbnailUrl/rectangleThumbnailUrl/fullUrl (Optional[str]).
  - Raw payload buckets for provider rehydration.
  - Playback: playbackInfo dict, downloadMeta dict, downloadState, downloadProgress.
  - Lyrics: Optional[dict].
  - Normalization rules:
    - Strings default to "" if essential for UI (title, artist); otherwise Optional.
    - Integers default to 0 only when UI binds immediately; else Optional[int].
    - Never block main thread to derive/parse; do I/O off the main thread.

- Threading and signals boundary
  - All network and heavy I/O via universal.bgworker or universal.asyncBgworker.
  - Song emits QML signals only from its own thread; if needed, re-emit with queued connections.
  - Preserve existing QML signals/properties:
    - Signals: idChanged, sourceChanged, dataStatusChanged, downloadStateChanged, downloadProgressChanged, playbackReadyChanged, songInfoFetched, playingStatusChanged.
    - Properties: id (bare), providerId, providerName, source, dataStatus, downloadState, downloadProgress, playbackReady, and legacy fields mapped from SongData (title, artist, description, duration, views, upload/publish dates, thumbnails, etc.).

### 2) File-by-file change list (src/**)

- `src/innertube/song.py`
  - Identity handling:
    - Parse input id; validate strict shape when prefixed; normalize to providerName/providerId/fullId; keep `id` = bare providerId.
    - Add `providerId` and `providerName` QProperties (read-only); keep `id` read-only in QML with setter helpers internally.
  - Provider delegation:
    - Replace direct ytmusicapi/yt-dlp logic with calls to registry provider:
      - get_info() → provider.fetch_metadata(providerId, cache_only=False)
      - get_info_cache_only() → provider.fetch_metadata(providerId, cache_only=True)
      - get_playback()/download_playbackInfo() → provider.fetch_playback_info(providerId)
      - download() → provider.download(SongData(..., playbackInfo=...))
      - purge_playback() → provider.purge_playback_cache(providerId) + legacy purge
      - get_lyrics() → provider.fetch_lyrics(providerId) with fallback.
  - SongData mapping:
    - Implement `_apply_songdata(data: SongData)` to set legacy attributes and emit `songInfoFetched`, set `dataStatus` and recompute `playbackReady`.
    - Keep thumbnail URL fields and largestThumbnailUrl used by image providers.
  - QML contracts:
    - Preserve/forward `playbackReadyChanged`, `idChanged`, `songInfoFetched`.
    - Ensure `PlayingStatus` integration remains (via Queue re-emission).
  - Read-only QProperties with setter helpers:
    - Internally use setId/setSource/setDataStatus/setDownloadState/setDownloadProgress to update and emit.
  - Singleton semantics:
    - Keep singleton map keyed by input id string (structured or bare) for backward compatibility.
    - Document that if an instance exists, manual provider override is ignored; mitigation documented in migration section.

- `src/innertube/models/song_data.py`
  - Confirm dataclass fields cover identity, metadata, thumbnails, playback, lyrics, and raw payloads.
  - Document normalization rules and Optional vs default behavior in comments/docstrings.
  - No UI-thread operations in dataclass.

- `src/innertube/providers/protocols.py`
  - Define SongProvider Protocol as above (async signatures).
  - Optionally runtime_checkable for developer errors; keep light typing due to PySide6 typing quirks.

- `src/innertube/providers/registry.py`
  - Verify ProviderRegistry has register/get/set_default/detect; detect validates structured ids and returns provider by name; default for bare ids.
  - Add strict validation helpers for fullId shape.

- `src/innertube/providers/constants.py`
  - Centralize FMT_DATA/FMT_DATA_HUMAN; ensure providers import these.

- `src/innertube/providers/youtube.py`
  - Implement SongProvider:
    - fetch_metadata: ytm.get_song, cache key "<provider_id>_info", normalize to SongData; LOGIN_REQUIRED/ERROR -> NOTLOADED.
    - fetch_playback_info: yt-dlp, exclude m3u8 formats, quality mapping/sort; cache key "<provider_id>_playbackinfo".
    - download: pick best audio/video, write to song_datastore using provider_id; write "<provider_id>_downloadMeta".
    - fetch_lyrics: ytm.get_lyrics.
    - purge_playback_cache: clear cache entries and datastore file/meta.
  - Ensure no UI thread blocking; use bgworker/asyncBgworker in callers.

- `src/innertube/providers/local.py` (new; detailed design in section 6)
  - Implement LocalSongProvider with identity "local:song:<fs-safe-key>".

- `src/innertube/providers/__init__.py`
  - Export registry helpers; optionally expose register_provider/get_provider convenience.

- `src/universal.py`
  - Register default providers at startup:
    - Import YouTubeSongProvider and register("youtube", instance); set default.
    - Optionally discover/register Local provider.
  - Keep existing caches/datastores; no behavior changes required.

- `src/playback/queuemanager.py`
  - No behavior change expected:
    - We already use Song.id for queueIds (still bare provider_id).
    - playbackReadyChanged -> Queue.songMrlChanged remains wired.
    - get_best_playback_mrl semantics unchanged.
  - Confirm `goToSong`/`gotoOrAdd` accept structured ids transparently (Song normalizes id to bare).

- `src/app/qml/*`
  - Expectations remain:
    - Display id uses provider_id (Song.id).
    - If needed, UI can compose "(provider) provider_id" using providerName/providerId.
    - Theme interactions remain unchanged.
    - Image provider uses Song.largestThumbnailUrl; no change required.

- `src/innertube/search.py` and model usages
  - Ensure `from_search_result` in Song accepts both "videoId" and "id", sets provider mapping correctly.

### 3) Migration and compatibility

- Bare IDs default to YouTube:
  - Input "abc123" → providerName "youtube", providerId "abc123", fullId "youtube:song:abc123".
- Structured IDs:
  - For caches/datastores, strip prefix and key by provider_id for YouTube (unchanged key names).
  - Download datastore continues using provider_id for filenames and "<provider_id>_downloadMeta" for metadata.
- Backwards compatibility contract:
  - Song.id returns bare provider_id for QML and queue.
  - .providerId and .providerName added for QML; idChanged behavior unchanged.
  - Singletons are keyed by the input string (structured or bare). If a Song was created with one form, a subsequent creation with a different provider hint but same key string returns the existing instance. Mitigation: normalize callers to a single form (prefer fullId), or explicitly purge/clear singleton mapping for development/testing, or use a factory that normalizes keys to fullId to avoid duplicates if desired in the future.

### 4) Edge cases and error handling

- Network offline:
  - fetch_metadata(cache_only=True) path; set DataStatus.NOTLOADED; image provider uses placeholder; playbackInfo returns {"audio": None, "video": None}.
- Cache-only paths:
  - If cache miss and cache_only=True, return SongData with NOTLOADED and do not mutate UI fields beyond NOTLOADED state.
- Login-required or error statuses:
  - Treat as NOTLOADED; log warnings; do not crash; do not emit misleading loaded state.
- Playback info absent or m3u8 formats only:
  - Exclude m3u8; if no viable formats, set playbackInfo {"audio": None, "video": None} and playbackReady False.
- Corrupted download metadata:
  - On read error for "<provider_id>_downloadMeta", warn and refetch playback info; do not crash.
- Retries and fallbacks:
  - On provider failures, log and fall back to legacy path where possible (YouTube only); retry briefly via networkManager if download parallel path fails; then single-thread download fallback.

### 5) Testing strategy

- Unit-level
  - Provider registry: register/get/set_default/detect; invalid id format raises; bare id uses default.
  - SongData mapping: provider SongData -> Song; fields mapped; dataStatus transitions; playbackReady semantics.
  - YouTube provider normalization: title/artist/duration/thumbnail URLs; LOGIN_REQUIRED/ERROR -> NOTLOADED.
  - Playback info selection: quality sort; exclude m3u8; audio preferred; video fallback.
  - Purge behavior: cache keys removed; datastore files/meta removed; Song state resets and re-fetch works.
- Integration
  - Queue add/goto: add bare and structured ids; queueIds remain bare; playbackReadyChanged triggers MRL migration.
  - Image provider: caches masked images; uses largestThumbnailUrl; falls back to placeholder offline.
  - Download flow: writes file + "<provider_id>_downloadMeta"; Song transitions to DOWNLOADED and returns file path for MRL.
  - Lyrics fetch optional: provider returns None without errors; Song.lyrics set when available.

### 6) Local file provider design (detailed)

- Identity
  - fullId: "local:song:<fs-safe-key>"; provider_id is a key derived from absolute path hashed to an fs-safe key (e.g., md5).
  - Display id: fs-safe key (Song.id).
- Metadata
  - Read via mutagen/taglib in background worker; no UI thread blocking.
  - Thumbnails: embedded album art if present; otherwise generate a waveform or use a placeholder; cache image bytes in images_cache keyed by content hash or path-hash.
  - Duration via probe (ffprobe/mutagen), off the main thread.
  - publish/upload dates empty; views None.
- Playback
  - Return file URL with extension; no yt-dlp; quality list single item representing the file.
  - purge_playback_cache() is a no-op (or clears provider-local caches only).
- Download
  - No-op; return Path to existing file; download state treated as DOWNLOADED immediately when Song constructed with valid path mapping (or after background validation).
- Lyrics
  - Optionally read sidecar .lrc next to the file; if present, parse in background; else None.
- Caching
  - Use song_datastore or a dedicated local_files datastore for thumbnails/waveforms; keys are fs-safe path-hashes.
- QML
  - Display via existing bindings (title/artist/duration/thumbnail); id remains fs-safe key; providerName "local".

### 7) Risks and mitigation

- Threading violations
  - Enforce all provider I/O on background workers; only emit signals and assign QProperties on Song instance thread.
- Long I/O in providers
  - Use universal.bgworker/asyncBgworker; incremental updates signaled via downloadProgress.
- Circular imports
  - Providers should not import queue; Song should reference universal.queueInstance for migration calls only.
- Cache miss semantics
  - Be explicit with NOTLOADED vs LOADED; don’t emit songInfoFetched until mapped.
- QML expecting immediate data
  - Provide defaults to avoid attribute errors; emit songInfoFetched promptly after mapping; leave id stable.
- Test flakiness
  - Isolate network in tests; mock networkManager/ytmusicapi/yt-dlp; use temporary caches/datastores.

### Phased timeline with checkpoints and rollback

- Phase 1: Protocols and registry
  - Implement SongProvider protocol, registry, constants; register YouTube in `universal.py`.
  - Checkpoint: unit tests for registry/protocol; app still uses current Song paths.
  - Rollback: Disable provider registration; fall back to legacy Song paths.

- Phase 2: SongData and mapping
  - Finalize `SongData`; add `_apply_songdata` in Song; keep legacy fetch as fallback.
  - Checkpoint: Song loads from cache_only and full; signals unchanged in QML.
  - Rollback: Short-circuit to legacy _set_info; keep identity normalization.

- Phase 3: Delegate metadata/playback/lyrics
  - Wire Song methods to provider; keep legacy fallback for YouTube only.
  - Checkpoint: queue add/play/downloading works; playbackReady semantics preserved; images render.
  - Rollback: Toggle a feature flag to force legacy paths.

- Phase 4: Local provider (optional preview)
  - Implement Local provider; limited UI surface; behind a developer toggle.
  - Checkpoint: Add local files, playback works, no download action.
  - Rollback: Unregister Local provider; no impact to YouTube behavior.

- Phase 5: Migration polish and tests
  - Add tests (unit/integration) and compatibility/migration notes.
  - Checkpoint: CI green, manual smoke on Windows; cache/datastore unchanged.

- Phase 6: Harden and clean
  - Remove dead legacy code paths where safe; keep minimal fallback for stability.
  - Checkpoint: telemetry/logs clean; no regressions in queue/QML.

### Further Considerations
- Provider keying for singletons: keep input-keyed now; consider normalizing to fullId later.
- Optional feature flag: enable/disable provider system globally for quick rollback.
- Error surfacing: consider lightweight user-facing notifications for login-required/offline states.

