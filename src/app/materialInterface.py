from materialyoucolor.dynamiccolor.material_dynamic_colors import MaterialDynamicColors
from materialyoucolor.dynamiccolor.dynamic_color import DynamicColor
from materialyoucolor.utils import color_utils
from materialyoucolor.hct import Hct
from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot
from materialyoucolor.scheme.dynamic_scheme import DynamicScheme
from materialyoucolor.score.score import Score
import materialyoucolor.quantize as materialQuantize
from PySide6.QtCore import QObject, Qt, Slot, Property, Signal

import json
import typing
import dataclasses

rgba_to_hex = lambda rgba: "#{:02X}{:02X}{:02X}{:02X}".format(*map(round, rgba))[:-2]


class Theme(QObject):
    themeChanged = Signal(name="themeChanged")

    _instance: typing.Union["Theme", None]

    @classmethod
    def getInstance(cls) -> "Theme":
        if (hasattr(cls, "_instance") and cls._instance is None) or not hasattr(
            cls, "_instance"
        ):  # if instance var exists and is not None, or if it does not exist
            cls._instance = Theme()
        return cls._instance

    def __init__(self) -> None:
        super().__init__()
        self._primary_paletteKeyColor: str
        self._secondary_paletteKeyColor: str
        self._tertiary_paletteKeyColor: str
        self._neutral_paletteKeyColor: str
        self._neutral_variant_paletteKeyColor: str
        self._background: str
        self._onBackground: str
        self._surface: str
        self._surfaceDim: str
        self._surfaceBright: str
        self._surfaceContainerLowest: str
        self._surfaceContainerLow: str
        self._surfaceContainer: str
        self._surfaceContainerHigh: str
        self._surfaceContainerHighest: str
        self._onSurface: str
        self._surfaceVariant: str
        self._onSurfaceVariant: str
        self._inverseSurface: str
        self._inverseOnSurface: str
        self._outline: str
        self._outlineVariant: str
        self._shadow: str
        self._scrim: str
        self._surfaceTint: str
        self._primary: str
        self._onPrimary: str
        self._primaryContainer: str
        self._onPrimaryContainer: str
        self._inversePrimary: str
        self._secondary: str
        self._onSecondary: str
        self._secondaryContainer: str
        self._onSecondaryContainer: str
        self._tertiary: str
        self._onTertiary: str
        self._tertiaryContainer: str
        self._onTertiaryContainer: str
        self._error: str
        self._onError: str
        self._errorContainer: str
        self._onErrorContainer: str
        self._primaryFixed: str
        self._primaryFixedDim: str
        self._onPrimaryFixed: str
        self._onPrimaryFixedVariant: str
        self._secondaryFixed: str
        self._secondaryFixedDim: str
        self._onSecondaryFixed: str
        self._onSecondaryFixedVariant: str
        self._tertiaryFixed: str
        self._tertiaryFixedDim: str
        self._onTertiaryFixed: str
        self._onTertiaryFixedVariant: str

        self.themeLight: DynamicScheme
        self.themeDark: DynamicScheme

    @Slot(result=str)
    def getAllColors(self):
        retlist = []
        for color in vars(
            MaterialDynamicColors
        ).keys():  # for every attr in this reference class
            color_name = getattr(
                MaterialDynamicColors, color
            )  # get the name of the attr from the reference
            if hasattr(color_name, "get_hct"):  # now we check if the attr is a color
                retlist.append(
                    {color: str(eval(f"self.{color}"))}
                )  # then we actually get the color from this class

        return json.dumps(retlist)

    @Slot(str, result=str)
    def getColor(self, color: str) -> str:
        """Get color from color name

        Args:
            color (str): Name of color

        Returns:
            str: Hex value of color
        """
        return getattr(self, color)

    def get_dynamicColors(
        self, source: int, dark: bool, contrast: float
    ) -> SchemeTonalSpot:
        """Get dynamic colors from source color

        Args:
            source (int): HCT color in int form
            dark (bool): _description_
            contrast (float): _description_

        Returns:
            SchemeTonalSpot: _description_
        """
        try:
            self.__getattribute__("primaryContainer")
        except AttributeError:
            firstTime = True
        else:
            firstTime = False

        scheme = SchemeTonalSpot(  # choose any scheme here
            Hct.from_int(source),  # source color in hct form
            dark,  # dark mode
            contrast,  # contrast
        )

        for color in vars(MaterialDynamicColors).keys():
            color_name = getattr(MaterialDynamicColors, color)
            if hasattr(color_name, "get_hct"):  # is a color
                #             print("self._" + color + ": str")
                #             print(f"""
                # @Property(str, notify=themeChanged)
                # def {color}(self):
                #     return self._{color}

                # @{color_name}.setter
                # def {color_name}(self, value):
                #     self._{color_name} = value
                #     self.themeChanged.emit()

                #                   """)

                if firstTime:
                    color_name: DynamicColor
                    c = color_name.get_hct(scheme).to_rgba()  # get color in rgba format
                    (
                        c[2] + 1
                    )  # for some reason every blue value is 1 less than it should be, so we add 1 to it
                    self.__setattr__(
                        color, self.list_rgb_to_hex(c)
                    )  # set attribute of color name to its value in rgba format
                else:
                    exec(
                        f"self.{color} = self.list_rgb_to_hex(color_name.get_hct(scheme).to_rgba())"
                    )
        self.themeChanged.emit()

    def get_dynamicColorObject(
        self, source: int, dark: bool, contrast: float
    ) -> DynamicScheme:
        """Get dynamic color object from source color

        Args:
            source (int): HCT color in int form
            dark (bool): Dark mode
            contrast (float): Contrast

        Returns:
            DynamicScheme: Dynamic color object
        """
        scheme = SchemeTonalSpot(  # choose any scheme here
            Hct.from_int(source),  # source color in hct form
            dark,  # dark mode
            contrast,  # contrast
        )
        return scheme

    def get_dynamicColorsFromImage(self, path: str):
        colors: dict = materialQuantize.ImageQuantizeCelebi(
            path, 1, 128
        )  # Get colors from image, quality=1 (only use every pixel), max_colors=128
        selected = Score.score(colors)
        return self.get_dynamicColorObject(selected[0], True, 0)

    def exportDynamicColorsFromImage(self, path: str) -> str:
        colors: dict = materialQuantize.ImageQuantizeCelebi(
            path, 1, 128
        )  # Get colors from image, quality=1 (only use every pixel), max_colors=128
        return json.dumps(colors)

    def loadDynamicColorsFromExport(self, export: str) -> DynamicScheme:
        colors: dict = json.loads(export)
        colors = {int(k): v for k, v in colors.items()}

        selected = Score.score(colors)
        return self.get_dynamicColorObject(selected[0], True, 0)

    def update_dynamicColors(self, colors: DynamicScheme):
        for attrName in vars(MaterialDynamicColors).keys():
            attr: DynamicColor = getattr(MaterialDynamicColors, attrName)
            if hasattr(attr, "get_hct"):
                # attr is now confirmed to be the color's name
                self.__setattr__(
                    "_" + attrName, rgba_to_hex(attr.get_hct(colors).to_rgba())
                )
        self.themeChanged.emit()

    def list_rgb_to_hex(self, color: list[int]) -> str:
        """Convert a list of rgb values to a hex string

        Args:
            color (list[int]): List of rgb values

        Returns:
            str: Hex string
        """
        return "#" + "".join(
            [hex(x)[2:].zfill(2) for x in color[:3]]
        )  # color[:3] because we don't need the alpha value

    @Property(str, notify=themeChanged)
    def primary_paletteKeyColor(self):
        return self._primary_paletteKeyColor

    @primary_paletteKeyColor.setter
    def primary_paletteKeyColor(self, value):
        self._primary_paletteKeyColor = value

    @Property(str, notify=themeChanged)
    def secondary_paletteKeyColor(self):
        return self._secondary_paletteKeyColor

    @secondary_paletteKeyColor.setter
    def secondary_paletteKeyColor(self, value):
        self._secondary_paletteKeyColor = value

    @Property(str, notify=themeChanged)
    def tertiary_paletteKeyColor(self):
        return self._tertiary_paletteKeyColor

    @tertiary_paletteKeyColor.setter
    def tertiary_paletteKeyColor(self, value):
        self._tertiary_paletteKeyColor = value

    @Property(str, notify=themeChanged)
    def neutral_paletteKeyColor(self):
        return self._neutral_paletteKeyColor

    @neutral_paletteKeyColor.setter
    def neutral_paletteKeyColor(self, value):
        self._neutral_paletteKeyColor = value

    @Property(str, notify=themeChanged)
    def neutral_variant_paletteKeyColor(self):
        return self._neutral_variant_paletteKeyColor

    @neutral_variant_paletteKeyColor.setter
    def neutral_variant_paletteKeyColor(self, value):
        self._neutral_variant_paletteKeyColor = value

    @Property(str, notify=themeChanged)
    def background(self):
        return self._background

    @background.setter
    def background(self, value):
        self._background = value

    @Property(str, notify=themeChanged)
    def onBackground(self):
        return self._onBackground

    @onBackground.setter
    def onBackground(self, value):
        self._onBackground = value

    @Property(str, notify=themeChanged)
    def surface(self):
        return self._surface

    @surface.setter
    def surface(self, value):
        self._surface = value

    @Property(str, notify=themeChanged)
    def surfaceDim(self):
        return self._surfaceDim

    @surfaceDim.setter
    def surfaceDim(self, value):
        self._surfaceDim = value

    @Property(str, notify=themeChanged)
    def surfaceBright(self):
        return self._surfaceBright

    @surfaceBright.setter
    def surfaceBright(self, value):
        self._surfaceBright = value

    @Property(str, notify=themeChanged)
    def surfaceContainerLowest(self):
        return self._surfaceContainerLowest

    @surfaceContainerLowest.setter
    def surfaceContainerLowest(self, value):
        self._surfaceContainerLowest = value

    @Property(str, notify=themeChanged)
    def surfaceContainerLow(self):
        return self._surfaceContainerLow

    @surfaceContainerLow.setter
    def surfaceContainerLow(self, value):
        self._surfaceContainerLow = value

    @Property(str, notify=themeChanged)
    def surfaceContainer(self):
        return self._surfaceContainer

    @surfaceContainer.setter
    def surfaceContainer(self, value):
        self._surfaceContainer = value

    @Property(str, notify=themeChanged)
    def surfaceContainerHigh(self):
        return self._surfaceContainerHigh

    @surfaceContainerHigh.setter
    def surfaceContainerHigh(self, value):
        self._surfaceContainerHigh = value

    @Property(str, notify=themeChanged)
    def surfaceContainerHighest(self):
        return self._surfaceContainerHighest

    @surfaceContainerHighest.setter
    def surfaceContainerHighest(self, value):
        self._surfaceContainerHighest = value

    @Property(str, notify=themeChanged)
    def onSurface(self):
        return self._onSurface

    @onSurface.setter
    def onSurface(self, value):
        self._onSurface = value

    @Property(str, notify=themeChanged)
    def surfaceVariant(self):
        return self._surfaceVariant

    @surfaceVariant.setter
    def surfaceVariant(self, value):
        self._surfaceVariant = value

    @Property(str, notify=themeChanged)
    def onSurfaceVariant(self):
        return self._onSurfaceVariant

    @onSurfaceVariant.setter
    def onSurfaceVariant(self, value):
        self._onSurfaceVariant = value

    @Property(str, notify=themeChanged)
    def inverseSurface(self):
        return self._inverseSurface

    @inverseSurface.setter
    def inverseSurface(self, value):
        self._inverseSurface = value

    @Property(str, notify=themeChanged)
    def inverseOnSurface(self):
        return self._inverseOnSurface

    @inverseOnSurface.setter
    def inverseOnSurface(self, value):
        self._inverseOnSurface = value

    @Property(str, notify=themeChanged)
    def outline(self):
        return self._outline

    @outline.setter
    def outline(self, value):
        self._outline = value

    @Property(str, notify=themeChanged)
    def outlineVariant(self):
        return self._outlineVariant

    @outlineVariant.setter
    def outlineVariant(self, value):
        self._outlineVariant = value

    @Property(str, notify=themeChanged)
    def shadow(self):
        return self._shadow

    @shadow.setter
    def shadow(self, value):
        self._shadow = value

    @Property(str, notify=themeChanged)
    def scrim(self):
        return self._scrim

    @scrim.setter
    def scrim(self, value):
        self._scrim = value

    @Property(str, notify=themeChanged)
    def surfaceTint(self):
        return self._surfaceTint

    @surfaceTint.setter
    def surfaceTint(self, value):
        self._surfaceTint = value

    @Property(str, notify=themeChanged)
    def primary(self):
        return self._primary

    @primary.setter
    def primary(self, value):
        self._primary = value

    @Property(str, notify=themeChanged)
    def onPrimary(self):
        return self._onPrimary

    @onPrimary.setter
    def onPrimary(self, value):
        self._onPrimary = value

    @Property(str, notify=themeChanged)
    def primaryContainer(self):
        return self._primaryContainer

    @primaryContainer.setter
    def primaryContainer(self, value):
        self._primaryContainer = value

    @Property(str, notify=themeChanged)
    def onPrimaryContainer(self):
        return self._onPrimaryContainer

    @onPrimaryContainer.setter
    def onPrimaryContainer(self, value):
        self._onPrimaryContainer = value

    @Property(str, notify=themeChanged)
    def inversePrimary(self):
        return self._inversePrimary

    @inversePrimary.setter
    def inversePrimary(self, value):
        self._inversePrimary = value

    @Property(str, notify=themeChanged)
    def secondary(self):
        return self._secondary

    @secondary.setter
    def secondary(self, value):
        self._secondary = value

    @Property(str, notify=themeChanged)
    def onSecondary(self):
        return self._onSecondary

    @onSecondary.setter
    def onSecondary(self, value):
        self._onSecondary = value

    @Property(str, notify=themeChanged)
    def secondaryContainer(self):
        return self._secondaryContainer

    @secondaryContainer.setter
    def secondaryContainer(self, value):
        self._secondaryContainer = value

    @Property(str, notify=themeChanged)
    def onSecondaryContainer(self):
        return self._onSecondaryContainer

    @onSecondaryContainer.setter
    def onSecondaryContainer(self, value):
        self._onSecondaryContainer = value

    @Property(str, notify=themeChanged)
    def tertiary(self):
        return self._tertiary

    @tertiary.setter
    def tertiary(self, value):
        self._tertiary = value

    @Property(str, notify=themeChanged)
    def onTertiary(self):
        return self._onTertiary

    @onTertiary.setter
    def onTertiary(self, value):
        self._onTertiary = value

    @Property(str, notify=themeChanged)
    def tertiaryContainer(self):
        return self._tertiaryContainer

    @tertiaryContainer.setter
    def tertiaryContainer(self, value):
        self._tertiaryContainer = value

    @Property(str, notify=themeChanged)
    def onTertiaryContainer(self):
        return self._onTertiaryContainer

    @onTertiaryContainer.setter
    def onTertiaryContainer(self, value):
        self._onTertiaryContainer = value

    @Property(str, notify=themeChanged)
    def error(self):
        return self._error

    @error.setter
    def error(self, value):
        self._error = value

    @Property(str, notify=themeChanged)
    def onError(self):
        return self._onError

    @onError.setter
    def onError(self, value):
        self._onError = value

    @Property(str, notify=themeChanged)
    def errorContainer(self):
        return self._errorContainer

    @errorContainer.setter
    def errorContainer(self, value):
        self._errorContainer = value

    @Property(str, notify=themeChanged)
    def onErrorContainer(self):
        return self._onErrorContainer

    @onErrorContainer.setter
    def onErrorContainer(self, value):
        self._onErrorContainer = value

    @Property(str, notify=themeChanged)
    def primaryFixed(self):
        return self._primaryFixed

    @primaryFixed.setter
    def primaryFixed(self, value):
        self._primaryFixed = value

    @Property(str, notify=themeChanged)
    def primaryFixedDim(self):
        return self._primaryFixedDim

    @primaryFixedDim.setter
    def primaryFixedDim(self, value):
        self._primaryFixedDim = value

    @Property(str, notify=themeChanged)
    def onPrimaryFixed(self):
        return self._onPrimaryFixed

    @onPrimaryFixed.setter
    def onPrimaryFixed(self, value):
        self._onPrimaryFixed = value

    @Property(str, notify=themeChanged)
    def onPrimaryFixedVariant(self):
        return self._onPrimaryFixedVariant

    @onPrimaryFixedVariant.setter
    def onPrimaryFixedVariant(self, value):
        self._onPrimaryFixedVariant = value

    @Property(str, notify=themeChanged)
    def secondaryFixed(self):
        return self._secondaryFixed

    @secondaryFixed.setter
    def secondaryFixed(self, value):
        self._secondaryFixed = value

    @Property(str, notify=themeChanged)
    def secondaryFixedDim(self):
        return self._secondaryFixedDim

    @secondaryFixedDim.setter
    def secondaryFixedDim(self, value):
        self._secondaryFixedDim = value

    @Property(str, notify=themeChanged)
    def onSecondaryFixed(self):
        return self._onSecondaryFixed

    @onSecondaryFixed.setter
    def onSecondaryFixed(self, value):
        self._onSecondaryFixed = value

    @Property(str, notify=themeChanged)
    def onSecondaryFixedVariant(self):
        return self._onSecondaryFixedVariant

    @onSecondaryFixedVariant.setter
    def onSecondaryFixedVariant(self, value):
        self._onSecondaryFixedVariant = value

    @Property(str, notify=themeChanged)
    def tertiaryFixed(self):
        return self._tertiaryFixed

    @tertiaryFixed.setter
    def tertiaryFixed(self, value):
        self._tertiaryFixed = value

    @Property(str, notify=themeChanged)
    def tertiaryFixedDim(self):
        return self._tertiaryFixedDim

    @tertiaryFixedDim.setter
    def tertiaryFixedDim(self, value):
        self._tertiaryFixedDim = value

    @Property(str, notify=themeChanged)
    def onTertiaryFixed(self):
        return self._onTertiaryFixed

    @onTertiaryFixed.setter
    def onTertiaryFixed(self, value):
        self._onTertiaryFixed = value

    @Property(str, notify=themeChanged)
    def onTertiaryFixedVariant(self):
        return self._onTertiaryFixedVariant

    @onTertiaryFixedVariant.setter
    def onTertiaryFixedVariant(self, value):
        self._onTertiaryFixedVariant = value
