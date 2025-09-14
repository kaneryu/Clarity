# stdlib imports
import random
import os
import random
import sys
import typing
import logging
import time
import ctypes

# library imports
from PySide6.QtCore import (
    QTimer,
    QUrl,
    QEventLoop,
    QResource,
    QFile
)

from PySide6.QtCore import Slot as Slot, QDir, QCoreApplication, Qt, QTimer, QThread
from PySide6.QtGui import QIcon, QFont, QFontDatabase
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlEngine,
    QQmlDebuggingEnabler,
    QQmlComponent,
    QQmlContext,
    qmlRegisterSingletonInstance
    
)
from PySide6.QtCore import Property as Property
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import QQuickWindow

from livecoding import start_livecoding_gui

# local imports
import src.app.materialInterface as materialInterface
import src.universal as universal
from . import Backend, Interactions, fonts
from src.misc import cleanup

__compiled__ = None # set to true when packaged

def generateRandomHexColor():
    return random.randint(0, 0xFFFFFF)


def engineSetup(engine: QQmlApplicationEngine, theme, backend, interactions):
    engine.rootContext().setContextProperty("Theme", theme)
    engine.rootContext().setContextProperty("Backend", backend)
    engine.rootContext().setContextProperty("Interactions", interactions)
    
    engine.rootContext().setContextProperty("AssetsPath", "file:///" + universal.Paths.ASSETSPATH.replace("\\", "/") + "/")
    engine.rootContext().setContextProperty("QMLPath", "file:///" + universal.Paths.QMLPATH.replace("\\", "/") + "/")
    engine.rootContext().setContextProperty("RootPath", "file:///" + universal.Paths.ROOTPATH.replace("\\", "/")+ "/")

    sip = universal.song_module.SongImageProvider()
    engine.addImageProvider("SongCover", sip)


def viewSetup(engine: QQmlApplicationEngine, theme, backend, interactions):
    engine.rootContext().setContextProperty("Theme", theme)
    engine.rootContext().setContextProperty("Backend", backend)
    engine.rootContext().setContextProperty("Interactions", interactions)
    
    engine.rootContext().setContextProperty("AssetsPath", "file:///" + universal.Paths.ASSETSPATH.replace("\\", "/") + "/")
    engine.rootContext().setContextProperty("QMLPath", "file:///" + universal.Paths.QMLPATH.replace("\\", "/") + "/")
    engine.rootContext().setContextProperty("RootPath", "file:///" + universal.Paths.ROOTPATH.replace("\\", "/")+ "/")

    sip = universal.song_module.SongImageProvider()
    engine.addImageProvider("SongCover", sip)
    
def reloadQML(engine: QQmlEngine, app, theme, backend, interactions, qml):
    print("Reloading QML...")
    engine.quit.disconnect(app.quit)
    # engine.quit.emit()
    engine.deleteLater()
    
    newEngine = None
    newEngine = QQmlApplicationEngine()
    engineSetup(engine, theme, backend, interactions)
    newEngine.load(qml)
    newEngine.quit.connect(app.quit)
    engine = newEngine
    
def main():
    def appQuitOverride():
        engine.exit.emit(1)
        cleanup.runCleanup()
    
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(appQuitOverride)
    
    fonts.loadFonts()
    app.setFont(QFont("Urbanist"))
    icon = QIcon(os.path.join(universal.Paths.ASSETSPATH, "clarityLogo.png"))
    app.setWindowIcon(icon)
    app.setApplicationName("Clarity")
    
    engine = QQmlApplicationEngine()
    qml = QUrl.fromLocalFile(os.path.join(universal.Paths.QMLPATH, "main.qml"))
    

    backend = Backend.Backend()
    interactions = Interactions.Interactions()
    theme = materialInterface.Theme.getInstance()
    theme.get_dynamicColors(0x1A1D1D, True, 0.0)
    engineSetup(engine,theme,backend,interactions)
    

    myappid = f'oss.clarity.music_player.{str(universal.version)}'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    engine.quit.connect(app.quit)
    engine.load(qml)
    if not engine.rootObjects():
        sys.exit(-1)
        
    backend.loadComplete.emit()
    app.exec()

def debug():
    def appQuitOverride():
        engine.exit.emit(1)
        cleanup.runCleanup()
    
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(appQuitOverride)
    
    fonts.loadFonts()
    app.setFont(QFont("Urbanist"))
    icon = QIcon(os.path.join(universal.Paths.ASSETSPATH, "clarityLogo.png"))
    app.setWindowIcon(icon)
    app.setApplicationName("Clarity")
    
    engine = QQmlApplicationEngine()
    qml = QUrl.fromLocalFile(os.path.join(universal.Paths.QMLPATH, "main.qml"))
    

    backend = Backend.Backend()
    interactions = Interactions.Interactions()
    theme = materialInterface.Theme.getInstance()
    theme.get_dynamicColors(0x1A1D1D, True, 0.0)
    engineSetup(engine,theme,backend,interactions)
    

    myappid = f'oss.clarity.music_player.{str(universal.version)}'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    engine.quit.connect(app.quit)
    
    start_livecoding_gui(
        engine,
        universal.Paths.QMLPATH,
        __file__
    )
    
    if not engine.rootObjects():
        sys.exit(-1)
        
    backend.loadComplete.emit()
    app.exec()
    
if __name__ == "__main__":
    print("Please use run.py to run this application, but we'll try anyway:")
    if __compiled__ is not None:
        main()
    else:
        debug()
        
# IMPLEMENT QSETTINGS
# AND QRC