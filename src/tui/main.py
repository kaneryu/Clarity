"""TUI entry point - initializes Qt application and urwid interface."""
from PySide6.QtCore import QCoreApplication
import sys
import urwid
from src import universal
from src.app import Backend, Interactions
from src.tui.app import ClarityTUI
from src.tui.qt_event_loop import QtUrwidEventLoop
from src.misc import cleanup


def main():
    """Initialize and run the TUI application."""
    # Create Qt application (no GUI)
    app = QCoreApplication(sys.argv)
    app.setApplicationName("Clarity TUI")
    
    # Initialize backend objects (same as GUI)
    backend = Backend.Backend()
    interactions = Interactions.Interactions()
    
    # Create TUI application
    tui_app = ClarityTUI(backend, interactions)
    
    # Create urwid main loop with Qt integration
    event_loop = QtUrwidEventLoop(app)
    loop = urwid.MainLoop(
        tui_app.root_widget,
        palette=tui_app.palette,
        event_loop=event_loop,
        unhandled_input=tui_app.handle_input
    )
    
    # Connect cleanup
    def quit_handler():
        loop.stop()
        cleanup.runCleanup()
    app.aboutToQuit.connect(quit_handler)
    
    # Start event loop
    try:
        loop.run()
    except KeyboardInterrupt:
        app.quit()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
