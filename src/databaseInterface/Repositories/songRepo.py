import functools
from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from src.providerInterface.globalModels import (
    NamespacedIdentifier,
    NamespacedTypedIdentifier,
    SimpleIdentifier,
)

from src.providerInterface.song.models import SongData
from src.databaseInterface.dbcore import DatabaseInterface


def idTypeMustBeSong(func):
    @functools.wraps(func)
    def wrapper(self, id: NamespacedTypedIdentifier, *args, **kwargs):
        if id.type != "song":
            raise ValueError("ID type must be 'song' for this operation.")
        return func(self, id, *args, **kwargs)

    return wrapper


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


class SongRepository:
    def __init__(self, db: DatabaseInterface):
        self.db = db

    @idTypeMustBeSong
    def get(self, id: NamespacedTypedIdentifier) -> Optional[SongRow]:
        """Gets a song from the database, returning the SongRow object, or None

        Args:
            id (NamespacedTypedIdentifier): The ID, must be of type "song". Any namespace.

        Returns:
            Optional[SongRow]: The SongRow object if found, or None if not found.
        """
        query = "SELECT title, album_id, duration, thumbnail_url, material_color, liked, play_count, date_added, last_played, download_status FROM songs WHERE id = ?;"
        results = self.db.query(query, (id.namespacedIdentifier,))
        if results:
            (
                title,
                album_id,
                duration,
                thumbnail_url,
                material_color,
                liked,
                play_count,
                date_added,
                last_played,
                download_status,
            ) = results[0]
            return SongRow(
                id=id.namespacedIdentifier,
                title=title,
                album_id=album_id,
                duration=duration,
                thumbnail_url=thumbnail_url,
                material_color=material_color,
                liked=bool(liked),
                play_count=play_count,
                date_added=date_added,
                last_played=last_played,
                download_status=download_status,
            )
        return None

    @idTypeMustBeSong
    def put(
        self,
        id: NamespacedTypedIdentifier,
        songData: SongData,
        download_status: Optional[int] = None,
    ) -> None:
        """Adds or updates a song in the database with the given SongData.

        Args:
            id (NamespacedTypedIdentifier): The ID, must be of type "song". Any namespace.
            songData (SongData): The SongData to add or update in the database.
            download_status (Optional[int]): The download status of the song. If None,
                preserves the current database value or uses 0 for new rows.

        Returns:
            Always None.
        """

        if songData.title is None:
            raise ValueError("SongData must have a title.")

        title = songData.title
        try:
            album_id = songData.albumId if songData.albumId else None
        except AttributeError:
            album_id = None
        duration = songData.duration if songData.duration else 0
        thumbnail_url = songData.thumbnailUrl if songData.thumbnailUrl else None

        existing_row = self.get(id)
        resolved_download_status = (
            download_status
            if download_status is not None
            else existing_row.download_status if existing_row is not None else 0
        )

        query = """
        INSERT INTO songs (
            id,
            title,
            album_id,
            duration,
            thumbnail_url,
            liked,
            play_count,
            date_added,
            download_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            album_id=excluded.album_id,
            duration=excluded.duration,
            thumbnail_url=excluded.thumbnail_url,
            download_status=excluded.download_status;
        """

        self.db.execute(
            query,
            (
                id.namespacedIdentifier,
                title,
                album_id,
                duration,
                thumbnail_url,
                0,  # liked status
                0,  # play_count
                datetimeNow(),  # date_added
                resolved_download_status,  # download_status
            ),
        )

    @idTypeMustBeSong
    def delete(self, id: NamespacedTypedIdentifier):
        """Deletes a song from the database.

        Args:
            id (NamespacedTypedIdentifier): The ID. Must be of type song, any namespace.
        """
        query = "DELETE FROM songs WHERE id = ?;"
        self.db.execute(query, (id.namespacedIdentifier,))

    @idTypeMustBeSong
    def get_liked_status(self, id: NamespacedTypedIdentifier) -> Optional[bool]:
        """Gets a song's liked status

        Args:
            id (NamespacedTypedIdentifier): The ID. Must be of type song. Any namespace.

        Returns:
            Optional[bool]: Returns a bool, returning None if song doesn't exist.
        """
        query = "SELECT liked FROM songs WHERE id = ?;"
        results = self.db.query(query, (id.namespacedIdentifier,))
        if results:
            return bool(results[0][0])
        return None

    @idTypeMustBeSong
    def set_liked_status(self, id: NamespacedTypedIdentifier, liked_status: bool):
        if not isinstance(liked_status, bool):
            try:
                liked_status = bool(int(liked_status))
            except ValueError:
                raise ValueError("Liked status must be a boolean value.")

        query = "UPDATE songs SET liked = ? WHERE id = ?;"
        self.db.execute(query, (int(liked_status), id.namespacedIdentifier))

    @idTypeMustBeSong
    def get_download_status(self, id: NamespacedTypedIdentifier) -> Optional[int]:
        query = "SELECT download_status FROM songs WHERE id = ?;"
        results = self.db.query(query, (id.namespacedIdentifier,))
        if results:
            return int(results[0][0])
        return None

    @idTypeMustBeSong
    def set_download_status(
        self, id: NamespacedTypedIdentifier, download_status: int
    ) -> None:
        try:
            download_status = int(download_status)
        except (TypeError, ValueError) as exc:
            raise ValueError("Download status must be an integer value.") from exc

        query = "UPDATE songs SET download_status = ? WHERE id = ?;"
        self.db.execute(query, (download_status, id.namespacedIdentifier))

    @idTypeMustBeSong
    def get_material_color(self, id: NamespacedTypedIdentifier) -> Optional[str]:
        """Gets a song's material color

        Args:
            id (NamespacedTypedIdentifier): The ID. Must be of type song. Any namespace.

        Returns:
            Optional[str]: Returns a hex color string, or None if song doesn't exist or has no material color.
        """

        query = "SELECT material_color FROM songs WHERE id = ?;"
        results = self.db.query(query, (id.namespacedIdentifier,))
        if results:
            return results[0][0]
        return None

    @idTypeMustBeSong
    def set_material_color(self, id: NamespacedTypedIdentifier, color: str):
        """Sets a song's material color

        Args:
            id (NamespacedTypedIdentifier): The ID. Must be of type song. Any namespace.
            color (str): The hex color string to set as the material color.

        Returns:
            Always None.
        """
        if not isinstance(color, str):
            raise ValueError("Color must be a string.")

        query = "UPDATE songs SET material_color = ? WHERE id = ?;"
        self.db.execute(query, (color, id.namespacedIdentifier))

    @idTypeMustBeSong
    def get_play_count(self, id: NamespacedTypedIdentifier) -> Optional[int]:
        """Gets a song's play count

        Args:
            id (NamespacedTypedIdentifier): The ID. Must be of type song. Any namespace.

        Returns:
            Optional[int]: Returns the play count as an integer, or None if song doesn't exist.
        """
        query = "SELECT play_count FROM songs WHERE id = ?;"
        results = self.db.query(query, (id.namespacedIdentifier,))
        if results:
            return results[0][0]
        return None

    @idTypeMustBeSong
    def increment_play_count(self, id: NamespacedTypedIdentifier):
        """Increments a song's play count by 1

        Args:
            id (NamespacedTypedIdentifier): The ID. Must be of type song. Any namespace.

        Returns:
            Always None.
        """
        query = "UPDATE songs SET play_count = play_count + 1 WHERE id = ?;"
        self.db.execute(query, (id.namespacedIdentifier,))

    @idTypeMustBeSong
    def set_play_count(self, id: NamespacedTypedIdentifier, play_count: int):
        """Sets a song's play count to a specific value

        Args:
            id (NamespacedTypedIdentifier): The ID. Must be of type song. Any namespace.
            play_count (int): The value to set the play count to.

        Returns:
            Always None.
        """
        if not isinstance(play_count, int) or play_count < 0:
            raise ValueError("Play count must be a non-negative integer.")

        query = "UPDATE songs SET play_count = ? WHERE id = ?;"
        self.db.execute(query, (play_count, id.namespacedIdentifier))

    @idTypeMustBeSong
    def reset_play_count(self, id: NamespacedTypedIdentifier):
        """Resets a song's play count to 0

        Args:
            id (NamespacedTypedIdentifier): The ID. Must be of type song. Any namespace.

        Returns:
            Always None.
        """
        self.set_play_count(id, 0)

    @idTypeMustBeSong
    def update_last_played(self, id: NamespacedTypedIdentifier):
        """Updates a song's last played timestamp to the current time

        Args:
            id (NamespacedTypedIdentifier): The ID. Must be of type song. Any namespace.

        Returns:
            Always None.
        """
        query = "UPDATE songs SET last_played = ? WHERE id = ?;"
        self.db.execute(query, (datetimeNow(), id.namespacedIdentifier))
