"""Qt + urwid event loop integration."""
import urwid
from PySide6.QtCore import QCoreApplication, QTimer, QEventLoop


class QtUrwidEventLoop(urwid.SelectEventLoop):
    """
    Custom event loop that processes both urwid and Qt events.
    
    This allows Qt signals to work properly in the TUI by integrating
    Qt's event processing with urwid's terminal event loop.
    """
    
    def __init__(self, qt_app: QCoreApplication):
        super().__init__()
        self.qt_app = qt_app
        self._qt_timer = QTimer()
        self._qt_timer.timeout.connect(self._process_qt_events)
        self._qt_timer.setInterval(10)  # Process Qt events every 10ms
    
    def run(self):
        """Override run to start Qt timer."""
        self._qt_timer.start()
        super().run()
    
    def _process_qt_events(self):
        """Process pending Qt events."""
        self.qt_app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 10)
    
    def _loop(self):
        """Override main loop iteration to handle Qt."""
        # Process Qt events before urwid events
        self._process_qt_events()
        # Then process urwid events
        return super()._loop()
