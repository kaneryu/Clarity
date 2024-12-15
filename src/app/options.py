from PySide6.QtCore import QObject, Qt, Slot, Property, Signal


class Settings(QObject):
    
    def __init__(self) -> None:
        super().__init__()
        self.createSettingProperty("cleanUi", False)
        
    @Slot()
    def loadSetings(self):
        raise NotImplementedError("loadSettings not implemented")
    
    @Slot()
    def saveSettings(self):
        raise NotImplementedError("saveSettings not implemented")
    
    def createSettingProperty(self, setting: str, default=None):
        self.__setattr__("_" + setting, default)
        self.__setattr__(setting + "Changed", Signal(str | int | float | bool))
        self.__setattr__(setting, Property(str | int | float | bool, self.getSetting(setting), self.setSetting(setting), notify=self.__getattribute__(setting + "Changed")))
    
    
    @Slot(str, result=None)
    def getSetting(self, setting: str):
        raise NotImplementedError("getSetting not implemented")

    @Slot(str, result=None)
    def setSetting(self, setting: str, value):
        raise NotImplementedError("setSetting not implemented")