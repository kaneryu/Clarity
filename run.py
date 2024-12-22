# Compilation mode, support OS-specific options
# nuitka-project: --mode=standalone
# The PySide6 plugin covers qt-plugins

# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --include-qt-plugins=sensible,styles,qml

# nuitka-project: --include-data-dir=src/app/qml=src/app/qml
# nuitka-project: --include-data-dir=src/app/assets=src/app/assets
# nuitka-project: --windows-icon-from-ico={MAIN_DIRECTORY}/nuitkaAssets/Logo.ico

# nuitka-project: --file-description="InnerTuneDesktop -- A music player."
# nuitka-project: --copyright="This is free and open-source software -- GNU GPL v3"
# nuitka-project: --windows-product-name="InnerTuneDesktop"

# nuitka-project: --product-version=0.9.0
# nuitka-project: --file-version=0.9.0

# nuitka-project: --output-filename=InnerTuneDesktop
# disabled: --disable-console
# nuitka-project: --user-package-configuration-file=./nuitka-fix.config.yml 

import src.universal
from src.app import main


main.main()