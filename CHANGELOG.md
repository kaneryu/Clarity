# 0.54.0

## New Features

- add basic implementation for downloads page -- kaneryu on 2026-01-13

## Bugfixes

- add temporary fix for goToOrAdd in queue by modifying logic in queueIdsList -- kaneryu on 2026-01-13


# 0.53.0

## New Features

- add ability to store material colors in database -- kaneryu on 2026-01-13


# 0.52.0

## New Features

- begin implementation of database and song liking functionality -- kaneryu on 2026-01-12


# 0.51.0

## New Features

- migrate to provider-based song architecture with separated data models -- kaneryu on 2026-01-11


# 0.50.0

## New Features

- add update_playing_status method to media players, also package libvlc with clarity. -- kaneryu on 2025-11-14

## Bugfixes

- fix bug where not all songs would be added to results -- kaneryu on 2025-12-22
- make all bugfixes display under the same (major.minor.0) instead of each displaying under their own heading, and add a test mode -- kaneryu on 2025-12-22


# 0.49.0

## New Features

- display the current song title and playing status in window title -- kaneryu on 2025-10-06

## Bugfixes

- update DownloadStatus references to DownloadState in album and song modules -- kaneryu on 2025-10-06
- restore previous versioning behavior (not previous changlog behavior, though) -- kaneryu on 2025-10-06
- fix endless RecursionError in songproxy -- kaneryu on 2025-10-07
- revert completely to using legacy versioning files, and update most_recent_changelog behavior. -- kaneryu on 2025-10-08
- bug where queuemanager doesn't convert playingstatus int to playingstatus enum value -- kaneryu on 2025-10-08
- streamline presence recconect, and potentially fix bug with it. -- kaneryu on 2025-10-08
- fix bug in autochangelog where it would include too many commits in most_recent_changelog -- kaneryu on 2025-10-08
- handle missing audio and video keys in playbackInfo to prevent KeyError -- kaneryu on 2025-10-31
- albums now fetch a 'clean' song list, when possible. -- kaneryu on 2025-11-01
- fix bug where dynamic timed jobs interval doesn't increase -- kaneryu on 2025-11-04
- add previous song signal, change how getting playback status works to rely on the player's status instead of tracking it ourself (for VLC and QT only, not MPV) -- kaneryu on 2025-11-05
- Improve search transparency by logging when no results were added to the model, not just when no results were returned from the search. -- kaneryu on 2025-11-05
- Fix interactions to use the new renamed mutex variable -- kaneryu on 2025-11-05


# 0.48.0

## New Features

- add version.py, contains version information. Also add Release information -- kaneryu on 2025-10-06


# 0.47.0

## New Features

- improve QML components with particles, blur effects, and visual feedback -- kaneryu on 2025-10-04

## Bugfixes

- fix bug where run.py and main.py still used the old (broken) method to detect if they're compiled -- kaneryu on 2025-10-04
- fix bug where workers would be started up twice -- kaneryu on 2025-10-04
- fix bug where Vlc would always be loaded first regardless of user's choice -- kaneryu on 2025-10-04
- update type annotations for bgworker and asyncBgworker variables -- kaneryu on 2025-10-05
- fix bug where app would run in debugging mode even when not compiled -- kaneryu on 2025-10-05
- refactor presence management and improve status handling -- kaneryu on 2025-10-06


# 0.46.0

## New Features

- add album page with SongListModel and SongProxyListModel -- kaneryu on 2025-10-04


# 0.45.0

## New Features

- add async song insertion, goto/gotoOrAdd, and improve player backend fallback -- kaneryu on 2025-10-04


# 0.44.0

## New Features

- rename downloaded to downloadState and improve initialization -- kaneryu on 2025-10-04

## Bugfixes

- add Qt signals and proper change notifications to AppUrl -- kaneryu on 2025-10-04


# 0.43.0

## New Features

- standardize MediaPlayer with NAME constant and songChanged(int) signal -- kaneryu on 2025-10-04


# 0.42.0

## New Features

- add configurable starting interval for dynamic interval tasks -- kaneryu on 2025-10-04


# 0.41.0

## New Features

- Add occasional task management to BackgroundWorker for dynamic interval tasks, Added occasional offlinecheck and occasional discord recconect attempts (closes: 13) -- kaneryu on 2025-09-21

## Bugfixes

- made it so the albumtype is displayed in UI -- kaneryu on 2025-09-21
- don't spam online checks when we're offline -- kaneryu on 2025-09-23
- improvements to notifying logs -- kaneryu on 2025-09-23
- ensure multiple instances of interval tasks can't be started at the same time -- kaneryu on 2025-09-23


# 0.40.0

## New Features

- Implement multiple media player backends -- kaneryu on 2025-09-21

## Bugfixes

- Update _set_info validation to include EP type -- kaneryu on 2025-09-21


# 0.39.0

## New Features

- Add support for multiple media player backends; Implement FFPlay Backend -- kaneryu on 2025-09-16

## Bugfixes

- Allow album type to include singles in _set_info validation -- kaneryu on 2025-09-16


# 0.38.0

## New Features

- Add Albums. Currently available in search. -- kaneryu on 2025-09-16


# 0.37.0

## New Features

- implement debounce logic for Next and Prev song controls -- kaneryu on 2025-09-07

## Bugfixes

- fix bug where notifying log model wouldn't add logs based on error level, and disable song fetching if we're offline -- kaneryu on 2025-09-08
- bug where incorrect offline check led to infinite recursion -- kaneryu on 2025-09-09
- decrease offline mode timeout check for faster offline startup -- kaneryu on 2025-09-09
- make various bugfixes so the app now compiles again -- kaneryu on 2025-09-13
- add error catching for search, and add hot reload plugin for development -- kaneryu on 2025-09-14


# 0.36.0

## New Features

- add dynamic color based on current song cover -- kaneryu on 2025-09-07

## Bugfixes

- Emit endReached signal immediately on song finish instead of using QTimer -- kaneryu on 2025-09-07


# 0.35.0

## New Features

- intergrate with winsmtc play, pause, next and prev buttons -- kaneryu on 2025-09-01

## Bugfixes

- Move default settings out of code, and make sure that the active settings file updates itself to the default setting's file schema -- kaneryu on 2025-09-03
- Update path constants to use uppercase naming convention and add online status management in NetworkManager -- kaneryu on 2025-09-04
- Fix bug where orphaned items would never actually be deleted in intergrity check -- kaneryu on 2025-09-04


# 0.34.0

## New Features

- implement dataStore integrity restoration in integrityCheck method -- kaneryu on 2025-08-23

## Bugfixes

- update search function to allow None as a filter, add copilot Instructions -- kaneryu on 2025-08-24
- add ratelimit to discord presence -- kaneryu on 2025-08-24
- add some extra resiliency to search -- kaneryu on 2025-09-01
- Skipping forwards in progressbar not functioning -- kaneryu on 2025-09-01


# 0.33.0

## New Features

- add basic integration with windows SMTC -- kaneryu on 2025-08-23


# 0.32.0

## New Features

- implement logging system with notification support and structured log history -- kaneryu on 2025-08-08

## Bugfixes

- allow for use of video as a playback MRL -- kaneryu on 2025-08-13
- make presence use artist instead of song title -- kaneryu on 2025-08-23


# 0.31.0

## New Features

- add settings page -- kaneryu on 2025-08-01

## Bugfixes

- fix bug where settings would not save to disk -- kaneryu on 2025-08-01


# 0.30.0

## New Features

- add new discord RPC feature -- kaneryu on 2025-07-27

## Bugfixes

- add ability for downloader to retry downloading song if chunking doesn't work -- kaneryu on 2025-07-27


# 0.29.0

## New Features

- begin work on login -- kaneryu on 2025-03-09

## Bugfixes

- make progressbar a bit larger -- kaneryu on 2025-03-12
- add some things to cleanup -- kaneryu on 2025-03-14
- Bump dependencies, swap out ytmusicapi for my own version (still async) -- kaneryu on 2025-07-02
- Make sure presence is stopped and the thread is properly deleted when the app is closed -- kaneryu on 2025-07-03
- codebase now passes mypy check (not in strict mode, with some changes made in mypy.ini) -- kaneryu on 2025-07-05
- songs can now be in the queue without a MRL ready -- kaneryu on 2025-07-07
- If expiration isn't set, ignore it -- kaneryu on 2025-07-07
- Add active song playing check -- kaneryu on 2025-07-27


# 0.28.0

## New Features

- implement part of reworked networking -- kaneryu on 2025-03-08


# 0.27.0

## New Features

- Add functioning marquee to text elements -- kaneryu on 2025-03-04


# 0.26.0

## New Features

- added base for settings -- kaneryu on 2025-03-01

## Bugfixes

- remove KImage (closes #4) -- kaneryu on 2025-03-01
- use logging in both datastore and cache, and make cache more resilient to being moved. -- kaneryu on 2025-03-02
- Fix bug where going to the next song would hang the application; also improve job handling in background workers & split queue class up for easier managment -- kaneryu on 2025-03-03


# 0.25.0

## New Features

- add rich presence support -- kaneryu on 2025-02-28


# 0.24.0

## New Features

- improve queueview visuals -- kaneryu on 2025-02-21

## Bugfixes

- add mouseblocker on queue view so clicks and scrolls don't pass through it -- kaneryu on 2025-02-21
- make search use the default song thing -- kaneryu on 2025-02-22
- bug where search used the wrong ID in searchpress -- kaneryu on 2025-02-23
- remove kimage from interactions -- kaneryu on 2025-02-25


# 0.23.0

## New Features

- Added busyindicators to image to show when the image is loading -- kaneryu on 2025-02-21

## Bugfixes

- fixed a few startup bugs, made queueview use the Song object -- kaneryu on 2025-02-21
- made duration available from song object -- kaneryu on 2025-02-21


# 0.22.0

## New Features

- add song image provider, to start moving away from KImage (#4) -- kaneryu on 2025-02-20


# 0.21.0

## New Features

- assosiate song kimages with songs #3 -- kaneryu on 2025-02-18


# 0.20.0

## New Features

- Add font files to the application with a test on the homepage -- kaneryu on 2025-01-25

## Bugfixes

- bug in cacheManager that didn't use asyncio.lock on deleting a key, and also integrity check having incorrect implementation. -- kaneryu on 2025-02-02
- fix bug in cachemanger caused by using async lock in non-async functions -- kaneryu on 2025-02-02
- fix bug in workers that didn't call the callback if using putcoverconvert, and fix bug that didn't convert coverconvert key into path before returing it to the UI -- kaneryu on 2025-02-02
- fix bug where non-rounded cover would be returned when retrieveing cover from cache -- kaneryu on 2025-02-02
- fix bug in kimage that wouldn't initialize a variable before downlading the image -- kaneryu on 2025-02-03
- fix bug in song where playback info was never downloaded in the first place -- kaneryu on 2025-02-03
- fix various bugs in cacheManager, while working on the Song tile -- kaneryu on 2025-02-17
- fix bug where status wasn't updated when fetching image from cache -- kaneryu on 2025-02-17


# 0.19.0

## New Features

- Add functionality to the queueview -- kaneryu on 2025-01-23

## Bugfixes

- fix title in queue, fix overlapping issue in song results -- kaneryu on 2025-01-23
- fix bug where seeking would cause the play button to show buffering indef -- kaneryu on 2025-01-24
- song duration not updating -- kaneryu on 2025-01-24


# 0.18.0

## New Features

- Add prerequisite for queuePanel -- kaneryu on 2025-01-23


# 0.17.0

## New Features

- Improve semantics around the play/pasue button, and fix a bug where it wouldn't update sometimes -- kaneryu on 2025-01-22


# 0.16.0

## New Features

- replace placeholder text on songbar to be icons -- kaneryu on 2025-01-21

## Bugfixes

- fix spacing and icon height -- kaneryu on 2025-01-22


# 0.15.0

## New Features

- Song no longer downloads playback info from internet if it's already downloaded -- kaneryu on 2025-01-11

## Bugfixes

- Fix searchModel returning KImage living in different thread -- kaneryu on 2025-01-11
- fix multiple bugs related to downloading songs -- kaneryu on 2025-01-19
- fix bug where songs could not be played if the download was corrupted -- kaneryu on 2025-01-19
- Add mutexes to increase thread safety -- kaneryu on 2025-01-21


# 0.14.0

## New Features

- Add song downloading -- kaneryu on 2025-01-06

## Bugfixes

- fix None in coverconvert caused by imageCache being set too early -- kaneryu on 2025-01-06
- try a fix for no corner radius showing in the songbar image -- kaneryu on 2025-01-06
- Fix random application crash by not directly accessing song object that lives in a different thread using QML. -- kaneryu on 2025-01-07
- fix bug where QML didn't recive the song object properly -- kaneryu on 2025-01-08
- Try another fix for random application crashes because trying to access Song in different thread -- kaneryu on 2025-01-08
- Speed up setqueue by a bit -- kaneryu on 2025-01-11
- Yet another try to fix random application crashes, using an interface to access KImage living in different thread -- kaneryu on 2025-01-11


# 0.13.0

## New Features

- Improve songbar, add threading to non-async bgworker, refactor some stuff -- kaneryu on 2025-01-02

## Bugfixes

- added fault tolerance to convertocover by making sure that cache is always set to a real cache instead of None -- kaneryu on 2025-01-03
- added fault tolerance to the queue by allowing it to ask for a song's data to be refetched. -- kaneryu on 2025-01-04


# 0.12.0

## New Features

- complete alpha songbar -- kaneryu on 2024-12-26


# 0.11.0

## New Features

- Added song cover, song details to the songbar -- kaneryu on 2024-12-25


# 0.10.0

## New Features

- add prelim stuff for songbar -- kaneryu on 2024-12-23


# 0.9.0

## New Features

- add pages to the app using a URL scheme, with innertune:// as the protocol -- kaneryu on 2024-12-21

## Bugfixes

- add versions as datafiles, add app icon to app. -- kaneryu on 2024-12-22


# 0.8.0

## New Features

- added images to search results in QML, also refactored a few things to do so. -- kaneryu on 2024-12-21

## Bugfixes

- fix version file not being found causing application crash -- kaneryu on 2024-12-21


# 0.7.0

## New Features

- added autoversioning using conventional commits -- kaneryu on 2024-12-19

## Bugfixes

- clean up autover.py for use in commit hooks -- kaneryu on 2024-12-19
- fix bug in autover where commit history was reversed. -- kaneryu on 2024-12-19


# 0.6.0

## New Features

- Added preliminary version of search, and made connection the the UI. it can also play songs from the results. -- kaneryu on 2024-12-19


# 0.5.0

## New Features

- try a fix for build failing -- kaneryu on 2024-12-18

## Bugfixes

- Update run.py -- kaneryu on 2024-12-19
- switched from using --standalone to --mode=app -- kaneryu on 2024-12-19
- fix issues caused queue module having a name conflict -- kaneryu on 2024-12-19


# 0.4.0

## New Features

- add requirements so workflow functions -- kaneryu on 2024-12-18

## Bugfixes

- update action -- kaneryu on 2024-12-18
- Move yt_dlp fix (occured in untracked file, involved deleting a bunch of code) into a config.yaml. Also included proper dependencies in the requirements.txt for the aciton. -- kaneryu on 2024-12-18
- windows only -- kaneryu on 2024-12-18


# 0.3.0

## New Features

- enhance cache integrity checks and cleanup process via new integrityCheck function -- kaneryu on 2024-12-18

## Bugfixes

- made sure gitignore ignores cache files -- kaneryu on 2024-12-18
- make some changes to make freezing via nuitka work, and add the configuration to run.py -- kaneryu on 2024-12-18


# 0.2.0

## New Features

- added the QueueModel, and connected it to the QML. -- kaneryu on 2024-12-18

## Bugfixes

- make cache more resistant when data is deleted but the reference is not -- kaneryu on 2024-12-18


# 0.1.0

## New Features

- added the basic queue and player, and made the connection from it to the GUI -- kaneryu on 2024-12-17


# 0.0.0


