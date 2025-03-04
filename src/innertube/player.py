import time
import logging
from enum import IntEnum
import vlc

from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker, Property as QProperty, Qt
from PySide6.QtCore import QMetaObject

class PlayingStatus(IntEnum):
    """Playing Status"""
    PLAYING = 0  # Playing
    PAUSED = 1  # Paused
    BUFFERING = 2  # Media is buffering
    STOPPED = 3  # No media is loaded
    ERROR = 4  # Unrecoverable error
    
    NOT_PLAYING = 5  # Only for songproxy class; Returned when the current song is not currently playing

class MediaPlayer(QObject):
    """Handles media playback operations"""
    
    playingStatusChanged = Signal(int)
    durationChanged = Signal()
    mediaFinished = Signal()
    mediaError = Signal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("MediaPlayer")
        
        # Setup VLC
        vlc_args = ["h254-fps=15", "network-caching", "file-caching", "verbose=1", "vv", "log-verbose=3"]
        self.instance = vlc.Instance(vlc_args)
        self.player = self.instance.media_player_new()
        self.eventManager = self.player.event_manager()
        
        self._mutex = QMutex()
        self._playingStatus = PlayingStatus.STOPPED
        self.__bufflastTime = 0
        
        # Setup event handlers
        self.eventManager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_song_finished)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_vlc_error)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPaused, self._on_pause_event)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_play_event)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerBuffering, self._on_buffering_event)
    
    def _on_play_event(self, event):
        self.logger.info("Play Event")
        self._playingStatus = PlayingStatus.PLAYING
        self.playingStatusChanged.emit(self._playingStatus)
    
    def _on_pause_event(self, event):
        self.logger.info("Pause Event")
        self._playingStatus = PlayingStatus.PAUSED
        self.playingStatusChanged.emit(self._playingStatus)
    
    def _on_buffering_event(self, event):
        if time.time() - self.__bufflastTime < 1:
            return
        self.__bufflastTime = time.time()
        self._playingStatus = PlayingStatus.BUFFERING
        self.playingStatusChanged.emit(self._playingStatus)
        
    def _on_song_finished(self, event):
        self.logger.info("Song Finished")
        self.logger.info("Player state: %s", self.player.get_state())
        self.mediaFinished.emit()
    
    def _on_vlc_error(self, event):
        self.logger.error("VLC Error")
        self.logger.error("VLC error event: %s", event)
        self.mediaError.emit()
    
    @QProperty(int, notify=playingStatusChanged)
    def playingStatus(self):
        with QMutexLocker(self._mutex):
            if self.player.get_media() is None:
                return PlayingStatus.STOPPED
            return self._playingStatus
    
    @QProperty(bool, notify=playingStatusChanged)
    def isPlaying(self):
        with QMutexLocker(self._mutex):
            return self._playingStatus == PlayingStatus.PLAYING
    
    @QProperty(int, notify=durationChanged)
    def duration(self):
        try:
            return self.player.get_length() // 1000
        except OSError:
            return 0
    
    @QProperty(int, notify=durationChanged)
    def position(self):
        try:
            if self.player.get_media() is None:
                return 0
            return self.player.get_time() // 1000
        except OSError:
            return 0
    
    @QProperty(int, notify=durationChanged)
    def finishesAt(self):
        return time.time() + self.duration - self.position
    
    def play_media(self, mrl):
        """Plays media from the given MRL (Media Resource Locator)"""
        if self.player.get_state() in [vlc.State.Error, vlc.State.Opening, vlc.State.Buffering]:
            self.logger.warning(f"Player in unstable state {self.player.get_state()}, delaying operation")
            QMetaObject.invokeMethod(self, "play_media", Qt.ConnectionType.QueuedConnection, Qt.Q_ARG(str, mrl))
            return
        
        # Stop previous media with a small delay
        if self.player.get_media() is not None:
            self.player.stop()
            # Wait a bit to let VLC clean up
            time.sleep(0.01)
        
        # Create and play new media
        media = self.instance.media_new(mrl)
        media.add_option("http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Herring/97.1.8280.8")
        media.add_option("http-referrer=https://www.youtube.com/")
        self.player.set_media(media)
        self.player.play()
        self.durationChanged.emit()
    
    def migrate(self, mrl):
        """Switch to a new media source while preserving position"""
        paused = (self.player.is_playing() == 0)
        position = self.player.get_time()
        
        new_media = self.instance.media_new(mrl)
        self.player.pause()
        self.player.set_media(new_media)
        
        if not paused:
            self.player.play()
        else:
            self.player.pause()
            
        self.player.set_time(position)
    
    def pause(self):
        """Pause playback"""
        self.player.pause()
    
    def resume(self):
        """Resume playback"""
        self.player.play()
    
    def stop(self):
        """Stop playback"""
        self.player.stop()
    
    def seek(self, time_seconds):
        """Seek to specific time in seconds"""
        if self.player.get_media() is None:
            raise ValueError("No media loaded")
        self.player.set_time(time_seconds * 1000)
    
    def seek_relative(self, time_seconds_delta):
        """Seek relative to current position (+ or -)"""
        if self.player.get_media() is None:
            raise ValueError("No media loaded")
        new_time = self.player.get_time() + time_seconds_delta * 1000
        self.player.set_time(new_time)
    
    def seek_percent(self, percentage):
        """Seek to percentage of media duration"""
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")
        if self.player.get_media() is None:
            raise ValueError("No media loaded")
        self.player.set_time(self.player.get_length() * percentage // 100)
