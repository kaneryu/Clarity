import yt_dlp as yt_dlp_module
import vlc

from PySide6.QtCore import QObject, Slot, Signal, Property as QProperty
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex
from PySide6.QtGui import QStandardItem, QStandardItemModel

import io
import enum
import requests

from src import universal as g
from src import cacheManager
import src.innertube.song as song
import time
import asyncio

ydlOpts = {
    "external_downloader_args": ['-loglevel', 'panic'],
    "quiet": False
}

ytdl: yt_dlp_module.YoutubeDL
ytdl = yt_dlp_module.YoutubeDL(ydlOpts)

class LoopType(enum.Enum):
    """Loop Types"""
    NONE = 0 # Halt after playing all songs
    SINGLE = 1 # Repeat the current song
    ALL = 2 # Repeat all songs in the queue
    

class QueueModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self._queueIds = []
        self._queue = []

    def rowCount(self, parent=QModelIndex()):
        print("asked for rowCount")
        return len(self._queue)

    def count(self):
        return len(self._queue)
    
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and index.isValid():
            print("returning data at", index.row())
            print("data:", self._queue[index.row()])
            return self._queue[index.row()]
        return None

    def roleNames(self):
        return {
            Qt.DisplayRole: b"song"
        }
    
    def headerData(self, section, orientation, role = ...):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return "Song"
            else:
                return f"Song {section}"
        return None
    
    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole and index.isValid():
            self._queue[index.row()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def setQueue(self, queue):
        self.beginResetModel()
        self._queue = queue
        self.endResetModel()

    def removeItem(self, index):
        if 0 <= index < len(self._queue):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self._queue[index]
            self.endRemoveRows()

    def moveItem(self, from_index, to_index):
        if 0 <= from_index < len(self._queue) and 0 <= to_index < len(self._queue):
            self.beginMoveRows(QModelIndex(), from_index, from_index, QModelIndex(), to_index)
            self._queue.insert(to_index, self._queue.pop(from_index))
            self.endMoveRows()
            
class Queue(QObject):
    """Combined Queue and Player"""

    queueChanged = Signal()
    songChanged = Signal()
    pointerMoved = Signal()
    playingStatusChanged = Signal()
    
    instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Queue, cls).__new__(cls, *args, **kwargs)
        return cls.instance
        
    def __init__(self):
        super().__init__()
        

        self._pointer = 0
        self.player: vlc.MediaPlayer = vlc.MediaPlayer()
        self.eventManager = self.player.event_manager()
        
        self.instance: vlc.Instance = self.player.get_instance()
        
        self.player.set_hwnd(0)
        self.loop: LoopType = LoopType.NONE
        self.queueModel = QueueModel()
        
        if not cacheManager.cacheExists("queueCache"):
            cache = cacheManager.CacheManager(name="queueCache")
        else:
            cache = cacheManager.getCache("queueCache")
        
        self.cache = cache
        self.queue: list[song.Song]
        self.pointer: int
        
        self.songChanged.connect(self.playingStatusChanged)
        self.playingStatusChanged.connect(lambda: print("Playing Status Changed"))

    @QProperty(list, notify=queueChanged)
    def queue(self):
        return self.queueModel._queue
    
    @QProperty(list, notify=queueChanged)
    def queueIds(self):
        return self.queueModel._queueIds
    
    @queue.setter
    def queue(self, value):
        self.queueChanged.emit()
        self.setQueue(value, skipSetData = True)
        
    @QProperty(str, notify=songChanged)
    def currentSongTitle(self):
        return self.info(self.pointer)["title"]

    @QProperty(str, notify=songChanged)
    def currentSongChannel(self):
        return self.info(self.pointer)["uploader"]
    
    @QProperty(str, notify=songChanged)
    def currentSongDescription(self):
        return self.info(self.pointer)["description"]
    
    @QProperty(str, notify=songChanged)
    def currentSongId(self):
        return self.queueIds[self.pointer]
    
    @QProperty(int, notify=pointerMoved)
    def pointer(self):
        return self._pointer
        
    @pointer.setter
    def pointer(self, value):
        if value == -1:
            self._pointer = len(self.queue) - 1 # special case for setting pointer to last song
        if value < 0 or value >= len(self.queue):
            raise ValueError("Pointer must be between 0 and length of queue")
        
        self.pointerMoved.emit()
        self._pointer = value
        
    @QProperty(int, notify=songChanged)
    def currentSongDuration(self):
        return self.player.get_length() // 1000
    
    @QProperty(int, notify=songChanged)
    def currentSongTime(self):
        return self.player.get_time() // 1000
    
    @QProperty(int, notify=songChanged)
    def songFinishesAt(self):
        return time.time() + self.currentSongDuration - self.currentSongTime # current time + time left

    @QProperty(bool, notify=playingStatusChanged)
    def isPlaying(self):
        return self.player.is_playing() == 1

        
    def checkError(self, url: str):
        r = requests.get(url)
        if r.status_code == 200:
            return False
        else:
            return True

    @Slot(result=dict)
    def getCurrentInfo(self) -> dict:
        return self.info(self.pointer)
    
    @Slot(str, bool)
    def setQueue(self, queue: list, skipSetData: bool = False):
        for i in queue:
            print("Adding", i)
            self.add(i)

    def songFinished(self, event):
        print("Song Finished")
        print(self.player.get_state())
        if self.loop == LoopType.SINGLE:
            self.play()
        elif self.loop == LoopType.ALL or self.loop == LoopType.NONE:
            self.next()
        else:
            print("LoopType Invalid")
            print("Treating as LoopType.NONE")
            self.next()
        self.songChanged.emit()
    
    def on_vlc_error(self, event):
        print("VLC Error")
        print(event)
        
    
    @Slot(str)
    def goToSong(self, id: str):
        if not id in self.queue:
            self.add(id)
        
        self.pointer = self.queueIds.index(id)
        self.play()
    
    @Slot()
    def pause(self):
        self.player.pause()
        self.playingStatusChanged.emit()
       
    @Slot()
    def resume(self):
        self.player.play()
        self.playingStatusChanged.emit()
        
         
    @Slot()
    def play(self):
        def Media(url):
            media: vlc.Media = self.instance.media_new(url)
            media.add_option("http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Herring/97.1.8280.8")
            media.add_option("http-referrer=https://www.youtube.com/")
            media.add_option("http-cookie=CONSENT=YES+cb.20210328-17-p0.en+FX+410")
            return media

        self.songChanged.emit()
        url = self.queue[self.pointer].playbackInfo["audio"][0]["url"]
        self.player.set_media(Media(url))
        self.player.play()
    
    @Slot()
    def stop(self):
        self.player.stop()
    
    @Slot()
    def reload(self):
        self.play()
    
    @Slot(int)
    def setPointer(self, index: int):
        self.pointer = index
        self.reload()
    
    @Slot()
    def next(self):
        print("Next")
        print("Pointer: " + str(self.pointer), "Length: " + str(len(self.queue)))
        if self.pointer == len(self.queue) - 1:
            print("Queue Finished")
            if self.loop == LoopType.SINGLE:
                self.play() # pointer doesn't change, song doesn't change
                return
            elif self.loop == LoopType.ALL:
                self.pointer = 0
                self.play()
                return
            else:
                print("Queue Exhaused")
                self.stop()
                return
        
        self.pointer += 1
        self.play()
    
    @Slot()
    def prev(self):
        self.pointer = self.pointer - 1 if self.pointer > 0 else 0
        self.play()
    
    def info(self, pointer: int):
        if len(self.queue) == 0:
            return {
                "title": "No Songs",
                "uploader": "No Songs",
                "description": "No Songs"
            }

        song_ = self.queue[pointer]
        
        return {
            "title": song_.title,
            "uploader": song_.artist,
            "description": song_.description
        }
    
    def add(self, id: str, index: int = -1):
        s = song.Song(id = id, cache = cacheManager)
        coro = s.get_info(g.asyncBgworker.API)
        future = asyncio.run_coroutine_threadsafe(coro, g.asyncBgworker.event_loop)
        future.result() # wait for the result
        s.get_playback()
        
        self.queue.append(s)
        self.queueIds.append(id)
        
    
    def _seek(self, time: int):
        if time < 0 or time > self.player.get_length() / 1000:
            raise ValueError("Time must be between 0 and video length")
        
        if not self.player.get_media() == None:
            self.player.set_time(time * 1000)
        else:
            raise ValueError("No Media Loaded")
    
    @Slot(int)
    def seek(self, time: int):
        self.player.set_time(time * 1000)
    
    @Slot(int)
    def aseek(self, time: int):
        self.player.set_time(self.player.get_time() + time * 1000)
    
    @Slot(int)
    def pseek(self, percentage: int):
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")
        len = self.player.get_length()
        self.player.set_time(len * percentage // 100)

