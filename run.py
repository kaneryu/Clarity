# Compilation mode, support OS-specific options
# nuitka-project: --mode=standalone
# The PySide6 plugin covers qt-plugins

# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --include-qt-plugins=sensible,styles,qml

# nuitka-project: --include-data-dir=src/app/qml=src/app/qml
# nuitka-project: --include-data-dir=src/app/assets=src/app/assets
# nuitka-project: --include-data-file=./version.txt=./version.txt
# nuitka-project: --include-data-file=src/version.txt=src/version.txt
# nuitka-project: --windows-icon-from-ico={MAIN_DIRECTORY}/nuitkaAssets/Logo.ico

# nuitka-project: --file-description="Clarity -- A music player."
# nuitka-project: --copyright="This is free and open-source software -- GNU GPL v3"
# nuitka-project: --windows-product-name="Clarity"

# nuitka-project: --product-version=0.36.0
# nuitka-project: --file-version=0.36.0

# nuitka-project: --output-filename=Clarity
# disabled: --disable-console
# nuitka-project: --user-package-configuration-file=./nuitka-fix.config.yml 

# STARTUP FLOW

# from run.py
# setup workers
# setup cache
# setup universal
# setup queue
# setup app
# run app

import src.universal
from src.app import main


main.main()