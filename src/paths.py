import os
__compiled__ = False # will be set to true by nuitka


class Paths:
    ASSETSPATH = os.path.abspath(os.path.join("assets") if __compiled__ else os.path.join("src", "app", "assets"))
    QMLPATH = os.path.abspath(os.path.join("qml") if __compiled__ else os.path.join("src", "app", "qml"))
    ROOTPATH = os.path.abspath(".")
    
    SETTINGSPATH = os.path.join(ROOTPATH, "settings.json")
    VERSIONPATH = os.path.join(ROOTPATH, "version.txt")