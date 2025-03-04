import logging
from typing import List, Dict, Optional

from PySide6.QtCore import QObject, Signal, Slot, Property as QProperty, Qt
from PySide6.QtCore import QTimer
import requests

from src import universal as g
from src.innertube.player import MediaPlayer, PlayingStatus
from src.innertube.queue_manager import QueueManager, LoopType
from src.innertube.song import Song
import src.discotube.presence as presence

class Queue(QObject):
    """
    Facade that combines QueueManager and MediaPlayer while maintaining
    the original Queue interface
    """
    
    queueChanged = Signal()
    songChanged = Signal()
    pointerMoved = Signal()
    playingStatusChanged = Signal(int)
    durationChanged = Signal()
    
    instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Queue, cls).__new__(cls)
        return cls.instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
            
        super().__init__()
        self.initialized = True
        self.logger = logging.getLogger("Queue")
        
        # Create component objects
        self.player = MediaPlayer()
        self.queueManager = QueueManager()
        
        # Connect component signals
        self.queueManager.queueChanged.connect(self.queueChanged)
        self.queueManager.pointerChanged.connect(self.pointerMoved)
        self.queueManager.currentSongChanged.connect(self.songChanged)
        
        self.player.playingStatusChanged.connect(self.playingStatusChanged)
        self.player.durationChanged.connect(self.durationChanged)
        self.player.mediaFinished.connect(self.songFinished)
        self.player.mediaError.connect(self.handleMediaError)
        
        # Initialize Discord presence
        self.presence = presence.initialize_discord_presence(self)
        
    # Property forwarding
    @QProperty(bool, notify=playingStatusChanged)
    def isPlaying(self):
        return self.player.isPlaying
    
    @QProperty(int, notify=playingStatusChanged)
    def playingStatus(self):
        return self.player.playingStatus
    
    @QProperty(list, notify=queueChanged)
    def queue(self):
        return self.queueManager.queue
    
    @queue.setter
    def queue(self, value):
        self.queueManager.queue = value
        
    @QProperty(list, notify=queueChanged)
    def queueIds(self):
        return self.queueManager.queueIds
    
    @QProperty(str, notify=songChanged)
    def currentSongTitle(self):
        info = self.queueManager.info(self.pointer)
        return info["title"]
    
    @QProperty(str, notify=songChanged)
    def currentSongChannel(self):
        info = self.queueManager.info(self.pointer)
        return info["uploader"]
    
    @QProperty(str, notify=songChanged)
    def currentSongDescription(self):
        info = self.queueManager.info(self.pointer)
        return info["description"]
    
    @QProperty(str, notify=songChanged)
    def currentSongId(self):
        return self.queueManager.currentSongId
    
    @QProperty(QObject, notify=songChanged)
    def currentSongObject(self):
        return self.queueManager.currentSong
    
    @QProperty(int, notify=pointerMoved)
    def pointer(self):
        return self.queueManager.pointer
    
    @pointer.setter
    def pointer(self, value):
        self.queueManager.pointer = value
    
    @QProperty(int, notify=songChanged)
    def currentSongDuration(self):
        return self.player.duration
    
    @QProperty(int, notify=songChanged)
    def currentSongTime(self):
        return self.player.position
    
    @QProperty(int, notify=songChanged)
    def songFinishesAt(self):
        return self.player.finishesAt
    
    @Slot(result=dict)
    def getCurrentInfo(self) -> dict:
        return self.queueManager.info(self.pointer)
    
    @Slot(str, bool)
    def setQueue(self, queue: list, skipSetData: bool = False):
        self.queueManager.setQueue(queue, skipSetData=skipSetData)
    
    def songFinished(self):
        """Handle song finished event"""
        # Move to next song if available
        if self.queueManager.moveNext():
            self.play()
        else:
            self.player.stop()
    
    def handleMediaError(self):
        """Handle media playback error"""
        g.bgworker.add_job(self.refetch)
    
    def refetch(self):
        """Try to refetch the current song after error"""
        song_id = self.currentSongId
        self.queueManager.purgetries[song_id] = self.queueManager.purgetries.get(song_id, 0) + 1
        
        if self.queueManager.purgetries[song_id] > 1:
            self.logger.error("Purge failed")
            self.stop()
            return
        else:
            self.currentSongObject.purge_playback()
            
        self.play()
    
    def checkError(self, url: str):
        """Check if a URL returns an error"""
        r = requests.get(url)
        return r.status_code != 200
    
    @Slot(str)
    def goToSong(self, id: str):
        """Go to a specific song by ID"""
        if id not in self.queueIds:
            self.queueManager.add(id)
            
        self.queueManager.pointer = self.queueIds.index(id)
        self.play()
    
    @Slot()
    def pause(self):
        """Pause playback"""
        self.player.pause()
    
    @Slot()
    def resume(self):
        """Resume playback"""
        self.player.resume()
    
    @Slot()
    def play(self):
        """Play current song"""
        if not self.currentSongObject:
            return
            
        mrl = self.currentSongObject.get_best_playback_MRL()
        self.player.play_media(mrl)
        self.songChanged.emit()
    
    def migrate(self, MRL):
        """Migrate to a new media resource"""
        self.player.migrate(MRL)
    
    @Slot()
    def stop(self):
        """Stop playback"""
        self.player.stop()
    
    @Slot()
    def reload(self):
        """Reload current song"""
        self.play()
    
    @Slot(int)
    def setPointer(self, index: int):
        """Set queue pointer and reload"""
        self.pointer = index
        self.reload()
    
    @Slot()
    def next(self):
        """Go to next song"""
        if self.queueManager.moveNext():
            self.play()
        else:
            self.stop()
    
    @Slot()
    def prev(self):
        """Go to previous song"""
        if self.queueManager.movePrevious():
            self.play()
    
    def add(self, id: str, index: int = -1, goto: bool = False):
        """Add song to queue"""
        self.queueManager.add(id, index, goto)
        if goto:
            self.play()
    
    @Slot(int)
    def seek(self, time: int):
        """Seek to specific time"""
        self.player.seek(time)
    
    @Slot(int)
    def aseek(self, time: int):
        """Seek relative to current position"""
        self.player.seek_relative(time)
    
    @Slot(int)
    def pseek(self, percentage: int):
        """Seek to percentage of song duration"""
        self.player.seek_percent(percentage)
