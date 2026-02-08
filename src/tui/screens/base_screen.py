"""Base classes for TUI screens and screen management."""
import urwid


class BaseScreen:
    """Base class for TUI screens."""
    
    def __init__(self, app):
        self.app = app
        self.widget = None
    
    def activate(self):
        """Called when screen becomes active."""
        pass
    
    def deactivate(self):
        """Called when screen becomes inactive."""
        pass
    
    def get_widget(self):
        """Return the urwid widget for this screen."""
        return self.widget
    
    def handle_input(self, key):
        """Handle screen-specific input. Return True if handled."""
        return False


class ScreenManager:
    """Manages multiple screens and switching."""
    
    def __init__(self, app):
        self.app = app
        self.screens = {}
        self.current_screen_name = None
        self.current_screen = None
    
    def register_screen(self, name, screen):
        """Register a screen."""
        self.screens[name] = screen
    
    def switch_to(self, name):
        """Switch to named screen."""
        if name not in self.screens:
            return False
        
        if self.current_screen:
            self.current_screen.deactivate()
        
        self.current_screen = self.screens[name]
        self.current_screen_name = name
        self.current_screen.activate()
        
        # Update body widget
        self.app.root_widget.body = self.current_screen.get_widget()
        return True
    
    def get_current(self):
        """Get current screen."""
        return self.current_screen
