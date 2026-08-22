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


APP_NAME = "Clarity"
# Must match --macos-signed-app-name in run.py, which is what Nuitka writes into
# the built bundle's CFBundleIdentifier.
APP_BUNDLE_IDENTIFIER = "com.kaneryu.clarity"


def applyMacBundleIdentity() -> None:
    """Give the running process a bundle identity on macOS.

    Run from source there is no .app, so NSBundle.mainBundle() carries an empty
    info dictionary: the menu bar reads "Python", and Control Center has no
    CFBundleIdentifier to resolve the Now Playing app icon from -- hence the
    blank placeholder badge next to the artwork.

    Patching the in-memory dictionary fixes the menu bar name outright, and lets
    the badge resolve once Clarity.app has been built and launched at least once
    (LaunchServices needs to have seen that identifier somewhere).

    Must be called before the first QApplication, which is what spins up
    NSApplication. No-op off macOS, and defers to a real bundle when there is
    one, so this is safe in a compiled build.
    """
    if not isMac:
        return
    try:
        from Foundation import NSBundle
    except ImportError:  # pyobjc missing; nothing to do
        return

    bundle = NSBundle.mainBundle()
    if bundle is None:
        return
    info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
    if info is None:
        return

    try:
        if not info.get("CFBundleIdentifier"):
            info["CFBundleIdentifier"] = APP_BUNDLE_IDENTIFIER
        if not info.get("CFBundleName"):
            info["CFBundleName"] = APP_NAME
    except (TypeError, ValueError):
        # Immutable info dictionary (some packaging layouts); not worth failing
        # startup over a cosmetic icon.
        pass
