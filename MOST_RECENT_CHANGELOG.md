# Changes Since Last Release

- (0.59.0) add temporary liked songs page -- kaneryu on 2026-04-16
bug where playingstatus wouldn't update -- kaneryu on 2026-04-17
- (0.58.0) add download status management to  SongRepository, and migrate song to use it. -- kaneryu on 2026-04-16
Also migrate downloadpage to use database also -- kaneryu on 2026-04-16
- (0.57.0) add right click menu with a few functions -- kaneryu on 2026-04-15
- (0.56.0) add first tabs implementation. -- kaneryu on 2026-04-12
Move lazyload away from bgworker to speed up application load -- kaneryu on 2026-04-13
- (0.55.0) add basic implementation for checkboxes -- kaneryu on 2026-02-13
refactor database -- kaneryu on 2026-02-16
Temporarily increase default task timeout -- kaneryu on 2026-02-22
Add fallback image for presence so it doesn't error 100 times a second -- kaneryu on 2026-02-23
update thumbnail URL references and add bestThumbnailUrl property to ensure images work everywhere -- kaneryu on 2026-03-09
race condition in song downloads -- kaneryu on 2026-04-12
add temporary login, fix some bugs, some misc housekeeping -- kaneryu on 2026-04-12
- (0.54.0) add basic implementation for downloads page -- kaneryu on 2026-01-13
add temporary fix for goToOrAdd in queue by modifying logic in queueIdsList -- kaneryu on 2026-01-13
- (0.53.0) add ability to store material colors in database -- kaneryu on 2026-01-13
- (0.52.0) begin implementation of database and song liking functionality -- kaneryu on 2026-01-12
- (0.51.0) migrate to provider-based song architecture with separated data models -- kaneryu on 2026-01-11
