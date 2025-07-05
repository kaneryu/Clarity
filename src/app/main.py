# stdlib imports
import random
import os
import random
import sys
import time

# library imports
from PySide6.QtCore import (
    QTimer,
)

from PySide6.QtCore import Slot as Slot, QDir, QCoreApplication, Qt
from PySide6.QtGui import QIcon, QFont, QFontDatabase
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlDebuggingEnabler,
)
from PySide6.QtWebEngineQuick import QtWebEngineQuick, QQuickWebEngineProfile
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo

from PySide6.QtCore import Property as Property
from PySide6.QtWidgets import QApplication

# local imports
import src.app.materialInterface as materialInterface
import src.universal as universal
from . import Backend, Interactions, fonts
from src.misc import cleanup



def generateRandomHexColor():
    return random.randint(0, 0xFFFFFF)

    

def main():
    def appQuitOverride():
        engine.exit.emit(1)
        cleanup.runCleanup()
    
    QQmlDebuggingEnabler.enableDebugging(False)
    
    QtWebEngineQuick.initialize()
    
    app = QApplication(sys.argv)
    webprofile = QQuickWebEngineProfile.defaultProfile()
    profileInterfaceManager = Backend.ProfileInterfaceManager(webprofile)

    app.setStyle("Material")
    app.aboutToQuit.connect(appQuitOverride)
    
    fonts.loadFonts()
    app.setFont(QFont("Urbanist"))

    engine = QQmlApplicationEngine()
    # engine.addImageProvider TODO: Add image provider
    engine.quit.connect(app.quit)
    
    qml = os.path.join(universal.Paths.qmlPath, "main.qml")

    backend = Backend.Backend()
    interactions = Interactions.Interactions()
    
    theme = materialInterface.Theme()
    theme.get_dynamicColors(0x1A1D1D, True, 0.0)
    
    engine.rootContext().setContextProperty("Theme", theme)
    engine.rootContext().setContextProperty("Backend", backend)
    engine.rootContext().setContextProperty("Interactions", interactions)
    
    engine.rootContext().setContextProperty("AssetsPath", "file:///" + universal.Paths.assetsPath.replace("\\", "/") + "/")
    engine.rootContext().setContextProperty("QMLPath", "file:///" + universal.Paths.qmlPath.replace("\\", "/") + "/")
    engine.rootContext().setContextProperty("RootPath", "file:///" + universal.Paths.rootpath.replace("\\", "/")+ "/")

    sip = universal.song_module.SongImageProvider()
    engine.addImageProvider("SongCover", sip)
    
    icon = QIcon(os.path.join(universal.Paths.assetsPath, "clarityLogo.png"))
    app.setWindowIcon(icon)
    app.setApplicationName("Clarity")
    engine.load(qml)
    if not engine.rootObjects():
        sys.exit(-1)

    # tim = QTimer()
    # tim.setInterval(1000)
    # tim.timeout.connect(lambda: theme.get_dynamicColors(generateRandomHexColor(), random.choice([True]), 0.0))
    # tim.start()
    
    print(QDir.currentPath())
    backend.loadComplete.emit()
    
    app.exec()
    
if __name__ == "__main__":
    print("Please use run.py to run this application, but we'll try anyway:")
    main()