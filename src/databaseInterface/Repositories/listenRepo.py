import functools
from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from src.providerInterface.song import song

from src.providerInterface.globalModels import (
    NamespacedIdentifier,
    NamespacedTypedIdentifier,
    SimpleIdentifier,
)

from src.databaseInterface.dbcore import DatabaseInterface


def idTypeMustBeListen(func):
    @functools.wraps(func)
    def wrapper(self, id: NamespacedTypedIdentifier, *args, **kwargs):
        if id.type != "listen":
            raise ValueError("ID type must be 'listen' for this operation.")
        return func(self, id, *args, **kwargs)

    return wrapper


# Copy Pasted definiton here to avoid circular imports. Unlike SongRow,
# This dataclass and the one in listenTracker.py should always be kept identical.
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


def datetimeNow():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SongRow:
    id: NamespacedIdentifier
    title: str
    album_id: Optional[str]
    duration: int
    thumbnail_url: Optional[str]
    material_color: Optional[str]
    liked: bool
    play_count: int
    date_added: str
    last_played: Optional[str]
    download_status: int = 0  # 0: not_downloaded, 1: downloading, 2: downloaded


class ListenRepository:
    def __init__(self, db: DatabaseInterface):
        self.db = db

    @idTypeMustBeListen
    def get(self, id: NamespacedTypedIdentifier) -> Optional[ListenEvent]:
        """Gets a listen event from the database, returning the ListenEvent` object, or None

        Args:
            id (NamespacedTypedIdentifier): The ID, must be of type "listen". Any namespace.

        Returns:
            Optional[ListenEvent]: The ListenEvent object if found, or None if not found.
        """
        query = "SELECT song_id, event_id, event_time, event_end_time, event_duration, liked, skipped, completed, downloaded FROM listen_events WHERE event_id = ?;"
        results = self.db.query(query, (id.namespacedIdentifier,))
        if results:
            (
                song_id,
                event_id,
                event_time,
                event_end_time,
                event_duration,
                liked,
                skipped,
                completed,
                downloaded,
            ) = results[0]
            return ListenEvent(
                song_id=song_id,
                id=event_id,
                timestamp=event_time,
                end_timestamp=event_end_time,
                duration=event_duration,
                liked=bool(liked),
                # skipped=bool(skipped), NotImplemented
                # completed=bool(completed),
                downloaded=bool(downloaded),
            )
        return None

    @idTypeMustBeListen
    def put(
        self,
        id: NamespacedTypedIdentifier,
        listen: ListenEvent,
        download_status: Optional[int] = None,
    ) -> None:
        """Adds or updates a song in the database with the given ListenEvent.

        Args:
            id (NamespacedTypedIdentifier): The ID, must be of type "listen". The Id must belong to the 'interactions' namespace.
            listen (ListenEvent): The ListenEvent to add or update in the database.
            download_status (Optional[int]): The download status of the song. If None,
                preserves the current database value or uses 0 for new rows.

        Returns:
            Always None.
        """

        query = """
        INSERT INTO listen_events (
            song_id,
            event_id,
            event_time,
            event_end_time,
            event_duration,
            liked,
            skipped,
            completed,
            downloaded
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            song_id=excluded.song_id,
            event_id=excluded.event_id,
            event_time=excluded.event_time,
            event_end_time=excluded.event_end_time,
            event_duration=excluded.event_duration,
            liked=excluded.liked,
            skipped=excluded.skipped,
            completed=excluded.completed,
            downloaded=excluded.downloaded
        """

        song_id = listen.song_id
        event_id = listen.id
        event_time = listen.timestamp
        event_end_time = listen.end_timestamp
        event_duration = listen.duration
        liked = int(listen.liked)
        skipped = 0  # NotImplemented
        completed = 0  # NotImplemented
        downloaded = int(listen.downloaded)

        self.db.execute(
            query,
            (
                song_id,
                event_id,
                event_time,
                event_end_time,
                event_duration,
                liked,
                skipped,
                completed,
                downloaded,
            ),
        )

    @idTypeMustBeListen
    def delete(self, id: NamespacedTypedIdentifier):
        """Deletes a listen event from the database.

        Args:
            id (NamespacedTypedIdentifier): The ID. Must be of type listen, any namespace.
        """
        query = "DELETE FROM listen_events WHERE event_id = ?;"
        self.db.execute(query, (id.namespacedIdentifier,))
