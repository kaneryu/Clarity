"""Queue management screen with manipulation capabilities."""
import urwid
from PySide6.QtCore import Qt
from src.tui.screens.base_screen import BaseScreen


class QueueScreen(BaseScreen):
    """Queue management screen."""
    
    def __init__(self, app):
        super().__init__(app)
        
        self.queue_model = app.interactions.queueModel_
        self.list_walker = urwid.SimpleFocusListWalker([])
        self.list_box = urwid.ListBox(self.list_walker)
        
        # Store references for deletion
        self.song_ids = []
        
        box = urwid.LineBox(self.list_box, title="Queue")
        self.widget = box
        
        # Connect signals
        self.queue_model.dataChanged.connect(self._refresh_list)
        self.queue_model.rowsInserted.connect(self._refresh_list)
        self.queue_model.rowsRemoved.connect(self._refresh_list)
        self.queue_model.modelReset.connect(self._refresh_list)
        self.app.interactions.songChanged.connect(self._update_highlight)
        
        self._refresh_list()
    
    def handle_input(self, key):
        """Handle queue-specific keys."""
        if key == 'd':  # Delete focused song
            self._delete_focused_song()
            return True
        elif key == 'D':  # Clear queue
            self._clear_queue()
            return True
        elif key == 'enter':  # Jump to song
            self._jump_to_focused_song()
            return True
        return False
    
    def _delete_focused_song(self):
        """Delete the currently focused song."""
        if len(self.list_walker) == 0:
            return
        focus_pos = self.list_box.focus_position
        if 0 <= focus_pos < len(self.song_ids):
            # Remove from queue via universal.queueInstance
            from src import universal
            universal.queueInstance.remove(focus_pos)
    
    def _clear_queue(self):
        """Clear entire queue with confirmation."""
        if len(self.song_ids) == 0:
            return
        
        # Import here to avoid circular dependency
        from src.tui.widgets.modal import show_modal
        
        def confirm_clear():
            from src import universal
            universal.queueInstance.clear()
        
        def cancel():
            pass
        
        # Get the main loop from app
        # We'll need to pass this through somehow, or store it
        # For now, we'll directly call clear without modal
        # TODO: Add modal support when main loop is accessible
        from src import universal
        universal.queueInstance.clear()
    
    def _jump_to_focused_song(self):
        """Jump playback to focused song."""
        if len(self.list_walker) == 0:
            return
        focus_pos = self.list_box.focus_position
        if 0 <= focus_pos < len(self.song_ids):
            from src import universal
            universal.queueInstance.goto(focus_pos)
    
    def _refresh_list(self):
        """Rebuild list from QueueModel."""
        self.list_walker.clear()
        self.song_ids.clear()
        
        count = self.queue_model.rowCount()
        current_index = self._get_current_song_index()
        
        for i in range(count):
            index = self.queue_model.index(i, 0)
            
            title = self.queue_model.data(index, Qt.ItemDataRole.DisplayRole) or "Unknown"
            artist = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 1) or "Unknown"
            duration = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 2) or 0
            song_id = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 4) or ""
            
            self.song_ids.append(song_id)
            
            is_current = (i == current_index)
            prefix = "►" if is_current else " "
            time_str = self._format_time(duration)
            line = f"{prefix} {i+1:02d}. {title} - {artist}"
            line = line.ljust(60) + f"[{time_str}]"
            
            attr = 'queue_current' if is_current else 'queue_item'
            text = urwid.Text((attr, line))
            item = urwid.AttrMap(text, None, focus_map='queue_focus')
            
            self.list_walker.append(item)
        
        title = f"Queue ({count} songs)"
        self.widget.set_title(title)
    
    def _update_highlight(self):
        """Update highlighted item."""
        self._refresh_list()
    
    def _get_current_song_index(self):
        """Get index of currently playing song."""
        try:
            current_id = self.app.interactions.currentSongId
            if not current_id:
                return -1
            
            for i, song_id in enumerate(self.song_ids):
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
