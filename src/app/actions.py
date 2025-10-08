from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QAction, QActionGroup


class songPlayAction(QAction):
    triggered = Signal(str)

    def __init__(self, parent: QObject = None):
        super().__init__("Play", parent)
        self.triggered.connect(self.on_triggered)

    @Slot()
    def on_triggered(self):
        self.triggered.emit("play")
