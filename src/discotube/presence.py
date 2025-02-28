import time
import logging
import traceback
import queue

from PySide6.QtCore import QThread
from pypresence import Presence, ActivityType

class PresenceManagerThread(QThread):
    def __init__(self, client_id, queue_instance, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.queue_instance = queue_instance
        self._running = True
        self.jobs = queue.Queue()
        
        self.queue_instance.songChanged.connect(self.putnewsong)
        self.queue_instance.playingStatusChanged.connect(self.playingStatusChanged)
        
        self.logger = logging.getLogger("DiscordPresence")
    
    def putnewsong(self):
        self.jobs.put(self.onNewSong)
    
    
    def playingStatusChanged(self):
        self.jobs.put(self.onPlayingStatusChanged)
    
    def run(self):
        self.rpc = Presence(self.client_id)
        try:
            self.rpc.connect()
            self.logger.info("Discord RPC connected")
        except Exception as e:
            self.logger.error(f"Failed to connect to Discord: {e}")
            return
        
        # Run an update once if a song is playing
        if self.queue_instance.isPlaying and self.queue_instance.currentSongObject:
            self.onNewSong()
        
        while self._running:
            time.sleep(1/60)  # Run at ~60Hz
            try:
                while True:
                    job = self.jobs.get_nowait()
                    try:
                        job()
                    except Exception as je:
                        self.logger.error(f"Error in presence job: {je}")
                        traceback.print_exc()
                    self.jobs.task_done()
            except queue.Empty:
                pass
        
        # Shutdown RPC connection when stopping
        try:
            self.rpc.close()
            self.logger.info("Discord RPC connection closed")
        except Exception as e:
            self.logger.error(f"Error closing Discord RPC: {e}")
    
    def onNewSong(self):
        if not hasattr(self, 'rpc') or not self.queue_instance.currentSongObject:
            return
        try:
            title = self.queue_instance.currentSongTitle
            channel = self.queue_instance.currentSongChannel
            song_time = self.queue_instance.currentSongTime
            duration = self.queue_instance.currentSongDuration
            song_id = self.queue_instance.currentSongId
            cover = self.queue_instance.currentSongObject.largestThumbnailUrl
            
            buttons = [
                {"label": "Listen on YouTube", "url": f"https://www.youtube.com/watch?v={song_id}"}
            ]
            
            current_time = int(time.time())
            start = current_time - song_time if song_time else current_time
            end = start + duration if duration else None
            
            self.rpc.update(
                activity_type=ActivityType.LISTENING,
                details=title[:128] if title else "Unknown Title",
                state=channel[:128] if channel else "Unknown Artist",
                start=start,
                end=end,
                large_image=cover,
                large_text="InnerTune Desktop",
                buttons=buttons
            )
            self.logger.info(f"Updated presence: {title} - {channel}")
        except Exception as e:
            self.logger.error(f"Failed to update presence: {e}")
            traceback.print_exc()
    
    def onPlayingStatusChanged(self):
        if not hasattr(self, 'rpc'):
            return
        if self.queue_instance.isPlaying:
            self.onNewSong()
        else:
            self.clearPresence()
    
    def clearPresence(self):
        if not hasattr(self, 'rpc'):
            return
        try:
            self.rpc.clear()
            self.logger.info("Cleared Discord presence")
        except Exception as e:
            self.logger.error(f"Failed to clear presence: {e}")
            traceback.print_exc()
    
    def stop(self):
        self._running = False
        self.logger.info("Discord presence manager stopped")


def initialize_discord_presence(queue_instance):
    DISCORD_CLIENT_ID = "1221181347071000637"  # Replace with your actual Discord app client ID
    presence_manager = PresenceManagerThread(DISCORD_CLIENT_ID, queue_instance)
    presence_manager.setObjectName("DiscordPresenceManager")
    presence_manager.start()
    return presence_manager