# stdlib imports
import dataclasses
import random
import os
import random
import sys
import threading
import time
import requests


# library imports
from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, QObject, Qt, QTimer, QThread, QEvent
from PySide6.QtCore import Signal as QSignal
from PySide6.QtCore import Slot as Slot, QDir
from PySide6.QtGui import QAction, QFont, QIcon
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
import materialInterface, base_models as base_models



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
    app = QApplication()
    
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

    # tim = QTimer()
    # tim.setInterval(10000)
    # tim.timeout.connect(lambda: theme.get_dynamicColors(generateRandomHexColor(), random.choice([True, False]), 0.0))
    # tim.start()
    
    print(QDir.currentPath())
    backend.loadComplete.emit()
    
    sys.exit(app.exec())
    

main()