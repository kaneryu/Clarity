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

from PySide6.QtCore import Slot as Slot, QDir
from PySide6.QtGui import QIcon
from PySide6.QtQml import (
    QQmlApplicationEngine,
)
from PySide6.QtCore import Property as Property
from PySide6.QtWidgets import QApplication

# local imports
import src.app.materialInterface as materialInterface
import src.universal as universal
from . import Backend, Interactions


def generateRandomHexColor():
    return random.randint(0, 0xFFFFFF)

def cleanUp():
    global engine
    engine.deleteLater()
    # engine.quit.emit()

    
def appQuitOverride():
    cleanUp()
    time.sleep(1)
    sys.exit()
    
def main():
    global app, engine, backend, theme

    app = QApplication()
    app.setStyle("Material")
    app.aboutToQuit.connect(appQuitOverride)

    engine = QQmlApplicationEngine()
    engine.quit.connect(app.quit)
    
    qml = os.path.join(universal.Paths.qmlPath, "main.qml")

    backend = Backend.Backend()
    interactions = Interactions.Interactions()
    
    theme = materialInterface.Theme()
    theme.get_dynamicColors(0x1A1D1D, True, 0.0)
    
    engine.rootContext().setContextProperty("Theme", theme)
    engine.rootContext().setContextProperty("Backend", backend)
    engine.rootContext().setContextProperty("Interactions", interactions)

    icon = QIcon(os.path.join(universal.Paths.assetsPath, "Logo.png"))
    app.setWindowIcon(icon)
    app.setApplicationName("InnerTuneDesktop")
    
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