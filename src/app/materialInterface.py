from materialyoucolor.dynamiccolor.material_dynamic_colors import MaterialDynamicColors
from materialyoucolor.hct import Hct
from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot
from PySide6.QtCore import QObject, Qt, Slot, Property, Signal

import json
import src.app.baseModels as baseModels
import dataclasses

class Theme(QObject):
    themeChanged = Signal(name="themeChanged")
    
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

    @Slot(result=str)
    def getAllColors(self):
        retlist = []
        for color in vars(MaterialDynamicColors).keys():
            color_name = getattr(MaterialDynamicColors, color)
            if hasattr(color_name, "get_hct"):
                retlist.append({color: str(eval(f"self.{color}"))})
                print(retlist[-1])
                
        return json.dumps(retlist)

    @Slot(result=baseModels.ListModel)
    def getAllColorsAsModel(self):
        retdict = {}
        for color in vars(MaterialDynamicColors).keys():
            color_name = getattr(MaterialDynamicColors, color)
            if hasattr(color_name, "get_hct"):
                retdict[color] = eval(f"self.{color}")
               
        @dataclasses.dataclass 
        class Color:
            name: str
            color: str
            
        model = baseModels.ListModel(Color)
        for k,v in retdict.items():
            model.addItem(Color(k, v))
        
        print(model.count())
        print(model.data(model.index(0)))
        return model
            
    @Property(str, notify=themeChanged)
    def primary_paletteKeyColor(self):
        return self._primary_paletteKeyColor

    @primary_paletteKeyColor.setter
    def primary_paletteKeyColor(self, value):
        self._primary_paletteKeyColor = value
        self.themeChanged.emit()

    @Property(str, notify=themeChanged)
    def secondary_paletteKeyColor(self):
        return self._secondary_paletteKeyColor

    @secondary_paletteKeyColor.setter
    def secondary_paletteKeyColor(self, value):
        self._secondary_paletteKeyColor = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def tertiary_paletteKeyColor(self):
        return self._tertiary_paletteKeyColor

    @tertiary_paletteKeyColor.setter
    def tertiary_paletteKeyColor(self, value):
        self._tertiary_paletteKeyColor = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def neutral_paletteKeyColor(self):
        return self._neutral_paletteKeyColor

    @neutral_paletteKeyColor.setter
    def neutral_paletteKeyColor(self, value):
        self._neutral_paletteKeyColor = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def neutral_variant_paletteKeyColor(self):
        return self._neutral_variant_paletteKeyColor

    @neutral_variant_paletteKeyColor.setter
    def neutral_variant_paletteKeyColor(self, value):
        self._neutral_variant_paletteKeyColor = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def background(self):
        return self._background

    @background.setter
    def background(self, value):
        self._background = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onBackground(self):
        return self._onBackground

    @onBackground.setter
    def onBackground(self, value):
        self._onBackground = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def surface(self):
        return self._surface

    @surface.setter
    def surface(self, value):
        self._surface = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def surfaceDim(self):
        return self._surfaceDim

    @surfaceDim.setter
    def surfaceDim(self, value):
        self._surfaceDim = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def surfaceBright(self):
        return self._surfaceBright

    @surfaceBright.setter
    def surfaceBright(self, value):
        self._surfaceBright = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def surfaceContainerLowest(self):
        return self._surfaceContainerLowest

    @surfaceContainerLowest.setter
    def surfaceContainerLowest(self, value):
        self._surfaceContainerLowest = value
        self.themeChanged.emit()

    @Property(str, notify=themeChanged)
    def surfaceContainerLow(self):
        return self._surfaceContainerLow

    @surfaceContainerLow.setter
    def surfaceContainerLow(self, value):
        self._surfaceContainerLow = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def surfaceContainer(self):
        return self._surfaceContainer

    @surfaceContainer.setter
    def surfaceContainer(self, value):
        self._surfaceContainer = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def surfaceContainerHigh(self):
        return self._surfaceContainerHigh

    @surfaceContainerHigh.setter
    def surfaceContainerHigh(self, value):
        self._surfaceContainerHigh = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def surfaceContainerHighest(self):
        return self._surfaceContainerHighest

    @surfaceContainerHighest.setter
    def surfaceContainerHighest(self, value):
        self._surfaceContainerHighest = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onSurface(self):
        return self._onSurface

    @onSurface.setter
    def onSurface(self, value):
        self._onSurface = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def surfaceVariant(self):
        return self._surfaceVariant

    @surfaceVariant.setter
    def surfaceVariant(self, value):
        self._surfaceVariant = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onSurfaceVariant(self):
        return self._onSurfaceVariant

    @onSurfaceVariant.setter
    def onSurfaceVariant(self, value):
        self._onSurfaceVariant = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def inverseSurface(self):
        return self._inverseSurface

    @inverseSurface.setter
    def inverseSurface(self, value):
        self._inverseSurface = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def inverseOnSurface(self):
        return self._inverseOnSurface

    @inverseOnSurface.setter
    def inverseOnSurface(self, value):
        self._inverseOnSurface = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def outline(self):
        return self._outline

    @outline.setter
    def outline(self, value):
        self._outline = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def outlineVariant(self):
        return self._outlineVariant

    @outlineVariant.setter
    def outlineVariant(self, value):
        self._outlineVariant = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def shadow(self):
        return self._shadow

    @shadow.setter
    def shadow(self, value):
        self._shadow = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def scrim(self):
        return self._scrim

    @scrim.setter
    def scrim(self, value):
        self._scrim = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def surfaceTint(self):
        return self._surfaceTint

    @surfaceTint.setter
    def surfaceTint(self, value):
        self._surfaceTint = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def primary(self):
        return self._primary

    @primary.setter
    def primary(self, value):
        self._primary = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onPrimary(self):
        return self._onPrimary

    @onPrimary.setter
    def onPrimary(self, value):
        self._onPrimary = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def primaryContainer(self):
        return self._primaryContainer

    @primaryContainer.setter
    def primaryContainer(self, value):
        self._primaryContainer = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onPrimaryContainer(self):
        return self._onPrimaryContainer

    @onPrimaryContainer.setter
    def onPrimaryContainer(self, value):
        self._onPrimaryContainer = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def inversePrimary(self):
        return self._inversePrimary

    @inversePrimary.setter
    def inversePrimary(self, value):
        self._inversePrimary = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def secondary(self):
        return self._secondary

    @secondary.setter
    def secondary(self, value):
        self._secondary = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onSecondary(self):
        return self._onSecondary

    @onSecondary.setter
    def onSecondary(self, value):
        self._onSecondary = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def secondaryContainer(self):
        return self._secondaryContainer

    @secondaryContainer.setter
    def secondaryContainer(self, value):
        self._secondaryContainer = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onSecondaryContainer(self):
        return self._onSecondaryContainer

    @onSecondaryContainer.setter
    def onSecondaryContainer(self, value):
        self._onSecondaryContainer = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def tertiary(self):
        return self._tertiary

    @tertiary.setter
    def tertiary(self, value):
        self._tertiary = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onTertiary(self):
        return self._onTertiary

    @onTertiary.setter
    def onTertiary(self, value):
        self._onTertiary = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def tertiaryContainer(self):
        return self._tertiaryContainer

    @tertiaryContainer.setter
    def tertiaryContainer(self, value):
        self._tertiaryContainer = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onTertiaryContainer(self):
        return self._onTertiaryContainer

    @onTertiaryContainer.setter
    def onTertiaryContainer(self, value):
        self._onTertiaryContainer = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def error(self):
        return self._error

    @error.setter
    def error(self, value):
        self._error = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onError(self):
        return self._onError

    @onError.setter
    def onError(self, value):
        self._onError = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def errorContainer(self):
        return self._errorContainer

    @errorContainer.setter
    def errorContainer(self, value):
        self._errorContainer = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onErrorContainer(self):
        return self._onErrorContainer

    @onErrorContainer.setter
    def onErrorContainer(self, value):
        self._onErrorContainer = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def primaryFixed(self):
        return self._primaryFixed

    @primaryFixed.setter
    def primaryFixed(self, value):
        self._primaryFixed = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def primaryFixedDim(self):
        return self._primaryFixedDim

    @primaryFixedDim.setter
    def primaryFixedDim(self, value):
        self._primaryFixedDim = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onPrimaryFixed(self):
        return self._onPrimaryFixed

    @onPrimaryFixed.setter
    def onPrimaryFixed(self, value):
        self._onPrimaryFixed = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onPrimaryFixedVariant(self):
        return self._onPrimaryFixedVariant

    @onPrimaryFixedVariant.setter
    def onPrimaryFixedVariant(self, value):
        self._onPrimaryFixedVariant = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def secondaryFixed(self):
        return self._secondaryFixed

    @secondaryFixed.setter
    def secondaryFixed(self, value):
        self._secondaryFixed = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def secondaryFixedDim(self):
        return self._secondaryFixedDim

    @secondaryFixedDim.setter
    def secondaryFixedDim(self, value):
        self._secondaryFixedDim = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onSecondaryFixed(self):
        return self._onSecondaryFixed

    @onSecondaryFixed.setter
    def onSecondaryFixed(self, value):
        self._onSecondaryFixed = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onSecondaryFixedVariant(self):
        return self._onSecondaryFixedVariant

    @onSecondaryFixedVariant.setter
    def onSecondaryFixedVariant(self, value):
        self._onSecondaryFixedVariant = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def tertiaryFixed(self):
        return self._tertiaryFixed

    @tertiaryFixed.setter
    def tertiaryFixed(self, value):
        self._tertiaryFixed = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def tertiaryFixedDim(self):
        return self._tertiaryFixedDim

    @tertiaryFixedDim.setter
    def tertiaryFixedDim(self, value):
        self._tertiaryFixedDim = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onTertiaryFixed(self):
        return self._onTertiaryFixed

    @onTertiaryFixed.setter
    def onTertiaryFixed(self, value):
        self._onTertiaryFixed = value
        self.themeChanged.emit()




    @Property(str, notify=themeChanged)
    def onTertiaryFixedVariant(self):
        return self._onTertiaryFixedVariant

    @onTertiaryFixedVariant.setter
    def onTertiaryFixedVariant(self, value):
        self._onTertiaryFixedVariant = value
        self.themeChanged.emit()

    @Slot(str, result=str)
    def getColor(self, color: str) -> str:
        """Get color from color name

        Args:
            color (str): Name of color

        Returns:
            str: Hex value of color
        """
        return getattr(self, color)
    
    def get_dynamicColors(self, source: int, dark: bool, contrast: float) -> SchemeTonalSpot:
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
            
        scheme = SchemeTonalSpot( # choose any scheme here
            
            Hct.from_int(source), # source color in hct form
            dark, # dark mode
            contrast, # contrast
        )
        
        for color in vars(MaterialDynamicColors).keys():
            color_name = getattr(MaterialDynamicColors, color)
            if hasattr(color_name, "get_hct"): # is a color
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
                    self.__setattr__(color, self.list_rgb_to_hex(color_name.get_hct(scheme).to_rgba())) # set attribute of color name to its value in rgba format
                else:
                    exec(f"self.{color} = self.list_rgb_to_hex(color_name.get_hct(scheme).to_rgba())")

    def list_rgb_to_hex(self, color: list[int]) -> str:
        """Convert a list of rgb values to a hex string

        Args:
            color (list[int]): List of rgb values

        Returns:
            str: Hex string
        """
        return "#" + "".join([hex(x)[2:].zfill(2) for x in color[:3]]) # color[:3] because we don't need the alpha value