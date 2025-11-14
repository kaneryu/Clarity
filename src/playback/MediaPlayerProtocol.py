# filepath: src/innertube/player.py
from __future__ import annotations

import time
import logging
import platform
import ctypes


from typing import Optional, Protocol, Union, runtime_checkable, Any

from src.innertube.song import Song
from src.misc.enumerations.Song import PlayingStatus


@runtime_checkable
class MediaPlayer(Protocol):
    """Abstract media playback engine contract.

    Purpose:
        Define the minimal feature + behavioral contract that any backend
        (e.g. VLC, future FFplay, MPV, custom decoder) must satisfy so the
        rest of the application (Queue, UI, integrations) can remain backend‑agnostic.

    Thread / Qt expectations:
        - All signal emissions MUST occur on the Qt main thread (QObject affinity).
        - Heavy / blocking I/O (probing, network, transcoding) MUST be delegated
          to the provided workers (see universal.bgworker / asyncBgworker)
          by concrete implementations, never inside direct slot calls.

    State model (PlayingStatus enum):
        NOT_READY  : No media loaded yet OR media placeholder while MRL resolving.
        BUFFERING  : Backend reports buffering / preroll.
        PLAYING    : Actively rendering audio.
        PAUSED     : Temporarily halted but position retained.
        STOPPED    : Intentionally stopped or media naturally ended (endReached emitted).
        (Implementations may transiently map vendor states → these canonical states.)

    Signals (all required):
        playingStatusChanged(int) : Emitted every time the canonical PlayingStatus
            changes. Payload is the integer value of the enum (never the enum object).
        durationChanged() : Fire when an actionable change in total duration (seconds)
            is known (initial load, live → VOD resolution, stream quality migration).
        timeChanged(int seconds) : Throttled (implementation defined) playback clock.
            MUST monotonically increase unless seeking or restarting.
        songChanged(int) : Active Song object changed or its resolved media (MRL) replaced.
        prevSongOnSongChange(QObject) : Previous Song object before songChanged emitted.
        endReached() : Natural media end (NOT emitted for manual stop()).
        errorOccurred(object) : Non‑recoverable backend error or unexpected failure.
            Payload SHOULD carry a backend specific event / exception object.

    General behavioral requirements:
        - All public control methods (play/pause/resume/stop/seek/aseek/pseek/reload/migrate)
          MUST be tolerant of being called when already in the target state (idempotent).
        - play(song) MUST:
            * Transition status to NOT_READY if playback MRL not yet available.
            * Emit songChanged() immediately after internal current song pointer updates.
            * Emit durationChanged() once a definitive duration is known (0 allowed).
        - Implementations SHOULD internally debounce / throttle timeChanged() to avoid UI flood.
        - Seeking MUST emit an updated playingStatusChanged(PLAYING) if the backend
          requires a re‑start or causes a transient buffer, mirroring VLC behavior.
        - migrate(mrl) keeps current position (best effort) while switching underlying
          media resource (e.g., quality upgrade, fallback). If position cannot be
          preserved, implementation SHOULD log and resume from 0.
        - reload() refetches / rebinds the media for the current Song without changing
          the logical current song reference (used after error recovery).
        - errorOccurred MUST NOT be spammed for the same root cause; implementations
          SHOULD coalesce rapid identical failures.
        - After endReached(), status SHOULD transition to STOPPED (Queue decides next).

    Return / edge cases:
        - current_duration_s(): Return 0 if unknown / not set / live.
        - current_time_s(): Return 0 if no media; never raise.
        - get_playing_status(): MUST return the integer value (not enum) for wiring
          consistency with QML / existing consumers.

    Extensibility:
        Future backends may add capabilities (e.g., volume, speed, waveform data).
        Such additions MUST remain optional and feature-detected outside this base
        protocol to preserve backward compatibility.

    Failure philosophy:
        Fail fast on invalid arguments (e.g., negative seek) via ValueError.
        Swallow backend transient errors only if an automatic retry strategy is
        in place; otherwise emit errorOccurred for supervisory layers.

    NOTE:
        This is a structural protocol; concrete implementations still inherit QObject
        for signal plumbing. Keep this spec updated if VLCMediaPlayer behavior evolves.
    """

    NAME: str  # the internal name of the mediaplayer

    # Signal attribute annotations only (no Signal() construction here). Use Any for MyPy friendliness.
    playingStatusChanged: Any
    durationChanged: Any
    timeChanged: Any
    songChanged: Any  # MUST accept an int
    prevSongOnSongChange: Any  # MUST accept a QObject

    endReached: Any
    errorOccurred: Any

    def isPlaying(self) -> bool:
        """Return True iff the canonical status is PLAYING (post-buffer, not paused)."""

    def get_playing_status(self) -> int:
        """Return the current PlayingStatus as an int (QML/consumer compatibility)."""

    def update_playing_status(self) -> None:
        """Query the underlying backend for its current state and update the internal
        PlayingStatus accordingly, emitting playingStatusChanged if it differs.
        Could be called periodically (e.g., timer), but should be called backend events."""

    def set_playing_status(self, value: PlayingStatus) -> None:
        """Force internal state machine to a new PlayingStatus and emit playingStatusChanged.
        Should only be used internally by implementations."""

    def current_duration_s(self) -> int:
        """Total media length in whole seconds; 0 if unknown / live / unset."""

    def current_time_s(self) -> int:
        """Current playback position in whole seconds (floor). 0 if no media loaded."""

    def play(self, song: Song) -> None:
        """Begin (or prepare) playback for the given Song.
        Must update current song reference immediately and emit songChanged().
        If media locator (MRL) absent, emit NOT_READY state and defer actual start."""

    def onSongMrlChanged(self, song: Song) -> None:
        """Handle the current Song's MRL change event (e.g., from async resolution).
        If the changed song is the current one and now has a valid MRL, resume playback.
        """

    def destroy(self) -> None:
        """Clean up resources, stop playback, disconnect signals, prepare for deletion."""

    def pause(self) -> None:
        """Pause playback if playing. No-op if already paused or not ready."""

    def resume(self) -> None:
        """Resume playback if paused / buffering completion allows. No-op if already playing."""

    def stop(self) -> None:
        """Stop playback (status transitions to STOPPED). Must NOT emit endReached()."""

    def reload(self) -> None:
        """Recreate / rebind the underlying backend media for the current Song (error recovery)."""

    def migrate(self, mrl: str) -> None:
        """Hot-swap underlying media resource while attempting to preserve playback position."""

    def seek(self, seconds: int) -> None:
        """Absolute seek to the given second offset. Raises ValueError if out of bounds."""

    def aseek(self, seconds: int) -> None:
        """Relative seek by delta seconds (negative allowed). Bounds clamped / validated."""

    def pseek(self, percentage: int) -> None:
        """Seek to percentage (0-100) of total duration. Raises ValueError if outside range."""
