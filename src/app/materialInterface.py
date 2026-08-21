"""Material You theme colors, exposed to QML as `Theme.<colorName>`."""

from materialyoucolor.dynamiccolor.color_spec import COLOR_NAMES
from materialyoucolor.dynamiccolor.dynamic_scheme import DynamicScheme
from materialyoucolor.dynamiccolor.material_dynamic_colors import MaterialDynamicColors
from materialyoucolor.hct import Hct
from materialyoucolor.quantize import ImageQuantizeCelebi
from materialyoucolor.score.score import Score
from PySide6.QtCore import Property, QObject, Signal, Slot
import materialyoucolor.scheme

from src.misc.settings import getSetting

import importlib
import json
import logging
import pkgutil
import typing


def discoverSchemes() -> dict[str, type[DynamicScheme]]:
    """Every scheme variant the library ships, keyed by a picker-friendly name.

    e.g. {"Content": SchemeContent, ..., "Vibrant": SchemeVibrant}. `SchemeAndroid`
    and the legacy `Scheme` are skipped: neither is a DynamicScheme.

    Returns:
        dict[str, type[DynamicScheme]]: Scheme classes by name, alphabetically
    """
    schemes: dict[str, type[DynamicScheme]] = {}
    for module in pkgutil.iter_modules(materialyoucolor.scheme.__path__):
        imported = importlib.import_module(f"materialyoucolor.scheme.{module.name}")
        for name, obj in vars(imported).items():
            if (
                isinstance(obj, type)
                and issubclass(obj, DynamicScheme)
                and obj is not DynamicScheme
            ):
                schemes[name.removeprefix("Scheme")] = obj
    return dict(sorted(schemes.items()))


SCHEMES = discoverSchemes()
DEFAULT_SCHEME = "TonalSpot"

# Settings that drive the theme. Their dropdown options live in
# DEFAULTSETTINGS.json; `themeScheme` must list the keys of SCHEMES.
SCHEME_SETTING = "themeScheme"
DARK_SETTING = "themeDarkMode"
CONTRAST_SETTING = "themeContrast"

logger = logging.getLogger("ThemeLogger")


def colorToHex(name: str, scheme: DynamicScheme) -> str:
    """Hex value of one Material color under a scheme.

    Args:
        name (str): Name of the color, as in `COLOR_NAMES`
        scheme (DynamicScheme): Scheme to resolve the color against

    Returns:
        str: Hex string, e.g. "#9BD0D1" (the library's alpha byte is dropped,
            since Qt reads a leading byte as alpha, not red)
    """
    return getattr(MaterialDynamicColors, name).get_hex(scheme)[:7]


def colorProperty(name: str, notify: Signal) -> Property:
    """Build the QML-facing Property backing one Material color."""
    private = "_" + name

    def getter(self) -> str:
        return getattr(self, private)

    def setter(self, value: str) -> None:
        setattr(self, private, value)

    return Property(str, getter, setter, notify=notify)


class Theme(QObject):
    themeChanged = Signal(name="themeChanged")
    schemeChanged = Signal(name="schemeChanged")

    # Internal. Marshals a scheme onto the thread Theme lives on, so colors can
    # be applied from a bgworker job without re-evaluating QML bindings there.
    # AutoConnection stays synchronous when emitted from Theme's own thread.
    schemeReady = Signal(object, name="schemeReady")

    # A Property per Material color, e.g. `Theme.primary`. Written into the
    # class namespace here because Qt properties must exist at class creation.
    for _colorName in COLOR_NAMES:
        locals()[_colorName] = colorProperty(_colorName, themeChanged)
    del _colorName

    _instance: typing.Union["Theme", None] = None

    @classmethod
    def getInstance(cls) -> "Theme":
        if cls._instance is None:
            cls._instance = Theme()
        return cls._instance

    def __init__(self) -> None:
        super().__init__()
        for name in COLOR_NAMES:
            setattr(self, "_" + name, "#000000")

        # Mirrors of the settings below, so building a scheme costs no lookups.
        self._scheme = DEFAULT_SCHEME
        self._dark = True
        self._contrast = 0.0
        # Source color of the theme in use, to rebuild against when a setting changes.
        self._source: typing.Union[int, None] = None

        self.schemeReady.connect(self.applyScheme)
        self.followSettings()

    def followSettings(self) -> None:
        """Take scheme, dark mode and contrast from settings, and track changes."""
        for key in (SCHEME_SETTING, DARK_SETTING, CONTRAST_SETTING):
            getSetting(key).valueChanged.connect(self.settingsChanged)
        self.settingsChanged()

    @Slot()
    def settingsChanged(self) -> None:
        """Re-read the theme settings and re-theme if any of them moved."""
        scheme = getSetting(SCHEME_SETTING).value
        if scheme not in SCHEMES:
            logger.error(
                "Setting %s is %r, which no scheme provides; falling back to %s",
                SCHEME_SETTING,
                scheme,
                DEFAULT_SCHEME,
            )
            scheme = DEFAULT_SCHEME

        dark = getSetting(DARK_SETTING).value == "dark"
        contrast = float(getSetting(CONTRAST_SETTING).value)

        if (scheme, dark, contrast) == (self._scheme, self._dark, self._contrast):
            return

        schemeMoved = scheme != self._scheme
        self._scheme, self._dark, self._contrast = scheme, dark, contrast

        if schemeMoved:
            self.schemeChanged.emit()
        if self._source is not None:
            self.update_dynamicColors(self.rebuildScheme(self._source))

    @Property(list, constant=True)
    def availableSchemes(self) -> list[str]:
        """Names accepted by `scheme`, for a picker to list."""
        return list(SCHEMES)

    @Property(str, notify=schemeChanged)
    def scheme(self) -> str:
        """Name of the scheme variant in use, e.g. "TonalSpot"."""
        return self._scheme

    @scheme.setter
    def scheme(self, name: str) -> None:
        self.setScheme(name)

    @Slot(str)
    def setScheme(self, name: str) -> None:
        """Switch scheme variant, re-theming from the current source color.

        Writes the `themeScheme` setting, so the choice persists and the
        settings page stays in step.

        Args:
            name (str): One of `availableSchemes`. Anything else is ignored.
        """
        if name not in SCHEMES:
            logger.error(
                "Unknown scheme %r, expected one of: %s", name, ", ".join(SCHEMES)
            )
            return
        getSetting(SCHEME_SETTING).setValue(name)

    @Slot(result=str)
    def getAllColors(self) -> str:
        return json.dumps([{name: getattr(self, name)} for name in COLOR_NAMES])

    @Slot(str, result=str)
    def getColor(self, color: str) -> str:
        """Get color from color name

        Args:
            color (str): Name of color

        Returns:
            str: Hex value of color
        """
        return getattr(self, color)

    def get_dynamicColorObject(
        self, source: int, dark: bool, contrast: float
    ) -> DynamicScheme:
        """Get dynamic color object from source color, in the current variant

        Args:
            source (int): HCT color in int form
            dark (bool): Dark mode
            contrast (float): Contrast

        Returns:
            DynamicScheme: Dynamic color object
        """
        return SCHEMES[self._scheme](Hct.from_int(source), dark, contrast)

    def rebuildScheme(self, source: int) -> DynamicScheme:
        """Scheme for `source` in the variant, dark mode and contrast from settings.

        Args:
            source (int): HCT color in int form

        Returns:
            DynamicScheme: Dynamic color object
        """
        return self.get_dynamicColorObject(source, self._dark, self._contrast)

    def get_dynamicColors(
        self,
        source: int,
        dark: typing.Union[bool, None] = None,
        contrast: typing.Union[float, None] = None,
    ) -> None:
        """Apply the scheme generated from a source color to this theme.

        Args:
            source (int): HCT color in int form
            dark (bool | None): Dark mode. Defaults to the `themeDarkMode` setting
            contrast (float | None): Contrast. Defaults to the `themeContrast` setting
        """
        if dark is None and contrast is None:
            scheme = self.rebuildScheme(source)
        else:
            scheme = self.get_dynamicColorObject(
                source,
                self._dark if dark is None else dark,
                self._contrast if contrast is None else contrast,
            )
        self.update_dynamicColors(scheme)

    def update_dynamicColors(self, scheme: DynamicScheme) -> None:
        """Apply `scheme` to every color property. Safe to call from any thread."""
        self.schemeReady.emit(scheme)

    @Slot(object)
    def applyScheme(self, scheme: DynamicScheme) -> None:
        self._source = scheme.source_color_argb
        for name in COLOR_NAMES:
            setattr(self, "_" + name, colorToHex(name, scheme))
        self.themeChanged.emit()

    def get_dynamicColorsFromImage(self, path: str) -> DynamicScheme:
        """Apply the theme generated from an image, and return its scheme."""
        scheme = self.rebuildScheme(self.scoreImage(path))
        self.update_dynamicColors(scheme)
        return scheme

    def exportDynamicColorsFromImage(self, path: str) -> str:
        """Quantized colors of an image, as JSON. Does not touch the theme."""
        # quality=1 (use every pixel), max_colors=128
        return json.dumps(ImageQuantizeCelebi(path, 1, 128))

    def loadDynamicColorsFromExport(self, export: str) -> DynamicScheme:
        """Apply the theme stored in an export from `exportDynamicColorsFromImage`."""
        colors = {int(color): count for color, count in json.loads(export).items()}
        scheme = self.rebuildScheme(Score.score(colors)[0])
        self.update_dynamicColors(scheme)
        return scheme

    def scoreImage(self, path: str) -> int:
        """Best source color for an image, in int form."""
        colors: dict = ImageQuantizeCelebi(path, 1, 128)
        return Score.score(colors)[0]
