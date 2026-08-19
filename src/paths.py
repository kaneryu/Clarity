import os
from .misc.compiled import __compiled__


class Paths:
    ROOTPATH = os.path.dirname(os.path.abspath(__file__))
    ASSETSPATH = os.path.abspath(
        os.path.join(ROOTPATH, "assets")
        if __compiled__
        else os.path.join("src", "app", "assets")
    )
    QMLPATH = os.path.abspath(
        os.path.join(ROOTPATH, "qml")
        if __compiled__
        else os.path.join("src", "app", "qml")
    )
    # This file lives in src, so this is the root of the project.
    DATAPATH = os.path.abspath(os.path.join(ROOTPATH, "..", "data"))

    SETTINGSPATH = os.path.join(ROOTPATH, "settings.json")
    VERSIONPATH = os.path.join(ROOTPATH, "version.txt")
