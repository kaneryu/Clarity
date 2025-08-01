import time
import logging
import traceback
import queue

from src.misc import cleanup, settings
from PySide6.QtCore import QThread, Slot
from pypresence import Presence, ActivityType, StatusDisplayType

class PresenceManagerThread(QThread):
    def __init__(self, queue_instance, parent=None):
        super().__init__(parent)
        self.queue_instance = queue_instance
        self._running = True
        self.jobs: queue.Queue = queue.Queue()
        self.queue_instance.songChanged.connect(self.putnewsong)
        self.queue_instance.playingStatusChanged.connect(self.playingStatusChanged)
        
        
        self.logger = logging.getLogger("DiscordPresence")
        self.PresenceEnabledSetting = settings.getSetting("discordPresenceEnabled")
        self.PresenceEnabledSetting.valueChanged.connect(self.enabledChanged)
        self.enabled = self.PresenceEnabledSetting.value
        
        self.clientIdSetting = settings.getSetting("discordClientId")
        self.clientIdSetting.valueChanged.connect(self.clientIdChanged)
        self.client_id = self.clientIdSetting.value
        
        self.newPresence: Presence | None = None
    
    
    def clientIdChanged(self):
        if self.clientIdSetting.value == self.client_id:
            self.logger.info("Discord client ID has not changed, skipping update.")
            return
        try:
            self.newPresence = Presence(self.clientIdSetting.value)
            self.newPresence.connect() # Test if the client ID is valid
        except Exception as e:
            self.logger.error(f"Invalid Discord client ID: {self.clientIdSetting.value}. Error: {e}")
            self.clientIdSetting.setValue(self.client_id)
            return
        self.client_id = self.clientIdSetting.value
        self.logger.info(f"Discord client ID changed to: {self.client_id}")

        self.jobs.put(self.reloadRPC)

        
    def restart(self):
        self.stop()
        self.wait()
        self.start()
        
    @Slot()
    def enabledChanged(self):
        self.enabled = self.PresenceEnabledSetting.value
        self.logger.info(f"Discord presence enabled changed: {self.enabled}")
        
        if self.enabled:
            self.enable()
        else:
            self.disable()
    
    def reloadRPC(self):
        if not self.newPresence:
            self.logger.info("Reload RPC called without newPresence set, creating new one.")
            self.newPresence = Presence(self.client_id)
            self.newPresence.connect()
        self.rpc = self.newPresence
        self.playingStatusChanged()
        self.logger.info("Discord RPC reloaded with new client ID")
    
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
        if not self.enabled:
            return
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
                status_display_type=StatusDisplayType.DETAILS,
                details=title[:128] if title else "Unknown Title",
                state=channel[:128] if channel else "Unknown Artist",
                start=start,
                end=end,
                large_image=cover,
                large_text="Clarity",
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
    
    def disable(self):
        self.clearPresence()
        self.logger.info("Discord presence disabled")
    
    def enable(self):
        self.logger.info("Discord presence enabled")
        self.onPlayingStatusChanged()
    
    def stop(self):
        self._running = False
        self.logger.info("Discord presence manager stopped")

presence_manager: PresenceManagerThread | None = None
def initialize_discord_presence(queue_instance):
    global presence_manager
    presence_manager = PresenceManagerThread(queue_instance)
    presence_manager.setObjectName("DiscordPresenceManager")
    presence_manager.start()
    cleanup.addCleanup(stop_discord_presence)
    return presence_manager

def stop_discord_presence():
    global presence_manager
    if presence_manager and presence_manager.isRunning():
        presence_manager.stop()
        presence_manager.wait()
        presence_manager = None
        logging.getLogger("DiscordPresence").info("Discord presence stopped")