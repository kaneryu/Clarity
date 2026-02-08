"""Queue list widget displaying songs from QueueModel."""
import urwid
from PySide6.QtCore import Qt


class QueueListWidget(urwid.WidgetWrap):
    """Display queue as scrollable list."""
    
    def __init__(self, backend, interactions):
        self.backend = backend
        self.interactions = interactions
        self.queue_model = interactions.queueModel_
        
        # List walker for dynamic content
        self.list_walker = urwid.SimpleFocusListWalker([])
        self.list_box = urwid.ListBox(self.list_walker)
        
        box = urwid.LineBox(self.list_box, title="Queue")
        super().__init__(box)
        
        # Connect Qt signals
        self.queue_model.dataChanged.connect(self._refresh_list)
        self.queue_model.rowsInserted.connect(self._refresh_list)
        self.queue_model.rowsRemoved.connect(self._refresh_list)
        self.queue_model.modelReset.connect(self._refresh_list)
        self.interactions.songChanged.connect(self._update_highlight)
        
        # Initial population
        self._refresh_list()
    
    def _refresh_list(self):
        """Rebuild list from QueueModel."""
        self.list_walker.clear()
        
        count = self.queue_model.rowCount()
        current_index = self._get_current_song_index()
        
        for i in range(count):
            index = self.queue_model.index(i, 0)
            
            # Get data from model (using role names)
            title = self.queue_model.data(index, Qt.ItemDataRole.DisplayRole) or "Unknown"
            artist = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 1) or "Unknown"
            duration = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 2) or 0
            
            # Format line
            is_current = (i == current_index)
            prefix = "►" if is_current else " "
            time_str = self._format_time(duration)
            line = f"{prefix} {i+1:02d}. {title} - {artist}"
            line = line.ljust(60) + f"[{time_str}]"
            
            # Create text widget with appropriate style
            attr = 'queue_current' if is_current else 'queue_item'
            text = urwid.Text((attr, line))
            item = urwid.AttrMap(text, None, focus_map='queue_focus')
            
            self.list_walker.append(item)
        
        # Update title
        title = f"Queue ({count} songs)"
        self._w.set_title(title)
    
    def _update_highlight(self):
        """Update which item is highlighted as current."""
        self._refresh_list()  # Simple approach: full refresh
    
    def _get_current_song_index(self):
        """Get index of currently playing song."""
        try:
            current_id = self.interactions.currentSongId
            if not current_id:
                return -1
            
            # Find in model
            for i in range(self.queue_model.rowCount()):
                index = self.queue_model.index(i, 0)
                song_id = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 4)
                if song_id == current_id:
                    return i
        except Exception:
            pass
        return -1
    
    @staticmethod
    def _format_time(seconds):
        """Format seconds as MM:SS."""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
    
    def keypress(self, size, key):
        """Handle queue-specific keys."""
        # Let list handle navigation (up/down)
        return super().keypress(size, key)
