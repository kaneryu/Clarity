"""Search screen for finding and adding songs."""
import urwid
from PySide6.QtCore import Qt, QTimer
from src.tui.screens.base_screen import BaseScreen


class SearchScreen(BaseScreen):
    """Search for songs."""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Search input
        self.search_edit = urwid.Edit("Query: ")
        urwid.connect_signal(self.search_edit, 'change', self._on_search_change)
        
        # Results list
        self.results_walker = urwid.SimpleFocusListWalker([])
        self.results_list = urwid.ListBox(self.results_walker)
        
        # Layout
        pile = urwid.Pile([
            ('pack', urwid.AttrMap(self.search_edit, 'search_input')),
            urwid.Divider(),
            ('pack', urwid.Text("Results:")),
            self.results_list,
        ])
        
        box = urwid.LineBox(pile, title="Search")
        self.widget = box
        
        # Search model from backend
        self.search_model = app.backend.searchModel
        self.search_model.dataChanged.connect(self._refresh_results)
        self.search_model.rowsInserted.connect(self._refresh_results)
        self.search_model.modelReset.connect(self._refresh_results)
        
        # Debounce timer for search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self.result_ids = []
        self.result_types = []
    
    def activate(self):
        """Focus search input when screen activates."""
        # Set focus to search edit
        pass
    
    def handle_input(self, key):
        """Handle search-specific keys."""
        if key == 'enter':
            # Check if we're in the results list
            if self.widget.original_widget.focus_position == 3:  # Results list
                self._add_focused_to_queue()
                return True
        return False
    
    def _on_search_change(self, edit, new_text):
        """Handle search input change (debounced)."""
        self.search_timer.stop()
        self.search_timer.start(500)  # 500ms debounce
    
    def _perform_search(self):
        """Execute search via backend."""
        query = self.search_edit.get_edit_text()
        if query.strip():
            self.app.backend.search(query)
    
    def _refresh_results(self):
        """Refresh results list from search model."""
        self.results_walker.clear()
        self.result_ids.clear()
        self.result_types.clear()
        
        count = self.search_model.rowCount()
        
        for i in range(count):
            index = self.search_model.index(i, 0)
            
            # Get search result data
            title = self.search_model.data(index, Qt.ItemDataRole.DisplayRole) or "Unknown"
            artist = self.search_model.data(index, Qt.ItemDataRole.UserRole + 1) or "Unknown"
            result_id = self.search_model.data(index, Qt.ItemDataRole.UserRole + 4) or ""
            result_type = self.search_model.data(index, Qt.ItemDataRole.UserRole + 5) or "song"
            
            self.result_ids.append(result_id)
            self.result_types.append(result_type)
            
            # Format type icon
            type_icon = "♪" if result_type == "song" else "🎵"
            line = f"  {i+1}. {type_icon} {title} - {artist}"
            
            text = urwid.Text(line)
            item = urwid.AttrMap(text, 'search_result', focus_map='search_focus')
            
            self.results_walker.append(item)
    
    def _add_focused_to_queue(self, and_play=False):
        """Add focused result to queue."""
        if len(self.results_walker) == 0:
            return
        focus_pos = self.results_list.focus_position
        if 0 <= focus_pos < len(self.result_ids):
            song_id = self.result_ids[focus_pos]
            
            # Add to queue via universal
            from src import universal
            universal.queueInstance.add(song_id, goto=and_play)
            
            # Show feedback via logging
            import logging
            logging.getLogger("TUI").info(f"Added {song_id} to queue")
