"""Main TUI application container."""
import urwid
from src.tui.widgets.now_playing import NowPlayingBar
from src.tui.widgets.queue_list import QueueListWidget
from src.tui.widgets.status_bar import StatusBar
from src.tui.theme import TUI_PALETTE


class ClarityTUI:
    """Main TUI application."""
    
    def __init__(self, backend, interactions):
        self.backend = backend
        self.interactions = interactions
        self.palette = TUI_PALETTE
        
        # Create widgets
        self.now_playing = NowPlayingBar(interactions)
        self.queue_list = QueueListWidget(backend, interactions)
        self.status_bar = StatusBar()
        
        # Layout: [NowPlaying | QueueList | StatusBar]
        self.root_widget = urwid.Frame(
            body=self.queue_list,
            header=self.now_playing,
            footer=self.status_bar
        )
        
        # Track focus for keybinding context
        self.current_screen = "queue"
    
    def handle_input(self, key):
        """Global unhandled input handler."""
        # Global keybindings (work everywhere)
        if key == ' ':  # Space: play/pause
            self._toggle_playback()
            return True
        elif key == 'n':  # Next track
            self.interactions.nextSong()
            return True
        elif key == 'p':  # Previous track
            self.interactions.previousSong()
            return True
        elif key in ('+', '='):  # Volume up
            self._change_volume(+5)
            return True
        elif key == '-':  # Volume down
            self._change_volume(-5)
            return True
        elif key == 'q':  # Quit
            raise urwid.ExitMainLoop()
        
        # Screen-specific keybindings handled by widgets
        return False
    
    def _toggle_playback(self):
        """Toggle play/pause."""
        from src.misc.enumerations.Song import PlayingStatus
        status = self.interactions.currentPlayingStatus
        if status == PlayingStatus.Playing.value:
            self.interactions.pause()
        else:
            self.interactions.play()
    
    def _change_volume(self, delta):
        """Change volume by delta."""
        current = self.interactions.volume
        new_volume = max(0, min(100, current + delta))
        self.interactions.setVolume(new_volume)
