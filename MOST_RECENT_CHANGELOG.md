# Changes Since Last Release

- (0.49.5) bug where queuemanager doesn't convert playingstatus int to playingstatus enum value -- kaneryu on 2025-10-08
- (0.49.4) revert completely to using legacy versioning files, and update most_recent_changelog behavior. -- kaneryu on 2025-10-08
- (0.49.3) fix endless RecursionError in songproxy -- kaneryu on 2025-10-07
- (0.49.2) restore previous versioning behavior (not previous changlog behavior, though) -- kaneryu on 2025-10-06
- (0.49.1) update DownloadStatus references to DownloadState in album and song modules -- kaneryu on 2025-10-06
- (0.49.0) display the current song title and playing status in window title -- kaneryu on 2025-10-06
- (0.48.0) add version.py, contains version information. Also add Release information -- kaneryu on 2025-10-06
- (0.47.9) refactor presence management and improve status handling -- kaneryu on 2025-10-06
- (0.47.8) fix bug where app would run in debugging mode even when not compiled -- kaneryu on 2025-10-05
- (0.47.7) update type annotations for bgworker and asyncBgworker variables -- kaneryu on 2025-10-05
- (0.47.6) fix bug where Vlc would always be loaded first regardless of user's choice -- kaneryu on 2025-10-04
- (0.47.5) fix bug where workers would be started up twice -- kaneryu on 2025-10-04
- (0.47.4) fix bug where run.py and main.py still used the old (broken) method to detect if they're compiled -- kaneryu on 2025-10-04
