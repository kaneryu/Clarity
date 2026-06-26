import logging
import time

from dataclasses import dataclass
from datetime import datetime, timezone

from typing import Union

from PySide6.QtCore import QObject

from src.providerInterface.globalModels import (
    NamespacedTypedIdentifier,
    NamespacedIdentifier,
    SimpleIdentifier,
    allIdTypes,
    str_to_identifer,
)
from src.misc.enumerations.Song import DownloadState
from src.databaseInterface.repoHost import songRepository, listenRepository

from src.misc.utils import ghash


def createListenId(song_id: NamespacedTypedIdentifier, timestamp: str) -> str:
    """Creates a unique listen ID based on the song ID and timestamp."""
    parta = ghash(str(song_id) + timestamp)
    return str(
        NamespacedTypedIdentifier.from_parts(
            namespace="interaction", type_="listen", id_=parta
        )
    )


@dataclass
class ActiveListenEvent:
    """Represents an in-progress listening session.

    Args:
        song_id (NamespacedTypedIdentifier): The ID of the song being listened to.
        timestamp (str): ISO timestamp for when the session started.
        duration (float): The accumulated listened duration in seconds.
        counted (bool): Whether or not this session has crossed the play threshold.
    """

    song_id: NamespacedTypedIdentifier
    timestamp: str
    duration: float

    counted: bool = False


@dataclass(frozen=True)
class ListenEvent:
    """Represents a listening event. This is an immutable version of ActiveListenEvent.
    Note that the ID has been converted to a string.

    Args:
        id: (str): The unique identifier for this listen event. This is generated when the event is finalized.
        song_id (str): The ID of the song being listened to.
        timestamp (str): ISO timestamp for when the session started.
        duration (float): The duration of the listening event in seconds.
        counted (bool): Whether or not this session crossed the play threshold.
        countedAt (float): The play threshold in seconds at the time this listen was counted.
        liked (bool): Whether or not the song was liked when the session ended.
        downloaded (bool): Whether or not the song was downloaded when the session ended.
    """

    id: str
    song_id: str
    timestamp: str
    end_timestamp: str  # remeber to look at the ai chat for the other stats
    duration: float

    counted: bool = False
    countedAt: float = 30.0  # The threshold at the time this listen was counted
    liked: bool = False
    downloaded: bool = False


class ListenTracker(QObject):
    """Tracks listened time for a single active song session.

    The tracker is intentionally self-contained and playback-backend agnostic.
    Callers advance it only while a song is actively playing. When playback is
    paused, buffering, or otherwise inactive, callers should stop ticking and
    call pause_tracking() so no time is backfilled.
    """

    cache: dict[str, list[ListenEvent]] = (
        {}
    )  # temporary in memory cache for listen events, keyed by song ID. This is not persisted and will be lost on shutdown.

    PLAY_COUNT_THRESHOLD_S = 30.0

    def __init__(self, parent=None):
        super().__init__(parent)

        self.logger = logging.getLogger(__name__)

        self._current_listen_event: Union[ActiveListenEvent, None] = None

        self.accumulated_listen_time: float = 0.0
        self.last_tick_mono: float = 0.0

    @staticmethod
    def _timestamp_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_song_id(
        song_id: Union[allIdTypes, str],
    ) -> NamespacedTypedIdentifier:

        if isinstance(song_id, str):
            song_id = str_to_identifer(song_id)

        if isinstance(song_id, NamespacedTypedIdentifier):
            if song_id.type != "song":
                raise ValueError("ID type must be 'song'.")
            return song_id

        if isinstance(song_id, NamespacedIdentifier):
            return NamespacedTypedIdentifier(namespacedIdentifier=song_id, type="song")

        if isinstance(song_id, SimpleIdentifier):
            raise ValueError(f"This is probably not an ID: {song_id}")

        raise TypeError(f"Unsupported song ID type: {type(song_id)}")

    def _start_new_session(self, song_id: NamespacedTypedIdentifier) -> None:
        self._current_listen_event = ActiveListenEvent(
            song_id=song_id,
            timestamp=self._timestamp_now(),
            duration=0.0,
        )
        self.accumulated_listen_time = 0.0
        self.last_tick_mono = time.monotonic()

    def _update_active_duration(self) -> None:
        if self._current_listen_event is None or self.last_tick_mono == 0.0:
            return

        current_time = time.monotonic()
        elapsed = max(0.0, current_time - self.last_tick_mono)

        self._current_listen_event.duration += elapsed
        self.accumulated_listen_time = self._current_listen_event.duration
        self.last_tick_mono = current_time

        if self._current_listen_event.duration >= self.PLAY_COUNT_THRESHOLD_S:
            self._current_listen_event.counted = (
                True  # TODO: Add logic to put this in db when counted.
            )

    def has_active_session(self) -> bool:
        return self._current_listen_event is not None

    def pause_tracking(self) -> None:
        """Stops time accumulation until playback becomes active again.
        Note that resume must be called afterwards to re-arm the monotonic anchor; listen_tick does not auto-resume.
        The current session will be erased and restarted otherwise due to the large time delta.
        """
        self._update_active_duration()
        self.last_tick_mono = 0.0
        # TODO: Probably should just remove this function in the future.

    def resume_tracking(self) -> None:
        """Re-arms the monotonic anchor without backfilling paused time."""
        if self._current_listen_event is None:
            return
        self.last_tick_mono = time.monotonic()

    def listen_tick(self, song_id: Union[allIdTypes, str]) -> ListenEvent | None:
        """Advance the active session and optionally roll over on song change.

        Args:
            song_id (allIdTypes): The ID of the currently playing song.

        Returns:
            ListenEvent | None: Finalized previous session if the song changed,
            otherwise None.
        """
        normalized_song_id = self._normalize_song_id(song_id)

        # We're expecting ticks every twoish seconds from the queue, so as a sanity check
        # We'll ignore the event if the time is > than 10 seconds, instead resetting the session.

        if self._current_listen_event and self.last_tick_mono:
            time_since_last_tick = time.monotonic() - self.last_tick_mono
            if time_since_last_tick > 10.0:
                self.logger.warning(
                    f"Time since last tick is {time_since_last_tick:.1f}s, which is longer than expected. Resetting listen session for song ID {normalized_song_id}."
                )
                self.finalize_listen()

        if self._current_listen_event is None:
            self._start_new_session(normalized_song_id)
            return None

        if self._current_listen_event.song_id != normalized_song_id:
            finalized = self.finalize_listen()
            self._start_new_session(normalized_song_id)
            return finalized

        if self.last_tick_mono == 0.0:
            self.last_tick_mono = time.monotonic()
            return None

        self._update_active_duration()
        return None

    def discard_current_session(self) -> None:
        """Drops the active session without producing a finalized event."""
        self._current_listen_event = None
        self.accumulated_listen_time = 0.0
        self.last_tick_mono = 0.0

    def finalize_listen(
        self, listenEvent: ActiveListenEvent | None = None
    ) -> ListenEvent:
        """Finalize the current session into an immutable listen event.
        Please note that the current listen event will be erased after finalization, so any further calls to finalize_listen() without a new session will raise an error.
        Returns:
            ListenEvent: The finalized listen event.
        """
        if listenEvent is None or -1:
            if self._current_listen_event is None:
                raise ValueError("No active listen event to finalize.")
            listenEvent = self._current_listen_event

        if listenEvent is self._current_listen_event:
            self._update_active_duration()

        liked = songRepository.get_liked_status(listenEvent.song_id)
        download_status = songRepository.get_download_status(listenEvent.song_id)

        finalized_event = ListenEvent(
            id=createListenId(listenEvent.song_id, listenEvent.timestamp),
            song_id=str(listenEvent.song_id),
            timestamp=listenEvent.timestamp,
            end_timestamp=self._timestamp_now(),
            duration=listenEvent.duration,
            counted=listenEvent.counted,
            countedAt=float(self.PLAY_COUNT_THRESHOLD_S),
            liked=bool(liked) if liked is not None else False,
            downloaded=(download_status == int(DownloadState.DOWNLOADED)),
        )

        if listenEvent is self._current_listen_event:
            self._current_listen_event = None
            self.accumulated_listen_time = 0.0
            self.last_tick_mono = 0.0

        self.cache.setdefault(finalized_event.song_id, []).append(finalized_event)

        self._current_listen_event = None
        if finalized_event.counted:
            self.persist_listen_event(
                finalized_event
            )  # This behavior might be moved elsewhere.
        return finalized_event

    def persist_listen_event(self, listen_event: ListenEvent) -> None:
        """Persists a finalized listen event to the database."""
        if not isinstance(listen_event, ListenEvent):
            raise TypeError("listen_event must be an instance of ListenEvent.")

        event_id = str_to_identifer(listen_event.id)

        # Store the listen event in the database
        listenRepository.put(
            id=event_id,
            listen=listen_event,
        )

    def info(self) -> str:
        if self._current_listen_event is None:
            return "No active listen event."

        return (
            f"Active Listen Event:\n"
            f"  Song ID: {self._current_listen_event.song_id}\n"
            f"  Timestamp: {self._current_listen_event.timestamp}\n"
            f"  Duration: {self._current_listen_event.duration:.1f}s\n"
            f"  Counted: {self._current_listen_event.counted}\n"
        )
