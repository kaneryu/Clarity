# stdlib imports
import dataclasses
import random
import os
import pathlib
import random
import sys
import asyncio
import time
import requests


# library imports
from PySide6.QtCore import (
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    QObject,
    Qt,
    QTimer,
    QThread,
    QEvent,
    QFile,
    QRunnable,
    QThreadPool
)
from PySide6.QtCore import Signal as QSignal
from PySide6.QtCore import Slot as Slot, QDir
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWebEngineQuick import QtWebEngineQuick
from PySide6.QtQml import (
    QmlElement,
    QmlSingleton,
    QQmlApplicationEngine,
    qmlRegisterSingletonInstance,
    qmlRegisterSingletonType,
)
from PySide6.QtCore import Property as Property
from PySide6.QtWidgets import QApplication

# local imports
import src.app.materialInterface as materialInterface
import src.app.baseModels as baseModels
from src.app.pyutils import (roundimage, downloadimage, convertTocover)
import src.globals as globals

class BackgroundWorker(QThread):
    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            time.sleep(1)
            print("Background Worker Running")

    def stop(self):
        self.running = False
        

class ConvertToCoverWorker(QRunnable):
    def __init__(self, link, radius, size):
        super().__init__()
        self.link = link
        self.radius = radius
        self.size = size
        self.hsh = None
        
    def run(self):
        self.hsh = asyncio.run(convertTocover.convertToCover(link=self.link, radius=self.radius, size=self.size))
        
    def getHash(self):
        return self.hsh
    
    def getpath(self):
        return globals.imageCache.sgetKeyPath(self.hsh)


def startBackgroundWorker():
    worker = BackgroundWorker()
    worker.start()
    return worker
    
    
QML_IMPORT_NAME = "CreateTheSun"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0

@QmlElement
class Backend(QObject):
    loadComplete = QSignal(name="loadComplete")
    activeTabChanged = QSignal(name="activeTabChanged")
    # tabModelChanged = QSignal(name="tabModelChanged")
    _instance = None
    
    def __init__(self):
        super().__init__()
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._value = 0
    
    @Slot(str, result=str)
    def getPage(self, url: str) -> str:
        
        # parse the url
        # possible roots as of now:
        # page
        # then we have the page name after, so like page/home
        
        # pages are stored locally in the html folder (src/app/html)
        
        url = url.split("/")
        print(url)
        print("file:///" + os.path.join(os.path.dirname(__file__), "html", url[0], url[1], "index.html").replace("\\","/"))
        return "file:///" + os.path.join(os.path.dirname(__file__), "html", url[0], url[1], "index.html").replace("\\","/")
        
    @Slot(result=str)
    def ping(self) -> str:
        return "pong"
    
    @Slot(str, int, result=str)
    def roundImage(self, path, radius = 20) -> str:
        
        hsh = globals.ghash(path + "rounded" + str(radius))
        if globals.globalCache.scheckInCache(hsh): # check if the rounded image is cached
            return "file:///" + globals.imageCache.sgetKeyPath(hsh) # return the path of the image
        
        # check if source image is cached
        
        path = asyncio.run(downloadimage.downloadimage(path))
        hsh = asyncio.run(roundimage.roundimage(path, radius))
    
        return "file:///" + globals.imageCache.sgetKeyPath(hsh) # return the path of the image
                
        
    @Slot(str, int, int, result=str)
    def convertToCover(self, link: str, radius: str, size: int) -> str:
        return "file:///" + globals.imageCache.sgetKeyPath(asyncio.run(convertTocover.convertToCover(link=link, radius=radius, size=size)))
            
def generateRandomHexColor():
    return random.randint(0, 0xFFFFFF)

def cleanUp():
    global engine
    engine.quit()
    
def appQuitOverride(event: QEvent):
    global bgworker
    bgworker.stop()
    cleanUp()
    event.accept()
    
def main():
    global app, engine, backend, theme
    # webengine = QtWebEngineQuick()
    # webengine.initialize()
    

    
    globals.globalCache.sput("test", "test", byte=False)
    asyncio.run(downloadimage.downloadimage("https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"))
    app = QApplication()
    app.setStyle("Material")
    app.aboutToQuit.connect(appQuitOverride)

    engine = QQmlApplicationEngine()
    engine.quit.connect(app.quit)
    
    qml = os.path.join(os.path.dirname(__file__), "qml/main.qml")

    backend = Backend()

    theme = materialInterface.Theme()
    theme.get_dynamicColors(0x1A1D1D, True, 0.0)
    
    engine.rootContext().setContextProperty("Theme", theme)
    engine.rootContext().setContextProperty("Backend", backend)

    
    engine.load(qml)
    if not engine.rootObjects():
        sys.exit(-1)

    tim = QTimer()
    tim.setInterval(1000)
    tim.timeout.connect(lambda: theme.get_dynamicColors(generateRandomHexColor(), random.choice([True]), 0.0))
    tim.start()
    
    print(QDir.currentPath())
    backend.loadComplete.emit()
    
    sys.exit(app.exec())
    
if __name__ == "__main__":
    print("Please use run.py to run this application, but we'll try anyway:")
    main()