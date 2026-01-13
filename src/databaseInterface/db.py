import sqlite3 as sq
import time
import os
from typing import Optional

from src.providerInterface.globalModels import (
    NamespacedIdentifier,
    NamespacedTypedIdentifier,
    SimpleIdentifier,
)

from src.providerInterface.song.models.songData import SongData

from src.paths import Paths
from src.misc import compiled


def createDatabaseCursor():
    conn = sq.connect(os.path.join(Paths.ASSETSPATH, "database", "data"))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA cache_size = 10000;")
    return conn.cursor(), conn


def initializeDatabase():
    cursor, conn = createDatabaseCursor()
    if compiled.compiled:
        with open("src/databaseInterface/schema.sql", "r") as f:
            cursor.executescript(f.read())
    else:
        with open(os.path.join(Paths.ASSETSPATH, "database", "schema.sql"), "r") as f:
            cursor.executescript(f.read())
    conn.commit()
    conn.close()


class ConnectionPool:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionPool, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.connections = []
        self.max_connections = 5

    def get_connection(self):
        if self.connections:
            return self.connections.pop()
        else:
            return createDatabaseCursor()[1]

    def return_connection(self, conn):
        if not len(self.connections) >= self.max_connections:
            self.connections.append(conn)


class DatabaseInterface:
    def __init__(self):
        self.pool = ConnectionPool()

    def execute_query(self, query, params=()):
        params = tuple(
            (
                str(i)
                if isinstance(
                    i,
                    (NamespacedIdentifier, NamespacedTypedIdentifier, SimpleIdentifier),
                )
                else i
            )
            for i in params
        )

        conn = self.pool.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.commit()
        self.pool.return_connection(conn)

        return results

    def testQuery(self):
        """Fetch a list of 100 song titles ordered by duration"""
        query = "SELECT title FROM songs ORDER BY duration LIMIT 100;"
        results = self.execute_query(query)
        return [row[0] for row in results]

    ## Song Functions
    def getLikedStatus(self, id: NamespacedTypedIdentifier) -> Optional[bool]:
        if id.type != "song":
            raise ValueError("ID type must be 'song' to get liked status.")

        query = "SELECT liked FROM songs WHERE id = ?;"
        results = self.execute_query(query, (id.namespacedIdentifier,))
        if results:
            return results[0][0]
        return None

    def setLikedStatus(self, id: NamespacedTypedIdentifier, likedStatus: bool):
        if id.type != "song":
            raise ValueError("ID type must be 'song' to set liked status.")

        query = "UPDATE songs SET liked = ? WHERE id = ?;"
        self.execute_query(query, (likedStatus, id.namespacedIdentifier))

    def addSongToLibrary(self, id: NamespacedTypedIdentifier, songData: SongData):
        if id.type != "song":
            raise ValueError("ID type must be 'song' to add to songs table.")

        query = """
        INSERT INTO songs (id, title, album_id, duration, thumbnail_url, liked, play_count, date_added)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """

        id: NamespacedIdentifier = id.namespacedIdentifier

        title = songData.title if songData.title else ""
        album_id = songData.albumId if songData.albumId else ""
        duration = songData.duration if songData.duration else 0
        thumbnail_url = (
            songData.largestThumbnailUrl if songData.largestThumbnailUrl else ""
        )

        liked = 0  # default to not liked
        play_count = 0
        date_added = int(time.time())

        # There should be code to automatically add the artist to the artists table here in the future

        self.execute_query(
            query,
            (
                id,
                title,
                album_id,
                duration,
                thumbnail_url,
                liked,
                play_count,
                date_added,
            ),
        )

    def checkSongInLibrary(self, id: NamespacedTypedIdentifier) -> bool:
        if id.type != "song":
            raise ValueError("ID type must be 'song' to check in songs table.")

        query = "SELECT 1 FROM songs WHERE id = ?;"
        results = self.execute_query(query, (id.namespacedIdentifier,))
        return len(results) > 0

    def saveSongMaterialColor(self, id: NamespacedTypedIdentifier, color: str):
        if id.type != "song":
            raise ValueError("ID type must be 'song' to save material color.")

        query = "UPDATE songs SET material_color = ? WHERE id = ?;"
        self.execute_query(query, (color, id.namespacedIdentifier))

    def getSongMaterialColor(self, id: NamespacedTypedIdentifier) -> Optional[str]:
        if id.type != "song":
            raise ValueError("ID type must be 'song' to get material color.")

        query = "SELECT material_color FROM songs WHERE id = ?;"
        results = self.execute_query(query, (id.namespacedIdentifier,))
        if results:
            return results[0][0]
        return None


if __name__ == "__main__":
    initializeDatabase()
