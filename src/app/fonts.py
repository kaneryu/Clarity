import os
from PySide6.QtGui import QFont, QFontDatabase
from PySide6 import QtCore
from src import universal

def loadFonts():
    fontDir = os.path.join(universal.Paths.ASSETSPATH, "fonts")
    urbanist = os.path.join(fontDir, "Urbanist", "Urbanist-VariableFont_wght.ttf")
    Icons = os.path.join(fontDir, "Material_Symbols_Rounded", "MaterialSymbolsRounded-VariableFont_FILL,GRAD,opsz,wght.ttf")
    qf = QFontDatabase()
    qf.addApplicationFont(urbanist)
    qf.addApplicationFont(Icons)
    return qf