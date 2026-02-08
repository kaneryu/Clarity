# Clarity – AI coding agent guide

Use these project-specific notes to be productive quickly. Keep changes aligned with existing patterns and Qt threading rules.

## Big picture
- Desktop music player (Python 3.12+, PySide6/QML) supporting multiple streaming providers.
- Entrypoint: `run.py` → initializes `src.universal` (creates singletons, workers, caches) → starts UI in `src/app/main.py`.
- UI: QML in `src/app/qml/` with context properties exposed via `engineSetup()`: `Theme` (Material You), `Backend` (app state/settings), `Interactions` (queue/playback bindings). Image providers (`SongCover`, `AlbumCover`) registered for async thumbnail loading.
- Core singletons in `src/universal.py`: `bgworker`/`asyncBgworker` (thread pools), `settings`, `globalCache`, `queueInstance`, `networkManager`, `innertubeSearchModel`. Most modules import from `universal` to access these.
- Playback architecture: `Queue` (`src/playback/queuemanager.py`) manages playlist state and delegates to pluggable player backends implementing `MediaPlayer` protocol. Default is `VLCMediaPlayer`; alternatives: `QtMediaPlayer`, `MpvMediaPlayer`. Queue integrates with Windows SMTC (`src/wintube/winSMTC`) and Discord RPC (`src/discotube/presence`).
- Provider system (`src/innertube/song/`): Songs/albums delegate to pluggable providers via `ProviderInterface` protocol. Current: YouTube (`ytmusicapi` + `yt-dlp`). Data separated into `SongData` (metadata) and `PlaybackData` (streaming formats) dataclasses. Each provider has its own cache/datastore.

## Developer workflows
- Install and run (dev mode with QML live reload):
  ```powershell
  python -m pip install --upgrade pip; pip install -e .
  python .\run.py
  ```
  Dev mode uses `main.debug()` → enables `pyside6-live-coding` for hot-reload. Ctrl+Shift+R reloads QML.
- Packaging: Nuitka options embedded as `# nuitka-project:` comments in `run.py`. Assets bundled via `--include-data-dir` directives. CI builds on push to `main` (`.github/workflows/main.yml`).
- Profiling: VS Code task "Profile main.py" uses Austin. Requires `pip install -e ".[test]"`.
- Testing: Manual tests in `tests/` (no pytest setup yet). Run interactively.

## Versioning & releases
- `version.txt` is the single source of truth for release version (consumed by CI, embedded in binary).
- Git hooks in `commit_hooks/` enforce conventional commits via `commit-msg.py`:
  - Types: `feat`, `fix`, `perf`, `refactor`, `chore`, `docs`; `BREAKING CHANGE` triggers major bump.
  - Example: `feat(queue): add debounced next/prev handling`.
  - Automated scripts: `autover.py` (semver bumps), `autochangelog.py` (generates `MOST_RECENT_CHANGELOG` for release notes).
- CI reads `MOST_RECENT_CHANGELOG` and uploads zipped Nuitka build.

## Conventions and patterns
- Imports: use absolute `src.*` imports to avoid circulars. Example: `from src import universal`, not `import universal`.
- Singletons: many classes use `__new__` to enforce single instance (e.g., `Settings`, `Backend`, `Queue`, `Song`). Always access via singleton pattern (class constructor or `.instance()` method). Song instances keyed by `NamespacedTypedIdentifier` in `Song._instances`.
- Identifiers: All IDs use namespaced format to support multiple providers:
  - `SimpleIdentifier` – raw provider ID (e.g., `dQw4w9WgXcQ`)
  - `NamespacedIdentifier` – `provider:id` (e.g., `youtube:dQw4w9WgXcQ`)
  - `NamespacedTypedIdentifier` – `provider:type:id` (e.g., `youtube:song:dQw4w9WgXcQ`)
  - Song/Album constructors accept any format or plain strings (auto-converted to typed namespaced format assuming YouTube).
  - Queue stores string representations; convert via `.from_string()` methods on identifier classes.
- Threading/Qt:
  - **Never block the Qt main thread.** Heavy work (network, file I/O, parsing) must go through `universal.bgworker` (sync tasks) or `universal.asyncBgworker` (async tasks).
  - Example: `universal.bgworker.addJob(lambda: expensive_work())` or `universal.asyncBgworker.addJob(async_function)`.
  - UI state comes from `Queue` which re-emits player signals on main thread. Emit Qt signals from correct thread using `QMetaObject.invokeMethod()` if needed.
- Logging: `universal.install_json_logging()` installs `HumanReadableConsoleFormatter` (human-readable console + JSON structured logs). Use `logging.getLogger(__name__)` over bare `print` statements.
- Paths: `src/paths.Paths` provides runtime paths (`ASSETSPATH`, `QMLPATH`, `DATAPATH`) that adapt for compiled vs dev environments (see `src/misc/compiled.py`). Always use these for file access.

## Key modules and how to extend

### Song and providers (`src/innertube/song/`)
- **Architecture**: Song class delegates to pluggable providers. Data separated into `SongData` (title, artist, duration, thumbnails) and `PlaybackData` (format streams for playback/download).
- **Creating songs**: `Song("youtube:song:VIDEO_ID")` or `Song(NamespacedTypedIdentifier(...))`. Accepts plain strings (auto-converts to YouTube).
- **Singleton behavior**: Same identifier returns same Song instance (cached in `Song._instances`).
- **Provider system**: Implement `ProviderInterface` protocol (`src/innertube/song/providers/providerInterface.py`) and register via `add_provider(name, ProviderClass)` in `registry.py`. Reference: `youtube/youtube.py`.
- **Data models**: Use dataclasses in `src/innertube/song/models/` (`SongData`, `PlaybackData`, `FormatData`). Providers parse raw API responses into these types via helper functions (e.g., `youtube/utils.py`).
- **Caching**: Each provider has its own cache/datastore (e.g., `YoutubeProvider.CACHE = globalCache.getCache("songs_cache")`). Song uses provider-specific cache for `_info` (metadata) and `_playbackinfo` (formats) keys.
- **Accessing data**: `song.title`, `song.artist` work via `__getattribute__` forwarding to `song.data.title`. Direct: use `song.data` (SongData) or `song.playbackInfo` (PlaybackData). Async fetch: `await song.get_info()`, `await song.get_playback()`.

### Queue and playback (`src/playback/queuemanager.py`)
- Add songs: `universal.queueInstance.add("youtube:song:VIDEO_ID", goto=True)` or pass `NamespacedTypedIdentifier`.
- Swap player backends: `queue.swapPlayers(YourMediaPlayer())` – implement `MediaPlayer` protocol (`MediaPlayerProtocol.py`). Protocol requires: `play(song)`, `pause()`, `stop()`, `seek(time_s)`, signals: `songChanged`, `playingStatusChanged`, `durationChanged`.
- Queue emits signals for QML bindings: `songChanged`, `playingStatusChanged`, `queueChanged` (via `queueModel`).
- Debounced next/prev (`_next()`, `_prev()`) prevent spamming; SMTC sync (`src/wintube/winSMTC`) hooks into these signals.

### Networking (`src/network.py`)
- Use `networkManager = NetworkManager.get_instance()` for all HTTP. Has retries, headers, proxy support.
- Returns `requests.Response` or `None` on failure. Always check: `if res is not None: res.content`.
- Parallel downloads: `networkManager.downloadMultiple(urls)` returns list of responses.

### Caching (`src/cacheManager/cacheManager.py`)
- Persistent caches initialized in `universal`: `imageCache`, `albumCache`, `globalCache`.
- Usage: `cache = cacheManager.getCache(name); cache.get(key); cache.put(key, value); cache.delete(key)`.
- Keys must be filesystem-safe (no spaces or path separators).
- Provider-specific: `YoutubeProvider.CACHE` (songs_cache), `YoutubeProvider.DATASTORE` (song_datastore for downloads).

### Settings (`src/misc/settings.py`)
- Add defaults to `src/app/assets/DEFAULTSETTINGS.json` (JSON tree with keys, types, defaults, descriptions).
- Access: `universal.settings.get(key)`, `universal.settings.set(key, value)` (persists and emits `settingChanged`).
- QML bindings: `Backend.settingsInterface` wraps `QmlSettingsInterface.instance()` for QML access.
- Tree model: `Backend.settingsModel` exposes hierarchical settings for QML tree views.

### App URL routing (`src/AppUrl.py`, `Backend`)
- QML navigation: `Backend.visitPath("clarity:///page/<name>")` resolves to `src/app/qml/pages/<name>.qml`.
- Query params: `Backend.getCurrentQuery()` returns dict of URL params for current page.
- Example: `clarity:///page/album?id=youtube:album:abc123` loads `album.qml` with `query["id"][0]` = album ID.

## QML integration examples
- Search from QML: `Backend.search(query)`; results bind to `Backend.searchModel` (roles: `title`, `artist`, `id`, `type`).
- Queue model: bind to `Backend.getqueueModel()`; roles: `title`, `artist`, `length`, `id`, `index`, `qobject`.
- Get objects from IDs: `Interactions.getSong(id)` returns Song QObject; `Interactions.getAlbum(id)` returns Album QObject.
- Dynamic theming: `Theme.get_dynamicColorsFromImage(path)` called on song change (`Backend.updateMaterialColors`). Theme properties auto-update QML colors.

## Gotchas
- Song identifiers: Always use namespaced format `youtube:song:ID` when passing strings. Plain YouTube video IDs are auto-converted but explicit is better for non-YouTube providers.
- Provider lookups: `get_provider(namespace)` returns `None` for unknown providers. Always null-check before accessing provider attributes.
- Song data access: `song.title` works via forwarding to `song.data.title`. For new attributes, add to `SongData` dataclass first, then provider parsing logic.
- MRL availability: `song.get_best_playback_mrl()` returns `None` if playback not fetched yet. Players handle this by calling `song.get_playback()` in background and waiting for `playbackReadyChanged` signal.
- Network failures: `NetworkManager.get()` returns `None` on failure. Always check before accessing `.content`/`.status_code`.
- Long I/O: Must run off UI thread via background workers. Example: `universal.bgworker.addJob(func)` for sync, `universal.asyncBgworker.addJob(async_func)` for async.
- Circular imports: Avoid importing `playback` from `innertube`. Use `src.universal.queueInstance` to access queue from song code.
- Asset paths: When adding runtime assets/QML, use `Paths.ASSETSPATH`, `Paths.QMLPATH`. For compiled builds, add `# nuitka-project: --include-data-*` directive in `run.py`.

## Type checker notes
PySide6/PyQt6 types confuse mypy. Common false positives:
- Properties reported as `Property` object instead of underlying type → ignore or use `# type: ignore[attr-defined]`.
- Signal argument type mismatches → ignore if runtime works correctly.
- `AbstractEventLoop | None` errors from asyncio → runtime guards prevent issues.
Configuration: `mypy.ini` has PySide6 plugin and ignore rules. Don't over-fix type errors at expense of readability.

## Extra notes
- Don't overcomment. Explain *why*, not *what*. Code should be self-documenting. Avoid redundant comments like `self.x = 5  # Set x to 5`.
- QML live coding: Dev mode has hot-reload via `pyside6-live-coding`. Save QML files → auto-reloads. Use `Backend.qmlReload()` for full reload if needed.
- Material You theming: Theme colors derived from song artwork via `materialyoucolor` library. QML binds to `Theme.primary`, `Theme.onPrimary`, etc. (auto-updates on song change).
- Some abbreviations:
- - NSID: Namespaced Identifier, like namespace:identifier
- - NTID: Namespaced Typed Identifier, like namespace:type:identifier
- - SID: Simple Identifier, just the identifier