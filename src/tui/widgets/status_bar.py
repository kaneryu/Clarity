"""Status bar widget showing keybinding hints."""
import urwid


class StatusBar(urwid.WidgetWrap):
    """Bottom status bar with keybinding hints."""
    
    def __init__(self):
        text = urwid.Text([
            ('key', '[Space]'), ' Play/Pause  ',
            ('key', '[N]'), ' Next  ',
            ('key', '[P]'), ' Prev  ',
            ('key', '[Tab]'), ' Switch  ',
            ('key', '[Q]'), ' Quit'
        ])
        
        attr = urwid.AttrMap(text, 'status')
        super().__init__(attr)
    
    def set_help(self, text):
        """Update help text (for context-specific hints)."""
        self._w.original_widget.set_text(text)
