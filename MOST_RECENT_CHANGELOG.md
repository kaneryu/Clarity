# Changes Since Last Release

- (0.50.0) add update_playing_status method to media players, also package libvlc with clarity. -- kaneryu on 2025-11-14
- (0.49.14) Fix interactions to use the new renamed mutex variable -- kaneryu on 2025-11-05
- (0.49.13) Improve search transparency by logging when no results were added to the model, not just when no results were returned from the search. -- kaneryu on 2025-11-05
- (0.49.12) add previous song signal, change how getting playback status works to rely on the player's status instead of tracking it ourself (for VLC and QT only, not MPV) -- kaneryu on 2025-11-05
- (0.49.11) fix bug where dynamic timed jobs interval doesn't increase -- kaneryu on 2025-11-04
- (0.49.9) albums now fetch a 'clean' song list, when possible. -- kaneryu on 2025-11-01
- (0.49.8) handle missing audio and video keys in playbackInfo to prevent KeyError -- kaneryu on 2025-10-31
- (0.49.7) fix bug in autochangelog where it would include too many commits in most_recent_changelog -- kaneryu on 2025-10-08
