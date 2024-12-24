import os
__compiled__ = False # will be set to true by nuitka
class Paths:
    assetsPath = os.path.abspath(os.path.join("assets") if __compiled__ else os.path.join("src", "app", "assets"))
    qmlPath = os.path.abspath(os.path.join("qml") if __compiled__ else os.path.join("src", "app", "qml"))
    rootpath = os.path.abspath(".")

print("assets path:", Paths.assetsPath)
print("qml path:", Paths.qmlPath)
print("root path:", Paths.rootpath)
