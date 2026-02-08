"""Now playing bar widget showing current song and playback progress."""
import urwid
from PySide6.QtCore import QTimer


class NowPlayingBar(urwid.WidgetWrap):
    """Top bar showing current song and playback status."""
    
    def __init__(self, interactions):
        self.interactions = interactions
        
        # Text widgets
        self.song_text = urwid.Text("")
        self.progress_text = urwid.Text("")
        self.status_text = urwid.Text("", align='right')
        
        # Layout
        top_line = urwid.Columns([
            ('weight', 2, self.song_text),
            ('pack', self.status_text),
        ])
        bottom_line = self.progress_text
        
        pile = urwid.Pile([top_line, bottom_line])
        box = urwid.LineBox(pile, title="Now Playing")
        
        super().__init__(box)
        
        # Connect Qt signals
        self.interactions.songChanged.connect(self._update_song_info)
        self.interactions.playingStatusChanged.connect(self._update_status)
        self.interactions.durationChanged.connect(self._update_duration)
        
        # Timer for progress updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_progress)
        self.timer.start(1000)  # Update every second
        
        # Initial update
        self._update_song_info()
        self._update_status()
    
    def _update_song_info(self):
        """Update song title and artist."""
        title = self.interactions.currentSongTitle or "No song playing"
        artist = self.interactions.currentSongChannel or ""
        
        if artist:
            text = f"♪ {title} - {artist}"
        else:
            text = f"♪ {title}"
        
        self.song_text.set_text(text)
        self._update_progress()
    
    def _update_status(self):
        """Update playing status icon."""
        from src.misc.enumerations.Song import PlayingStatus
        status = self.interactions.playingStatus
        
        if status == PlayingStatus.Playing.value:
            icon = "▶ Playing"
        elif status == PlayingStatus.Paused.value:
            icon = "⏸ Paused"
        else:
            icon = "⏹ Stopped"
        
        # Volume control not implemented yet, so we'll just show status
        self.status_text.set_text(icon)
    
    def _update_duration(self):
        """Update duration display."""
        self._update_progress()
    
    def _update_progress(self):
        """Update progress bar and time."""
        current = self.interactions.currentSongTime
        duration = self.interactions.currentSongDuration
        
        if duration > 0:
            percentage = current / duration
            bar_width = 40
            filled = int(bar_width * percentage)
            bar = "█" * filled + "░" * (bar_width - filled)
            time_str = f"[{self._format_time(current)} / {self._format_time(duration)}]"
            self.progress_text.set_text(f"[{bar}] {time_str}")
        else:
            self.progress_text.set_text("")
    
    @staticmethod
    def _format_time(seconds):
        """Format seconds as MM:SS."""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
