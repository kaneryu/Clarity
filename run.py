# Compilation mode, support OS-specific options
# nuitka-project: --mode=standalone
# The PySide6 plugin covers qt-plugins

# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --include-qt-plugins=sensible,styles,qml

# nuitka-project: --include-data-dir=src/app/qml=qml
# nuitka-project: --include-data-dir=src/app/assets=assets
# nuitka-project: --include-data-file=./version.txt=./version.txt
# nuitka-project: --include-data-file=./version.txt=./compiled.txt
# nuitka-project: --include-data-file=./phantomjs.exe=./phantomjs.exe
# nuitka-project: --include-data-file=./src/databaseInterface/schema.sql=./assets/database/schema.sql

# nuitka-project: --file-description="Clarity v0.63.0"
# nuitka-project: --copyright="This is free and open-source software — GNU GPL v3"

# nuitka-project: --product-version=0.63.0
# nuitka-project: --file-version=0.63.0

# nuitka-project-if: {OS} == "Windows":
#    nuitka-project: --windows-icon-from-ico={MAIN_DIRECTORY}/nuitkaAssets/Logo.ico
#    nuitka-project: --windows-product-name="Clarity"

# macOS needs a real .app bundle: Control Center looks the Now Playing badge up
# from CFBundleIdentifier (set by --macos-signed-app-name) via LaunchServices,
# so a loose executable shows a blank placeholder no matter what we publish to
# MPNowPlayingInfoCenter.
# nuitka-project-if: {OS} == "Darwin":
#    nuitka-project: --macos-create-app-bundle
#    nuitka-project: --macos-app-icon={MAIN_DIRECTORY}/nuitkaAssets/Logo.icns
#    nuitka-project: --macos-app-name="Clarity"
#    nuitka-project: --macos-signed-app-name="com.kaneryu.clarity"
#    nuitka-project: --macos-app-version=0.61.0
#    nuitka-project: --macos-app-mode=gui

# nuitka-project: --output-filename=Clarity
# nuitka-project: --user-package-configuration-file=./nuitka-fix.config.yml

# STARTUP FLOW

# from run.py
# setup workers
# setup cache
# setup universal
# setup queue
# setup app
# run app

import src.universal  # noqa: F401 (importing universal runs setup code)
from src.app import main
from src.misc.compiled import __compiled__

if __compiled__:
    main.main()
else:
    main.debug()
