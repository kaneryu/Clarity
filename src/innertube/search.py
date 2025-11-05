"""
Search.
"""

import ytmusicapi
from src.misc.enumerations.Search import SearchFilters
import json
from typing import Union
import asyncio
import src.universal as universal
import logging
import traceback

from PySide6.QtCore import (
    QObject,
    Signal,
    QAbstractListModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    Property,
    QMetaObject,
    QMetaMethod,
)


class BasicSearchResultsModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        # data structure
        # dictionary
        # types: song, video, album, artist, playlist, podcast, episode
        # title: title
        # creator: creator
        # id: id
        # parentId: id of the parent (for songs its the album id, for albums its the artist id, for playlists its the creator id, for podcasts its the creator id, for episodes its the podcast id, for videos its the creator id)
        # duration: duration (for albums, playists its the number of songs, for podcasts, videos, episodes, songs its the duration)

        self._data = [
            {
                "type": "",
                "title": "",
                "creator": "",
                "id": "",
                "parentId": "",
                "duration": "",
                "object": None,
            }
        ]
        # self.dataChanged.connect(self.log)

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return 6

    def index(self, row: int, column: int = 0, parent=QModelIndex()) -> QModelIndex:
        return self.createIndex(row, column)

    # def parent(self, index: QModelIndex) -> QModelIndex:
    #     return QModelIndex()

    def roleNames(self):
        return {
            Qt.ItemDataRole.DisplayRole: b"title",
            Qt.ItemDataRole.UserRole + 1: b"type",
            Qt.ItemDataRole.UserRole + 2: b"creator",
            Qt.ItemDataRole.UserRole + 3: b"ytid",
            Qt.ItemDataRole.UserRole + 4: b"duration",
            Qt.ItemDataRole.UserRole + 6: b"parentId",
            Qt.ItemDataRole.UserRole + 7: b"object",
        }

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if not index.isValid():
            return None
        if index.row() >= len(self._data):
            return None
        data = self._data[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return data["title"]
        if role == Qt.ItemDataRole.UserRole + 1:
            return data["type"]
        if role == Qt.ItemDataRole.UserRole + 2:
            return data["creator"]
        if role == Qt.ItemDataRole.UserRole + 3:
            return data["id"]
        if role == Qt.ItemDataRole.UserRole + 4:
            return data["duration"]
        if role == Qt.ItemDataRole.UserRole + 6:
            return data["parentId"]
        if role == Qt.ItemDataRole.UserRole + 7:
            print(data["object"])
            return data["object"]
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if section == 0:
                return "Type"
            if section == 1:
                return "Title"
            if section == 2:
                return "Creator"
            if section == 3:
                return "ID"
            if section == 4:
                return "Duration"
            if section == 5:
                return "parentID"
        return None

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if not index.isValid():
            return False
        if index.row() >= len(self._data):
            return False
        if role == Qt.ItemDataRole.UserRole + 1:
            self._data[index.row()]["type"] = value
        if role == Qt.ItemDataRole.DisplayRole:
            self._data[index.row()]["title"] = value
        if role == Qt.ItemDataRole.UserRole + 2:
            self._data[index.row()]["creator"] = value
        if role == Qt.ItemDataRole.UserRole + 3:
            self._data[index.row()]["id"] = value
        if role == Qt.ItemDataRole.UserRole + 4:
            self._data[index.row()]["duration"] = value
        if role == Qt.ItemDataRole.UserRole + 6:
            self._data[index.row()]["parentId"] = value
        if role == Qt.ItemDataRole.UserRole + 7:
            self._data[index.row()]["object"] = value
        self.dataChanged.emit(index, index)
        return True

    def insertRow(
        self, row: int, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ):
        self.beginInsertRows(parent, row, row)
        self._data.insert(
            row,
            {
                "type": "",
                "title": "",
                "creator": "",
                "id": "",
                "parentId": "",
                "duration": "",
                "object": None,
            },
        )
        self.endInsertRows()
        return True

    def _newResult(self, data: dict):
        if (
            not list(data.keys()).sort()
            == [
                "title",
                "type",
                "creator",
                "id",
                "duration",
                "parentId",
                "object",
            ].sort()
        ):
            logging.getLogger("SearchModel").error(
                f"Invalid data passed to search model: {data}"
            )
            return
        self.insertRow(len(self._data), QModelIndex())
        self.setData(
            self.index(len(self._data) - 1, 0),
            data["title"],
            Qt.ItemDataRole.DisplayRole,
        )
        self.setData(
            self.index(len(self._data) - 1, 0),
            data["type"],
            Qt.ItemDataRole.UserRole + 1,
        )
        self.setData(
            self.index(len(self._data) - 1, 0),
            data["creator"],
            Qt.ItemDataRole.UserRole + 2,
        )
        self.setData(
            self.index(len(self._data) - 1, 0), data["id"], Qt.ItemDataRole.UserRole + 3
        )
        self.setData(
            self.index(len(self._data) - 1, 0),
            data["duration"],
            Qt.ItemDataRole.UserRole + 4,
        )
        self.setData(
            self.index(len(self._data) - 1, 0),
            data["parentId"],
            Qt.ItemDataRole.UserRole + 6,
        )
        self.setData(
            self.index(len(self._data) - 1, 0),
            data["object"],
            Qt.ItemDataRole.UserRole + 7,
        )

    def resetModel(self):
        self.beginResetModel()
        self._data = []
        self.endResetModel()

    def log(self):
        print(self._data)


class Base:
    def __init__(self, item: dict):
        for key, value in item.items():
            setattr(self, key, value)


class Video(Base):
    def __init__(self, item: dict):
        super().__init__(item)


class Album(Base):
    def __init__(self, item: dict):
        super().__init__(item)


class Artist(Base):
    def __init__(self, item: dict):
        super().__init__(item)


class Playlist(Base):
    def __init__(self, item: dict):
        super().__init__(item)


class Podcast(Base):
    def __init__(self, item: dict):
        super().__init__(item)


class Episode(Base):
    def __init__(self, item: dict):
        super().__init__(item)


# searchResultItem = Union[song.Song, Video, Album, Artist, Playlist, Podcast, Episode]

# def get_search_result_item(item: dict) -> searchResultItem:
#     category = item["category"]
#     if category == "Episodes":
#         return Episode(item)
#     if category == "Podcasts":
#         return Podcast(item)
#     if category == "Songs":
#         item_ = song.Song()
#         item_.from_search_result(item)
#         return item_
#     if category == "Profiles":
#         return Artist(item)
#     if category == "Playlists":
#         return Playlist(item)
#     if category == "Albums":
#         return Album(item)
#     if category == "Videos":
#         return Video(item)


async def search_suggestions(query: str, detailed=True) -> list | dict:
    """Will return the text that shows up while you are typing a search query in youtube music.

    Args:
        query (str): The query to search for.

    Returns:
        list: A list of suggestions.
        detailed: A dictionary of suggestions, with more details.
    """

    return await universal.asyncBgworker.API.get_search_suggestions(
        query, detailed_runs=detailed
    )


async def search(
    query: str,
    filter: SearchFilters | None = None,
    limit: int = 20,
    ignore_spelling: bool = False,
    model: Union[BasicSearchResultsModel, None] = None,
) -> Union[BasicSearchResultsModel, None]:
    """Searches youtube music

    Args:
        query (str): The query to search for.
        filter (str, optional): The filter to use. Defaults to songs, use the SearchFilters enum.
        max_results (int, optional): Maximum results. Defaults to 20.

    Returns:
        searchResult: A class that contains the results.
    """
    API = universal.asyncBgworker.API
    model = BasicSearchResultsModel() if model is None else model

    def parseSong(item: dict):
        try:
            type_ = "song"
            title = item.get("title", "")
            creator = item["artists"][0]["id"] if item.get("artists", None) else ""
            id = item["videoId"] if item.get("videoId", None) else item["browseId"]

            if item.get("album", None) is not None:
                parentId = (
                    item["album"]["id"]
                    if len(item.get("album", [])) > 0
                    else item["artists"][0]["id"] if item.get("artists", None) else ""
                )
            else:
                parentId = ""

            duration = item["duration_seconds"]
            explicit = item["isExplicit"]
            song = universal.createSongMainThread(id)
            universal.asyncBgworker.addJob(song.get_info)
        except KeyError:
            return None
        return {
            "type": type_,
            "title": title,
            "creator": creator,
            "id": id,
            "parentId": parentId,
            "duration": duration,
            "object": universal.song_module.Song(id),
        }

    def parseVideo(item: dict):
        pass

    def parseAlbum(item: dict):
        type_ = "album"
        title = item["title"]
        creator = item["artists"][0]["id"]
        id = item["browseId"]
        parentId = item["artists"][0]["id"]
        duration = ""
        thumbnail = item["thumbnails"][0]["url"]
        explicit = ""
        album = universal.album_module.Album(item["browseId"])
        return {
            "type": type_,
            "title": title,
            "creator": creator,
            "id": id,
            "parentId": parentId,
            "thumbnail": thumbnail,
            "duration": duration,
            "object": album,
        }

    if model.rowCount(QModelIndex()) > 0:
        model.resetModel()

    # print(json.dumps(s))
    try:
        search_ = await API.search(
            query, filter=filter, limit=limit, ignore_spelling=ignore_spelling
        )
        if search_ == []:
            logging.getLogger("SearchLogger").info(
                f"No results found for {query}", {"notifying": True}
            )
            return model
        for result in search_:
            if result["resultType"] is None:
                continue  # TEMPORARY BEHAVIOR
            else:
                resultType = result["resultType"].lower()
            if resultType == "song":
                p = parseSong(result)
                if p == None:
                    continue
                model._newResult(p)
            if resultType == "album":
                p = parseAlbum(result)
                if p == None:
                    continue
                model._newResult(p)
        if model.rowCount(QModelIndex()) == 0 or model._data == []:
            logging.getLogger("SearchLogger").info(
                f"No results found for {query}", {"notifying": True}
            )
            return model
    except Exception as e:
        logging.getLogger("SearchLogger").error(
            f"Failed searching for {query}, Error: " + str(e)
        )
        traceback.print_exc()
        return None
        # print("\n\n\n")
    return model
