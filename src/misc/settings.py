import json
import logging
from src.paths import Paths

import typing

# use dacite
from PySide6.QtCore import QObject, Qt, Property, Signal, Slot, QModelIndex, QPersistentModelIndex, QAbstractItemModel, QMutex, QMutexLocker, QMetaObject, QByteArray

ModelIndex = typing.Union[QModelIndex, QPersistentModelIndex]

f = open(Paths.VERSIONPATH, "r")
version = f.read().strip()
f.close()

default_settings = {
    "for": version,
    "settings": {
        "discordPresenceEnabled": {"value": False, "type": bool, 
                                   "description": "Enable Discord Rich Presence", "group": "Discord",
                                   "name": "Enable Discord Presence", "secure": False, "hidden": False},
        "discordClientId": {"value": "1221181347071000637", "type": str,
                            "description": "Discord Client ID", "group": "Discord", "hidden": True,
                            "name": "Discord Client ID", "secure": False},
        
        "youtubeHeaders": {"value": "", "type": str,
                           "description": "Input your YouTube headers here to login to YouTube. ", "group": "Login",
                            "name": "YouTube Headers", "secure": True, "hidden": False},
        "youtubeLoginEnabled": {"value": False, "type": bool,
                                "description": "Enable YouTube Login", "group": "Login",
                                "name": "Enable YouTube Login", "secure": False, "hidden": False},
        
        "lastFMEnabled": {"value": False, "type": bool,
                           "description": "Enable Last.fm Scrobbling", "group": "Last.fm",
                           "name": "Enable Last.fm Scrobbling", "secure": False, "hidden": False},
        "lastFMLogin": {"value": "$$SPECIAL_ACTION:lastFmOauthButton", "type": str,
                            "description": "Last.fm Login Button", "group": "Last.fm",
                            "name": "Last.fm Login Button", "secure": False, "hidden": False},
    }
}

default_rootItem = {
    "key": "root",
    "name": "Root",
    "value": "",
    "description": "Root settings item",
    "group": "",
    "type": "str",
    "hidden": True,
    "secure": False
}

settings_fields = {"value": str, "type": str, "description": str, "group": str, "hidden": bool, "name": str, "secure": bool}

type_map = {
    "bool": bool,
    "str": str,
    "int": int,
    "float": float
}

def get_type(type_: typing.Union[str, type]) -> type:
    if isinstance(type_, type):
        return type_
    if type_ in type_map:
        return type_map.get(type_, str)
    raise TypeError(f"Invalid type: {type_}, must be one of {list(type_map.keys())} or a valid type")
    

treeItemKeyMap: dict[str, "TreeItem"] = {}
keyIndexMap: dict[str, ModelIndex] = {}

class TreeItem(QObject):
    def __init__(self, data: "Setting", parent: typing.Union['TreeItem', None] = None):
        super().__init__()
        
        if not isinstance(data, Setting):
            raise TypeError("Data must be an instance of Setting")
        
        if not isinstance(parent, (TreeItem, type(None))):
            raise TypeError("Parent must be a TreeItem or None")
        
        # Include ALL fields that the model will try to access
        self.fields = ["key", "name", "value", "description", "group", "hidden", "type"]
        self.fields += ["secure"] if hasattr(data, "secure") else []
        
        # Define which fields are visible as columns
        self.display_fields = ["name"]
        
        self.item_data = data
        self.parent_item = parent
        self.child_items: list['TreeItem'] = []
        
        treeItemKeyMap[data.key] = self

    def child(self, number: int) -> typing.Union['TreeItem', None]:
        if number < 0 or number >= len(self.child_items):
            return None
        return self.child_items[number]

    def lastChild(self):
        return self.child_items[-1] if self.child_items else None

    def childCount(self) -> int:
        return len(self.child_items)

    def childNumber(self) -> int:
        if self.parent_item:
            return self.parent_item.child_items.index(self)
        return 0

    def columnCount(self) -> int:
        return len(self.display_fields)

    def data(self, column: int | str):
        if isinstance(column, str):
            # Remove the strict validation - let it fail gracefully
            return self.item_data.get(column, None)
        
        if column < 0 or column >= len(self.display_fields):
            return None
        field_name = self.display_fields[column]
        return self.item_data.get(field_name, None)
    
    def setData(self, column: int, value):
        if column < 0 or column >= len(self.fields):
            return False

        field_name = self.fields[column]
        self.item_data.set(field_name, value)
        return True

    def setValue(self, value):
        """Set the value of the setting."""
        self.item_data.set("value", value)
    
    def parent(self):
        return self.parent_item


    def __repr__(self) -> str:
        result = f"<treeitem.TreeItem at 0x{id(self):x}"
        for d in self.item_data.data.values():
            result += f' "{d}"' if d else " <None>"
        result += f", {len(self.child_items)} children>"
        return result
    
class SettingsModel(QAbstractItemModel):
    # Define role constants
    NameRole = Qt.ItemDataRole.UserRole + 1
    HiddenRole = Qt.ItemDataRole.UserRole + 2
    SecureRole = Qt.ItemDataRole.UserRole + 3
    ValueRole = Qt.ItemDataRole.EditRole
    TypeRole = Qt.ItemDataRole.UserRole + 5
    DescriptionRole = Qt.ItemDataRole.ToolTipRole
    GroupRole = Qt.ItemDataRole.UserRole + 7
    isGroupRole = Qt.ItemDataRole.UserRole + 8

    def __init__(self, settings: "Settings", parent: typing.Union[QObject, None] = None):
        super().__init__(parent)
        self.rootItem = TreeItem(Setting(data=default_rootItem))
    
    
    def get_item(self, index: ModelIndex) -> TreeItem:
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem
    
    def index(self, row: int, column: int, parent: ModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        
        parent_item = self.get_item(parent)    
        child_item = parent_item.child(row)
        
        return self.createIndex(row, column, child_item) if child_item else QModelIndex()
    
    def roleNames(self) -> dict[int, QByteArray]:
        roles = super().roleNames()
        roles[self.NameRole] = QByteArray(b"name")
        roles[self.HiddenRole] = QByteArray(b"hidden")
        roles[self.SecureRole] = QByteArray(b"secure")
        roles[self.ValueRole] = QByteArray(b"value")
        roles[self.TypeRole] = QByteArray(b"type")
        roles[self.DescriptionRole] = QByteArray(b"description")
        roles[self.GroupRole] = QByteArray(b"group")
        roles[self.isGroupRole] = QByteArray(b"isGroup")
        return roles
    
    def data(self, index: ModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> typing.Any:
        if not index.isValid():
            return None
            
        item = self.get_item(index)
        if not item:
            return None
        
        if role == Qt.ItemDataRole.DisplayRole:
            return item.data(index.column())
        elif role == self.NameRole:
            return item.data("name")
        elif role == self.HiddenRole:
            return item.data("hidden")
        elif role == self.SecureRole:
            return item.data("secure")
        elif role == Qt.ItemDataRole.EditRole or role == self.ValueRole:
            return item.data("value")
        elif role == self.TypeRole:
            # Return the type name as string for QML
            type_obj = item.data("type")
            return type_obj.__name__ if hasattr(type_obj, '__name__') else str(type_obj)
        elif role == self.DescriptionRole:
            return item.data("description")
        elif role == self.GroupRole:
            return item.data("group")
        elif role == self.isGroupRole:
            return item.data("group") == "isGroup"
        
        return None
    
    def flags(self, index: ModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        
        return Qt.ItemFlag.ItemIsEditable | QAbstractItemModel.flags(self, index)
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> typing.Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section < self.rootItem.columnCount():
                return self.rootItem.display_fields[section].capitalize()
        
        return None
    
    def parent(self, child: ModelIndex) -> QModelIndex: # type: ignore
        if not child.isValid():
            return QModelIndex()
        
        item = self.get_item(child)
        parent_item = item.parent()
        
        if parent_item == self.rootItem or not parent_item:
            return QModelIndex()
        
        return self.createIndex(parent_item.childNumber(), 0, parent_item)
    
    def rootIndex(self) -> QModelIndex:
        return self.createIndex(0, 0, self.rootItem) if self.rootItem else QModelIndex()
    
    def rowCount(self, parent: ModelIndex = QModelIndex()) -> int:
        if parent.isValid() and parent.column() != 0:
            return 0
        parent_item = self.get_item(parent)
        if parent_item:
            return parent_item.childCount()
        
        return parent_item.child_count() if parent_item else 0
    
    def columnCount(self, parent: ModelIndex = QModelIndex()) -> int:
        return self.rootItem.columnCount()
    
    def setData(self, index: ModelIndex, value: typing.Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False

        item = self.get_item(index)
        
        # qt may return everything as a string, so we need to convert it to the correct type
        try:
            type_ = item.data("type")
            if isinstance(type_, str):
                type_ = get_type(type_)
            value = value if not isinstance(value, str) else type_(value)
        except Exception as e:
            logging.error(f"Failed to convert value {value} to type {item.data('type')}: {e}")

        if role == Qt.ItemDataRole.EditRole:
            if not item.setValue(value):
                return False
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole, self.ValueRole])
            return True
        elif role == self.ValueRole:
            if not item.setData(self.rootItem.fields.index("value"), value):
                 return False
            # Find the index for the 'value' column to emit dataChanged correctly
            value_col_idx = -1
            try:
                value_col_idx = self.rootItem.display_fields.index("value")
            except ValueError:
                pass # 'value' column is not visible

            if value_col_idx != -1:
                value_index = self.index(index.row(), value_col_idx, self.parent(index))
                self.dataChanged.emit(value_index, value_index, [Qt.ItemDataRole.EditRole, self.ValueRole])
            return True
        
        child = self.get_item(index)
        if not child:
            return False
        
        # In a tree view, setData is typically for column 0.
        # The role determines what data is being set, based on the enum value.
        if not child.setData(index.column(), value):
            return False
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
        return True
    
    def resetModel(self, rootItem: typing.Optional[TreeItem] = None) -> None:
        self.beginResetModel()
        self.rootItem = rootItem if rootItem else TreeItem(Setting(data=default_rootItem))
        self.endResetModel()
            
class Settings(QObject):
    _instance: typing.Union["Settings", None] = None
    
    settingChanged = Signal()  # Signal to notify that a setting has changed
    
    @classmethod
    def instance(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __new__(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, settings_file: str = Paths.SETTINGSPATH):
        if not isinstance(settings_file, str):
            raise TypeError("Settings file must be a string")
        
        if hasattr(self, 'initialized'):
            return  # Prevent re-initialization
        
        super().__init__()
        self.initialized = True
        
        self.logger = logging.getLogger("Settings")
        self.settings_file = settings_file
        self.settings: dict[str, typing.Any] = {}
        self.settingObjects: dict[str, Setting] = {}
        self.groupKeyMap: dict[str, list[str]] = {}
        
        self.settingsModel = SettingsModel(self)
        
        
        self.load()
    
    def load(self) -> None:
        try:
            with open(self.settings_file, "r") as f:
                self.settings = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load settings file: {e}")
            self.settings = default_settings
        
        if not self.settings.get("for") or self.settings.get("for") != version:
            self.logger.warning("Settings file outdated")
            
        value: dict
        for key, value in self.settings.get("settings", {}).items(): # type: ignore
            name = value.get("name")
            value_ = value.get("value")
            type_ = value.get("type", "")
            
            try:
                type_ = get_type(type_)
            except Exception as e:
                self.logger.error(f"Setting {name} has invalid type: {e}, Inferring type...")
                type_ = type(value_)
            
            if not isinstance(value_, type_):
                self.logger.error(f"Setting {name}'s type is supposed to be {type_}, but it is {type(value_)}, skipping...")
                continue
            
            group = value.get("group")
            
            value["key"] = key
            
            new = Setting(data = value)
            self.settingObjects[key] = new
            
            if group:
                if group not in self.groupKeyMap:
                    self.groupKeyMap[group] = []
                self.groupKeyMap[group].append(key)
                
        newroot = self.createModel()
        self.settingsModel.resetModel(newroot)
        self.logger.info("Settings loaded successfully")
    
    def createModel(self) -> TreeItem:
        rootItem = TreeItem(Setting(data=default_rootItem))
        x = 0
        for group, keys in self.groupKeyMap.items():
            groupItem = TreeItem(Setting(data={
                "key": group + "_group",
                "name": group + "_group",
                "value": "",
                "description": f"Settings for {group}",
                "group": "isGroup",
                "type": "str",
                "hidden": True,
                "secure": False
            }), parent=rootItem)
            groupIndex = self.settingsModel.index(0, 0, QModelIndex())
            keyIndexMap.update({group + "_group": groupIndex})
            
            for key in keys:
                item = TreeItem(self.settingObjects[key], parent=groupItem)
                groupItem.child_items.append(item)
                keyIndexMap[key] = self.settingsModel.index(x, 0, groupIndex)
            x += 1
            rootItem.child_items.append(groupItem)
        return rootItem
    
    def getModel(self) -> SettingsModel:
        return self.settingsModel            
    
    def save(self):
        settings_to_save = {"for": version, "settings": {}}
        for key, setting in self.settingObjects.items():
            settings_to_save["settings"][key] = { # type: ignore
            "value": setting.value,
            "type": setting.type.__name__,
            "description": setting.description,
            "group": setting.group,
            "hidden": setting.hidden,
            "name": setting.name,
            "secure": getattr(setting, "secure", False)  # Add secure field if it exists
            }
        
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings_to_save, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save settings file: {e}")
    
    def get(self, key: str, default=None):
        setting = self.settingObjects.get(key)
        if not setting:
            return default
        
        return setting.value
    
    def set(self, key: str, value):
        setting = self.settingObjects.get(key)
        if not setting:
            return
        
        if not isinstance(value, setting.type):
            self.logger.error(f"Setting {setting.name} is supposed to be of type {setting.type}, but it is {type(value)}, skipping...")
            return
        
        setting.value = value
        self.save()

class QmlSettingsInterface(QObject):
    _instance: typing.Union["QmlSettingsInterface", None] = None
    _is_initialized = False


    def __init__(self, settings: Settings, parent: QObject | None = None):
        # Ensure __init__ runs only once
        if self._is_initialized:
            return
        super().__init__(parent)
        self.settings = settings
        self.model = settings.getModel()
        self._is_initialized = True

    @classmethod
    def instance(cls) -> "QmlSettingsInterface":
        """Gets the singleton instance, creating it if necessary."""
        if cls._instance is None:
            # Pass the required arguments for the first-time initialization
            cls._instance = QmlSettingsInterface(settings=Settings.instance())
        return cls._instance

    @Slot(str, result=typing.Any)
    def get(self, key: str, default=None) -> typing.Any:
        """Get a setting value by key."""
        return self.settings.get(key, default)
    
    @Slot(str)
    def set(self, key: str, value) -> None:
        """Set a setting value by key."""
        self.settings.set(key, value)
    
    @Slot(str, result=QObject)
    def getSettingsObjectByKey(self, key: str) -> QObject:
        """Get a setting object by key."""
        setting = self.settings.settingObjects.get(key, QObject())
        return setting
    
    @Slot(str, result=QObject)
    def getSettingsObjectByName(self, name: str) -> QObject:
        """Get a setting object by name."""
        for setting in self.settings.settingObjects.values():
            if setting.name == name:
                return setting
        raise KeyError(f"No setting found with name: {name}")

    @Slot(str, result=str)
    def nameToKey(self, name: str) -> str:
        """Convert a setting name to its key."""
        for key, setting in self.settings.settingObjects.items():
            if setting.name == name:
                return key
        raise KeyError(f"No setting found with name: {name}")

class Setting(QObject):
    dataChanged = Signal(str, object)
    valueChanged = Signal()
    
    def __init__(self, data: dict):
        super().__init__()
        if data.get("settings") is not None:
            raise TypeError("Data must be a single setting, not a settings dictionary")
        if not isinstance(data["key"], str):
            raise TypeError("Key must be a string" + "\n" + str(data))
        if not isinstance(data["description"], str):
            raise TypeError("Description must be a string")
        
        self.logger = logging.getLogger("Settings")
        
        self.protectedFields = ["key", "name", "value", "description", "group", "hidden", "type", "secure"]
        
        self.data = data
        self.key = data["key"]
        self.value = data["value"]
        self.type = data["type"]
        self.description = data["description"]
        self.group = data["group"]
        self.hidden = data.get("hidden", False)  # Add hidden field if it exists
        self.name = data["name"]
        self.secure = data.get("secure", False)  # Add secure field if it exists
        
        self.valueProperty = Property(get_type(self.type), self.get, self.set, notify=self.dataChanged) # type: ignore
        
    
    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value):
        if key not in self.data:
            self.logger.error(f"Setting {self.key} does not have key {key}, skipping...")
            return
        
        if isinstance(value, int) and get_type(self.type) == float:
            value = float(value)
        
        if isinstance(value, int) and get_type(self.type) == bool:
            value = value == 1
        
        if not isinstance(value, get_type(self.type)):
            self.logger.error(f"Setting {self.key} is supposed to be of type {self.type}, but it is {type(value)} ({value}), skipping...")
            return
        
        self.logger.info(f"Setting '{key}' on {self.key} to {value}")
        self.data[key] = value
        self.__setattr__(key, value)
        self.dataChanged.emit(key, value)
        if key == "value":
            self.valueChanged.emit()
    
    def setValue(self, value):
        """Set the value of the setting."""
        Settings.instance().settingChanged.emit()
                # find the index of the 'value' column in the model
        model = Settings.instance().getModel()
        index = keyIndexMap.get(self.key)
        if index:
            value_col_idx = 0 # value isn't a display field, just say the first column was changed
            value_index = model.index(index.row(), value_col_idx, model.parent(index))
            model.dataChanged.emit(value_index, value_index, [Qt.ItemDataRole.EditRole, model.ValueRole])
        self.set("value", value)
    
    def setValue_model(self, value):
        """Set the value of the setting in the model."""
        self.set("value", value)
        


def getSetting(key: str) -> Setting:
    """Get a setting by key."""
    setting = Settings.instance().settingObjects.get(key)
    if not setting:
        raise KeyError(f"No setting found with key: {key}")
    return setting 