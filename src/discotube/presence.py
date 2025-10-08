import time
import logging
import traceback
import queue
import typing

if typing.TYPE_CHECKING:
    from src.playback.queuemanager import Queue

from src.misc import cleanup, settings
from src.misc.enumerations.Song import PlayingStatus
from PySide6.QtCore import QThread, Slot
from pypresence import Presence, ActivityType, StatusDisplayType, DiscordNotFound
from workers import bgworker


class PresenceManagerThread(QThread):
    def __init__(self, queue_instance: "Queue", parent=None):
        super().__init__(parent)
        self.queue_instance = queue_instance
        self._running = True
        self.jobs: queue.Queue = queue.Queue()

        self.logger = logging.getLogger("DiscordPresence")
        self.PresenceEnabledSetting = settings.getSetting("discordPresenceEnabled")
        self.PresenceEnabledSetting.valueChanged.connect(self.enabledChanged)
        self.enabled = self.PresenceEnabledSetting.value

        self.clientIdSetting = settings.getSetting("discordClientId")
        self.clientIdSetting.valueChanged.connect(self.clientIdChanged)
        self.client_id = self.clientIdSetting.value

        self.newPresence: Presence | None = None

        self._rate_limit_seconds = 0.5
        self._last_rpc_ts = 0.0
        self._pending_action = False

        self.currentDetails: dict[str, typing.Any] | None = None

    def clientIdChanged(self):
        if self.clientIdSetting.value == self.client_id:
            self.logger.info("Discord client ID has not changed, skipping update.")
            return
        try:
            self.newPresence = Presence(self.clientIdSetting.value)
            self.newPresence.connect()  # Test if the client ID is valid
        except Exception as e:
            self.logger.error(
                f"Invalid Discord client ID: {self.clientIdSetting.value}. Error: {e}"
            )
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
            self.rpc = Presence(self.client_id)
        else:
            self.rpc = self.newPresence
            self.newPresence = None
        try:
            self.rpc.connect()
            self.logger.info("Discord RPC connected")
        except Exception as e:
            self.logger.error(f"Failed to connect to Discord: {e}")
            if isinstance(e, DiscordNotFound):
                bgworker.add_occasional_task(
                    self.occasional_reconnect_try, interval=30
                )  # Try reconnecting every 30 seconds
            return
        # After reconnect, allow immediate update
        self._last_rpc_ts = 0.0

    # def putnewsong(self):
    #     self.jobs.put(self.onNewSong)

    # def playingStatusChanged(self):
    #     self.jobs.put(self.onPlayingStatusChanged)

    def occasional_reconnect_try(self):
        try:
            self.rpc.connect()
            self.logger.info("Reconnected to Discord RPC", {"notifying": True})
            if self.enabled and self.queue_instance.isPlaying:
                self.onNewSong()
            bgworker.remove_occasional_task(self.occasional_reconnect_try)
        except Exception as e:
            self.logger.warning(f"Reconnection to Discord RPC failed: {e}")

    def run(self):
        self.reloadRPC()
        # Run an update once if a song is playing
        if self.queue_instance.isPlaying and self.queue_instance.currentSongObject:
            self.onNewSong()

        while self._running:
            # time.sleep(1/60)  # Run at ~60Hz
            # try:
            #     while True:
            #         job = self.jobs.get_nowait()
            #         try:
            #             job()
            #         except Exception as je:
            #             self.logger.error(f"Error in presence job: {je}")
            #             traceback.print_exc()
            #         self.jobs.task_done()
            # except queue.Empty:
            #     pass
            now = time.time()
            if (now - self._last_rpc_ts) >= self._rate_limit_seconds:
                if (
                    self.queue_instance.playingStatus == PlayingStatus.PLAYING
                    or self.queue_instance.playingStatus
                    == PlayingStatus.BUFFERING_LOCAL
                ):
                    if not self.comparePresenceWithQueue():
                        self.onNewSong()
                elif (
                    self.queue_instance.playingStatus == PlayingStatus.STOPPED
                    or self.queue_instance.playingStatus == PlayingStatus.PAUSED
                    or self.queue_instance.playingStatus == PlayingStatus.BUFFERING
                ):
                    if not self.checkPresenceCleared():
                        self.clearPresence()

        # Shutdown RPC connection when stopping
        try:
            self.rpc.close()
            self.logger.info("Discord RPC connection closed")
        except Exception as e:
            self.logger.error(f"Error closing Discord RPC: {e}")

    def comparePresenceWithQueue(self):
        if not hasattr(self, "rpc") or not self.queue_instance.currentSongObject:
            return False
        title = self.queue_instance.currentSongTitle
        channel = self.queue_instance.currentSongChannel

        if not self.currentDetails:
            return False

        if (
            self.currentDetails["title"] == (title)
            and self.currentDetails["channel"] == (channel)
            and self.currentDetails["state"] == (self.queue_instance.playingStatus.name)
        ):
            return True
        return False

    def checkPresenceCleared(self):
        if not hasattr(self, "rpc"):
            return True
        return self.currentDetails is None

    def onNewSong(self):
        if not self.enabled:
            return
        if not hasattr(self, "rpc") or not self.queue_instance.currentSongObject:
            return
        try:
            now = time.time()
            if (now - self._last_rpc_ts) < self._rate_limit_seconds:
                self.logger.debug(
                    "Presence update throttled; will retry when window opens"
                )
                return

            title: str = self.queue_instance.currentSongTitle  # type: ignore
            channel: str = self.queue_instance.currentSongChannel  # type: ignore
            song_time: int = self.queue_instance.currentSongTime  # type: ignore
            duration: int = self.queue_instance.currentSongDuration  # type: ignore
            song_id: str = self.queue_instance.currentSongId  # type: ignore
            cover: str = self.queue_instance.currentSongObject.largestThumbnailUrl  # type: ignore

            self.currentDetails = {
                "title": title,
                "channel": channel,
                "song_time": song_time,
                "duration": duration,
                "song_id": song_id,
                "cover": cover,
            }
            if isinstance(self.queue_instance.playingStatus, int):
                self.currentDetails["state"] = PlayingStatus(
                    self.queue_instance.playingStatus
                ).name
            else:
                self.currentDetails["state"] = self.queue_instance.playingStatus.name

            buttons = [
                {
                    "label": "Listen on YouTube",
                    "url": f"https://www.youtube.com/watch?v={song_id}",
                }
            ]

            if not self.queue_instance.playingStatus == PlayingStatus.BUFFERING_LOCAL:
                current_time = int(time.time())
                start = current_time - song_time if song_time else current_time
                end = start + duration if duration else None

                self.rpc.update(
                    activity_type=ActivityType.LISTENING,
                    status_display_type=StatusDisplayType.STATE,
                    details=title[:128] if title else "Unknown Title",
                    state=channel[:128] if channel else "Unknown Artist",
                    start=start,
                    end=end,
                    large_image=cover,
                    large_text="Clarity",
                    buttons=buttons,
                )
            else:
                self.rpc.update(
                    activity_type=ActivityType.LISTENING,
                    status_display_type=StatusDisplayType.STATE,
                    details=title[:128] if title else "Unknown Title",
                    state=channel[:128] if channel else "Unknown Artist",
                    large_image=cover,
                    large_text="Clarity (Buffering...)",
                    buttons=buttons,
                )
            self._last_rpc_ts = now
            self.logger.info(f"Updated presence: {title} - {channel}")
        except Exception as e:
            self.logger.error(f"Failed to update presence: {e}")
            traceback.print_exc()

    def onPlayingStatusChanged(self):
        if not hasattr(self, "rpc"):
            return
        if self.queue_instance.isPlaying:
            self.onNewSong()
        else:
            self.clearPresence()

    def clearPresence(self):
        if not hasattr(self, "rpc"):
            return
        try:
            now = time.time()
            if (now - self._last_rpc_ts) < self._rate_limit_seconds:
                self.logger.debug(
                    "Presence update throttled; will retry when window opens"
                )
                return

            self.rpc.clear()
            self.currentDetails = None
            self._last_rpc_ts = now
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
