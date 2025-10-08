import urllib.parse
import typing

from PySide6.QtCore import QObject, Signal, Slot, Property


class AppUrl(QObject):
    # Signals (no payload; properties will be re-read by bindings)
    urlChanged = Signal()
    pathChanged = Signal()
    queryChanged = Signal()
    pointerChanged = Signal()
    historyChanged = Signal()
    canGoBackChanged = Signal()
    canGoForwardChanged = Signal()

    _instance: typing.Union["AppUrl", None] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppUrl, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            super().__init__()
            self.history = ["clarity:///page/home?firstlauch=true"]
            self.pointer = 0
            self.initialized = True

    def getParsedUrl(self):
        return urllib.parse.urlparse(self.history[self.pointer])

    def getUrl(self):
        return self.history[self.pointer]

    def getPath(self) -> list:
        p = self.getParsedUrl().path
        if p == "":
            return []
        return p.lstrip("/").split("/")

    def getQuery(self) -> dict:
        return urllib.parse.parse_qs(self.getParsedUrl().query)

    # Navigation helpers exposed as properties
    def _getCanGoBack(self) -> bool:
        return self.pointer > 0

    def _getCanGoForward(self) -> bool:
        return self.pointer < len(self.history) - 1

    # Emitters
    def _emitPointerAndDerived(self):
        self.pointerChanged.emit()
        self.urlChanged.emit()
        self.pathChanged.emit()
        self.queryChanged.emit()
        self.canGoBackChanged.emit()
        self.canGoForwardChanged.emit()

    # Slots
    @Slot(int)
    def goToHistory(self, index: int):
        # -1 is a special case for going to the end of the history
        new_index = index if index != -1 else len(self.history) - 1
        if new_index < 0:
            new_index = 0
        if new_index >= len(self.history):
            new_index = len(self.history) - 1
        if new_index != self.pointer:
            self.pointer = new_index
            self._emitPointerAndDerived()

    @Slot()
    def goBack(self):
        if self._getCanGoBack():
            self.pointer -= 1
            self._emitPointerAndDerived()

    @Slot()
    def goForward(self):
        if self._getCanGoForward():
            self.pointer += 1
            self._emitPointerAndDerived()

    @Slot(str)
    def setUrl(self, url: str):
        # remove all history after the current pointer
        if self.pointer < len(self.history) - 1:
            self.history = self.history[: self.pointer + 1]
            self.historyChanged.emit()
        self.history.append(url)
        self.pointer += 1
        self.historyChanged.emit()
        self._emitPointerAndDerived()

    # Properties
    url = Property(str, fget=getUrl, fset=setUrl, notify=urlChanged)
    path = Property(list, fget=getPath, notify=pathChanged)
    query = Property(dict, fget=getQuery, notify=queryChanged)
    canGoBack = Property(bool, fget=_getCanGoBack, notify=canGoBackChanged)
    canGoForward = Property(bool, fget=_getCanGoForward, notify=canGoForwardChanged)
    pointerIndex = Property(int, fget=lambda self: self.pointer, notify=pointerChanged)
    historyLength = Property(
        int, fget=lambda self: len(self.history), notify=historyChanged
    )


appUrl = AppUrl()
