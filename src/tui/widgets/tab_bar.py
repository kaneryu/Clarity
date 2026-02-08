"""Tab bar widget for screen switching."""
import urwid


class TabBar(urwid.WidgetWrap):
    """Tab bar for screen switching."""
    
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.tabs = [
            ('queue', 'Queue'),
            ('search', 'Search'),
        ]
        
        self.buttons = []
        widgets = []
        
        for name, label in self.tabs:
            btn = urwid.Button(label)
            urwid.connect_signal(btn, 'click', self._on_tab_click, name)
            self.buttons.append((name, btn))
            
            attr = urwid.AttrMap(btn, 'tab', focus_map='tab_focus')
            widgets.append(('pack', attr))
        
        cols = urwid.Columns(widgets)
        super().__init__(cols)
        
        # Initial active state
        self._update_active()
    
    def _on_tab_click(self, name, button):
        """Handle tab click."""
        self.screen_manager.switch_to(name)
        self._update_active()
    
    def _update_active(self):
        """Update visual state of tabs."""
        active = self.screen_manager.current_screen_name
        for name, btn in self.buttons:
            label = [tab[1] for tab in self.tabs if tab[0] == name][0]
            if name == active:
                btn.set_label(f"[{label}]")
            else:
                btn.set_label(label)
