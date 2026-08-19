import sys
import enum

isWindows = sys.platform.startswith("win")
isMac = sys.platform.startswith("darwin")
isLinux = sys.platform.startswith("linux")
isUndefined = not (isWindows or isMac or isLinux)


class Platform(enum.Enum):
    Windows = "Windows"
    MacOS = "MacOS"
    Linux = "Linux"
    undefined = "undefined"


platform = (
    Platform.Windows
    if isWindows
    else Platform.MacOS if isMac else Platform.Linux if isLinux else Platform.undefined
)
