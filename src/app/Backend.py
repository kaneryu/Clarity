# stdlib imports
import os
import logging
import typing
import urllib.parse

# library imports
from PySide6.QtCore import (
    QObject,
)

from PySide6.QtCore import Signal as QSignal
from PySide6.QtCore import Slot as Slot
from PySide6.QtQml import (
    QmlElement,
)
from PySide6.QtCore import Property


import src.universal as universal
import src.app.materialInterface as materialInterface
import src.network as networking
import src.paths as paths
import src.misc.settings as settings
import src.misc.logHistoryManager as logHistoryManager
from src.providerInterface.song.models.songListModel import (
    SongListModel,
    SongProxyListModel,
)


QML_IMPORT_NAME = "Backend"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class TabManager(QObject):
    """
    Okay, so this is just going to be a simple object that holds the available tabs and their root paths
    It will not keep track of tabs itself, combining a tab manager and the URL system would be weird
    So, we will just check if the root of the URL matches the path of a tab, and if it does, we will set that tab as active
    This is checked every time the variable is polled, not stored.
    """

    activeTabIndexChanged = QSignal(int, name="activeTabIndexChanged")

    def __init__(self):
        super().__init__()

        self.defualtTabIndex = 0  # Home for now

        self._tabs = [  # type: ignore[assignment]
            {"name": "home", "title": "Home", "path": "page/home", "showInNav": True},
            {
                "name": "explore",
                "title": "Explore",
                "path": "page/explore",
                "showInNav": False,  # NotImplemented
            },
            {
                "name": "library",
                "title": "Library",
                "path": "page/library",
                "showInNav": False,  # NotImplemented
            },
            {
                "name": "downloads",
                "title": "Downloads",  # Temp, will be rolled into the Library eventually
                "path": "page/downloads",
                "showInNav": True,
            },
            {
                "name": "liked",
                "title": "Liked Songs",  # Temp, will be rolled into the Library eventually
                "path": "page/liked",
                "showInNav": True,
            },
            {
                "name": "search",
                "title": "Search",
                "path": "page/search",
                "showInNav": False,  # Perm, it's a special tab
            },
            {
                "name": "settings",
                "title": "Settings",
                "path": "page/settings",
                "showInNav": False,  # Perm, navigate to it using settings button, not tabbar
            },
        ]

    @Property(list, constant=True)
    def tabs(self):
        return self._tabs

    @Property(int, constant=True)
    def tabCount(self):
        return len(self._tabs)

    @Property(list, constant=True)
    def tabNames(self):
        return [tab["name"] for tab in self.tabs]


@QmlElement
class Backend(QObject):
    loadComplete = QSignal(name="loadComplete")
    activeTabChanged = QSignal(name="activeTabChanged")
    # tabModelChanged = QSignal(name="tabModelChanged")
    queueVisibleChanged = QSignal(name="queueVisibleChanged")
    urlChanged = QSignal(name="urlChanged")
    loginRedirect = QSignal(name="loginRedirect")
    loginComplete = QSignal(name="loginComplete")

    settingChanged = QSignal(name="settingChanged")

    onlineChanged = QSignal(name="onlineChanged")

    _instance: "Backend"

    def __new__(cls) -> "Backend":
        if (hasattr(cls, "_instance") and cls._instance is None) or not hasattr(
            cls, "_instance"
        ):  # if instance var exists and is not None, or if it does not exist
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            super().__init__()
            self.initialized = True
            self._value = 0
            self._queueModel = universal.queueInstance.queueModel
            self._queueVisible = False

            # Forward settings changes from Settings to Backend for QML
            universal.settings.settingChanged.connect(self.settingChanged)
            universal.queueInstance.songChanged.connect(self.updateMaterialColors)

            universal.appUrl.urlChanged.connect(self.urlChanged)

            self.downloadModel = DownloadedSongsModel()
            self.likedModel = LikedSongsModel()

            self.tabmanager = TabManager()

            self._activeTabIndex = self.tabmanager.defualtTabIndex
            self.urlChanged.connect(self.urlUpdateTabChecker)

    @Property(list, constant=True)
    def tabs(self):
        return self.tabmanager.tabs

    @Property(list, constant=True)
    def navTabs(self):
        return [tab for tab in self.tabmanager.tabs if tab["showInNav"]]

    @Property(int, notify=activeTabChanged)
    def activeNavTabIndex(self):
        navTabs = self.navTabs
        activeTabName = self.activeTabName
        for i in range(len(navTabs)):
            if navTabs[i]["name"] == activeTabName:
                return i
        return -1  # Return -1 if no matching tab is found

    @Property(object, constant=True)
    def tabManager(self):
        return self.tabmanager

    @Property(int, notify=activeTabChanged)
    def activeTabIndex(self):
        tabpaths = [self.tabs[i]["path"] for i in range(self.tabmanager.tabCount)]
        currentPath = universal.appUrl.getUrl().strip("clarity:///")
        for i in range(len(tabpaths)):
            if currentPath.startswith(tabpaths[i]):
                if not self._activeTabIndex == i:
                    self._activeTabIndex = i
                    self.activeTabChanged.emit()  # Emit the signal to notify of the change
                    # This miiiight be dangerous, maybe an edge case where there could be an infinite loop of checks
                    # I'm not sure how that would happen though...
                    # Tally times when it happened: 1
                return i

        return -1  # Return -1 if no matching tab is found

    @Property(str, notify=activeTabChanged)
    def activeTabName(self):
        index = self.activeTabIndex
        if index == -1:
            return ""
        return self.tabs[index]["name"]

    @Property(str, notify=activeTabChanged)
    def activeTabTitle(self):
        index = self.activeTabIndex
        if index == -1:
            return ""
        return self.tabs[index]["title"]

    def urlUpdateTabChecker(self):
        # This function is called every time the URL changes, and it checks if the active tab should be changed
        newActiveTabIndex = self.activeTabIndex
        if newActiveTabIndex != self._activeTabIndex:
            self._activeTabIndex = newActiveTabIndex
            self.activeTabChanged.emit()

    @Property(str, notify=urlChanged)
    def url(self):
        return universal.appUrl.getUrl()

    @url.setter
    def url(self, value: str):
        try:
            urllib.parse.urlparse(value)
        except Exception:
            print("Set URL failed, invalid URL", value)
            return
        universal.appUrl.setUrl(value)

    @Slot(str)
    def setUrl(self, value):
        self.url = "clarity:///" + value

    @Property(dict, notify=urlChanged)
    def currentQuery(self):
        return universal.appUrl.getQuery()

    @Slot(result=dict)
    def getCurrentQuery(self) -> dict:
        # Some things might want to get the query once, instead of binding to it and listening for changes
        return universal.appUrl.getQuery()

    @Property(str, notify=urlChanged)
    def getCurrentPageFilePath(self):
        path = universal.appUrl.getPath()
        try:
            if path[0] == "page":
                if path == "/":
                    ret = os.path.join(universal.Paths.QMLPATH, "pages", "home.qml")
                else:
                    first = path[1]
                    first.replace("/", "")
                    ret = os.path.join(universal.Paths.QMLPATH, "pages", first + ".qml")

                if not os.path.exists(ret):
                    print("Path does not exist", ret)
                    return ""
                return "file:///" + ret
        except Exception as e:
            logging.getLogger("BackendClassLogger").error(
                "Error in getCurrentPageFilePath: %s", e
            )
            return ""

    def updateMaterialColors(self):
        def updateMaterialColors_task():
            songobj = universal.queueInstance.currentSongObject

            retrievedMaterialColors = songobj.materialColor
            if retrievedMaterialColors is not None:
                materialInterface.Theme.getInstance().loadDynamicColorsFromExport(
                    retrievedMaterialColors
                )
                return

            thumb = songobj.bestThumbnailUrl  # type: ignore[attr-defined]
            res = networking.networkManager.get(thumb)
            if res is None:
                return
            with open(os.path.join(paths.Paths.DATAPATH, "currentthumb"), "wb") as f:
                f.write(res.content)

            if res is not None:
                export = (
                    materialInterface.Theme.getInstance().exportDynamicColorsFromImage(
                        os.path.join(paths.Paths.DATAPATH, "currentthumb")
                    )
                )
                if export is not None:
                    materialInterface.Theme.getInstance().loadDynamicColorsFromExport(
                        export
                    )
                    songobj.materialColor = export

        universal.bgworker.addJob(updateMaterialColors_task)

    @Slot(str)
    def setSearchURL(self, query):
        self.url = "clarity:///page/search?query=" + query

    @Slot(result=QObject)
    def getqueueModel(self):
        return universal.queueInstance.queueModel

    @Property(QObject, constant=True)
    def queueModel(self):
        return self._queueModel

    @Property(QObject, constant=True)
    def searchModel(self):
        return universal.searchModel

    @Property(QObject, constant=True)
    def settingsModel(self):
        return universal.settings.settingsModel

    @Property(QObject, constant=True)
    def settingsInterface(self):
        return settings.QmlSettingsInterface.instance()

    @Property(QObject, constant=True)
    def logHistoryModel(self):
        return logHistoryManager.bridge.historyModel

    @Property(QObject, constant=True)
    def notifyingLogHistoryModel(self):
        return logHistoryManager.bridge.notifyingModel

    @Property(QObject, constant=True)
    def logHistoryBridge(self):
        return logHistoryManager.bridge

    @Property(QObject, constant=True)
    def downloadedSongsModel(self):
        return self.downloadModel

    @Property(QObject, constant=True)
    def likedSongsModel(self):
        return self.likedModel

    @Slot(str, result=QObject)
    def getSettingsObjectByName(self, name: str) -> QObject:
        return settings.QmlSettingsInterface.instance().getSettingsObjectByName(name)

    @Property(QObject, constant=True)
    def queue(self):
        return universal.queueInstance

    @Property(bool, notify=queueVisibleChanged)
    def queueVisible(self):
        return self._queueVisible

    @queueVisible.setter
    def queueVisible(self, value):
        self._queueVisible = value
        self.queueVisibleChanged.emit()

    @Slot(str, result=str)
    def getPage(self, url: str) -> str:

        # parse the url
        # possible roots as of now:
        # page
        # then we have the page name after, so like page/home

        # pages are stored locally in the html folder (src/app/html)

        url: list[str] = url.split("/")
        print(url)
        print(
            "file:///"
            + os.path.join(
                os.path.dirname(__file__), "html", url[0], url[1], "index.html"
            ).replace("\\", "/")
        )
        return "file:///" + os.path.join(
            os.path.dirname(__file__), "html", url[0], url[1], "index.html"
        ).replace("\\", "/")

    @Slot(result=str)
    def ping(self) -> str:
        return "pong"


def castUb(input: typing.Any) -> typing.Union[bytes, bytearray]:
    return typing.cast(typing.Union[bytes, bytearray], input)


class DownloadedSongsModel(SongProxyListModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__()
        self.setSongList(universal.getAllDownloadedSongs_Objects(proxy=True))

        universal.UniversalSignals.songDownloaded.connect(self.downloadedSongsUpdated)

    def downloadedSongsUpdated(self):
        self.setSongList(universal.getAllDownloadedSongs_Objects())


class LikedSongsModel(SongProxyListModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__()
        self.setSongList(universal.getAllLikedSongs_Objects(proxy=True))

        universal.UniversalSignals.songLikeStateChanged.connect(self.likedSongsUpdated)

    def likedSongsUpdated(self):
        self.setSongList(universal.getAllLikedSongs_Objects())
