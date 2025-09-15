
import time
from datetime import datetime, timedelta
import json
import asyncio
import io
import enum
import os
import logging
from typing import Union

from PySide6.QtCore import Property as QProperty, Signal, Slot, Qt, QObject, QSize, QBuffer, QRect
from PySide6.QtGui import QPixmap, QPainter, QImage
from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtQuick import QQuickImageProvider

import ytmusicapi as ytm
import yt_dlp as yt_dlp_module # type: ignore[import-untyped]

from src import universal as universal
from src import cacheManager
from src.innertube import song


"""
What do we need albums to do?
Albums are basically just a collection of songs, with some metadata.

We should be able to:
- Get album metadata (title, artist, year, etc.)
- Get album songs (list of song objects)
- Get album art (as QPixmap or QImage)
- Maybe get album duration (total length of all songs)
- Perform bulk operations on albums (e.g., download all songs, add all songs to queue, etc.)

Just like Song, albums should be singletons. There should only be one instance of an album for a given album ID.
"""


class Album:
    pass

def albumFromSong(song: song.Song) -> Album:
    pass