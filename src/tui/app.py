"""Main TUI application container."""
import urwid
from src.tui.widgets.now_playing import NowPlayingBar
from src.tui.widgets.tab_bar import TabBar
from src.tui.widgets.status_bar import StatusBar
from src.tui.screens.queue_screen import QueueScreen
from src.tui.screens.search_screen import SearchScreen
from src.tui.screens.base_screen import ScreenManager
from src.tui.theme import TUI_PALETTE


class ClarityTUI:
    """Main TUI application."""
    
    def __init__(self, backend, interactions):
        self.backend = backend
        self.interactions = interactions
        self.palette = TUI_PALETTE
        
        # Create screen manager
        self.screen_manager = ScreenManager(self)
        
        # Register screens
        self.screen_manager.register_screen('queue', QueueScreen(self))
        self.screen_manager.register_screen('search', SearchScreen(self))
        
        # Start with queue screen
        self.screen_manager.switch_to('queue')
        
        # Create widgets
        self.now_playing = NowPlayingBar(interactions)
        self.tab_bar = TabBar(self.screen_manager)
        self.status_bar = StatusBar()
        
        # Layout with tabs
        header = urwid.Pile([
            self.now_playing,
            self.tab_bar,
        ])
        
        # Body comes from screen manager
        self.root_widget = urwid.Frame(
            body=self.screen_manager.get_current().get_widget(),
            header=header,
            footer=self.status_bar
        )
    
    def handle_input(self, key):
        """Global unhandled input handler."""
        # Let current screen handle first
        current_screen = self.screen_manager.get_current()
        if current_screen and current_screen.handle_input(key):
            return True
        
        # Tab switching
        if key == 'tab':
            self._cycle_tabs()
            return True
        elif key == '1':
            self.screen_manager.switch_to('queue')
            return True
        elif key == '2':
            self.screen_manager.switch_to('search')
            return True
        elif key == '/':  # Quick search
            self.screen_manager.switch_to('search')
            return True
        
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
        
        return False
    
    def _cycle_tabs(self):
        """Switch to next tab."""
        tabs = ['queue', 'search']
        current = self.screen_manager.current_screen_name
        try:
            idx = tabs.index(current)
            next_idx = (idx + 1) % len(tabs)
            self.screen_manager.switch_to(tabs[next_idx])
        except ValueError:
            self.screen_manager.switch_to('queue')
    
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
