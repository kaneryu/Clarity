import json
import logging
from src.paths import Paths
import os

import typing

# use dacite
from PySide6.QtCore import QObject, Qt, Property, Signal, Slot, QModelIndex, QPersistentModelIndex, QAbstractItemModel, QMutex, QMutexLocker, QMetaObject, QByteArray

ModelIndex = typing.Union[QModelIndex, QPersistentModelIndex]

f = open(Paths.VERSIONPATH, "r")
version = f.read().strip()
f.close()

default_settings_file = open(os.path.join(Paths.ASSETSPATH, "DEFAULTSETTINGS.json"))
defaultSettings: dict[str, str | dict] = json.loads(default_settings_file.read())
default_settings_file.close()

defaultSettings["for"] = version

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
    # UI/control types
    "switch": bool,
    "textEdit": str,
    "dropdown": str,
    # Back-compat literal types (legacy)
    "bool": bool,
    "str": str,
    "int": int,
    "float": float,
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
    DropdownOptionsRole = Qt.ItemDataRole.UserRole + 9
    VisualDropdownOptionsRole = Qt.ItemDataRole.UserRole + 10

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
        roles[self.DropdownOptionsRole] = QByteArray(b"dropdownOptions")
        roles[self.VisualDropdownOptionsRole] = QByteArray(b"visualDropdownOptions")
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
            # Return the declared UI/control type string as-is (e.g., "switch", "dropdown", "textEdit")
            return item.data("type")
        elif role == self.DescriptionRole:
            return item.data("description")
        elif role == self.GroupRole:
            return item.data("group")
        elif role == self.isGroupRole:
            return item.data("group") == "isGroup"
        elif role == self.DropdownOptionsRole:
            return item.data("dropdownOptions") or []
        elif role == self.VisualDropdownOptionsRole:
            # Fallback to dropdownOptions for display if visual labels aren't provided
            return item.data("visualDropdownOptions") or item.data("dropdownOptions") or []
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
        
        return 0
    
    def columnCount(self, parent: ModelIndex = QModelIndex()) -> int:
        return self.rootItem.columnCount()
    
    def setData(self, index: ModelIndex, value: typing.Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False

        item = self.get_item(index)
        
        # Convert to the underlying value type
        try:
            declared_type = item.data("type")  # "switch", "textEdit", "dropdown"
            py_type = get_type(declared_type)
            if declared_type == "dropdown":
                options = item.data("dropdownOptions") or []
                if value not in options:
                    logging.error(f"Dropdown value '{value}' not in allowed options {options}")
                    return False
            if isinstance(value, str) and py_type is not str:
                # Cast only if needed; checkbox sends bool already, combo sends str
                value = py_type(value)
        except Exception as e:
            logging.error(f"Failed to convert value {value} for type {item.data('type')}: {e}")

        if role in (Qt.ItemDataRole.EditRole, self.ValueRole):
            if not item.setValue(value):
                return False
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole, self.ValueRole])
            return True
        
        child = self.get_item(index)
        if not child:
            return False

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
    
    settingChanged = Signal()  # Signal to notify that a setting has changed'
    
    
    @staticmethod
    def cleanSettingsForSaving(settings: dict) -> dict:
        # for now, resolve all types to their string names
        
        cleaned_settings = settings.copy()
        for setting in cleaned_settings:
            setting[type] = get_type(setting["type"]).__name__
        
        return cleaned_settings
        
    @staticmethod
    def unpackSettingsForLoading(settings: dict) -> dict:
        # for now, resolve string types to their actual types
        unpacked_settings = settings.copy()
        for setting in unpacked_settings:
            setting["type"] = get_type(setting["type"])
        return unpacked_settings
    
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
        self.settingsDict: dict[str, typing.Any] = {}
        self.settingObjects: dict[str, Setting] = {}
        self.groupKeyMap: dict[str, list[str]] = {}
        
        self.settingsModel = SettingsModel(self)
        
        
        self.load()
    
    def load(self) -> None:
        try:
            with open(self.settings_file, "r") as f:
                self.settingsDict = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load settings file: {e}")
            self.settingsDict = {}

        # Always start from defaults to preserve metadata like dropdownOptions
        defaultSettingsDictSettings: dict = typing.cast(dict, defaultSettings.get("settings", {}))
        savedSettings: dict = typing.cast(dict, (self.settingsDict or {}).get("settings", {}))

        merged_settings: dict[str, dict] = {}
        for key, default_entry in defaultSettingsDictSettings.items():
            entry = dict(default_entry)  # shallow copy; values are primitives/lists
            saved_entry = savedSettings.get(key, {})
            if isinstance(saved_entry, dict) and "value" in saved_entry:
                entry["value"] = saved_entry["value"]
            merged_settings[key] = entry

        if not self.settingsDict.get("for") or self.settingsDict.get("for") != version:
            self.logger.warning("Settings file outdated")

        # Rebuild internal maps
        self.settingObjects.clear()
        self.groupKeyMap.clear()

        for key, value in merged_settings.items():
            name = value.get("name")
            value_ = value.get("value")
            declared_type = value.get("type", "textEdit")

            # Validate basic underlying type using the mapping
            try:
                base_type = get_type(declared_type)
            except Exception as e:
                self.logger.error(f"Setting {name} has invalid type '{declared_type}': {e}, inferring from current value...")
                base_type = type(value_)

            # Coerce some common mismatches
            if base_type is float and isinstance(value_, int):
                value_ = float(value_)
            if base_type is bool and isinstance(value_, int):
                value_ = value_ == 1

            # Enforce dropdown membership
            if declared_type == "dropdown":
                options = value.get("dropdownOptions") or []
                if value_ not in options and options:
                    self.logger.warning(f"'{name}' value '{value_}' not in {options}, defaulting to first option.")
                    value_ = options[0]
                value["value"] = value_

            # Create Setting object
            value["key"] = key
            new = Setting(data=value)
            self.settingObjects[key] = new

            group = value.get("group")
            if group:
                self.groupKeyMap.setdefault(group, []).append(key)

        newroot = self.createModel()
        self.settingsModel.resetModel(newroot)
        self.logger.info("Settings loaded successfully")
        self.save()
    
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
            out = {
                "value": setting.value,
                "type": setting.type,
                "description": setting.description,
                "group": setting.group,
                "hidden": setting.hidden,
                "name": setting.name,
                "secure": getattr(setting, "secure", False),
            }
            # Preserve dropdownOptions if present so UI has data even without defaults
            if getattr(setting, "dropdownOptions", None):
                out["dropdownOptions"] = setting.dropdownOptions
            # Preserve visualDropdownOptions if present so UI labels remain available
            if getattr(setting, "visualDropdownOptions", None):
                out["visualDropdownOptions"] = setting.visualDropdownOptions
            settings_to_save["settings"][key] = out  # type: ignore

        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings_to_save, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save settings file: {e}")
    
    def get(self, key: str, default=None) -> typing.Any:
        setting = self.getSettingObject(key)
        if not setting:
            return default
        
        return setting.value
    
    def getSettingObject(self, key: str) -> typing.Union["Setting", None]:
        setting = self.settingObjects.get(key)
        if not setting:
            return None
        
        return setting
    
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
    
    @Slot(str, object)
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
        
        self.protectedFields = [
            "key", "name", "value", "description", "group", "hidden",
            "type", "secure", "dropdownOptions", "visualDropdownOptions"
        ]

        self.data = data
        self.key = data["key"]
        self.value = data["value"]
        self.type = data["type"]  # UI/control type string
        self.description = data["description"]
        self.group = data["group"]
        self.hidden = data.get("hidden", False)
        self.name = data["name"]
        self.secure = data.get("secure", False)
        self.dropdownOptions = data.get("dropdownOptions", None)
        self.visualDropdownOptions = data.get("visualDropdownOptions", None)

        # Underlying value type is derived from UI/control type
        self.valueProperty = Property(get_type(self.type), self.get, self.set, notify=self.dataChanged)  # type: ignore

    
    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value):
        if key not in self.data:
            self.logger.error(f"Setting {self.key} does not have key {key}, skipping...")
            return

        # Normalize to underlying base type
        base_type = get_type(self.type)

        if isinstance(value, int) and base_type == float:
            value = float(value)
        if isinstance(value, int) and base_type == bool:
            value = value == 1

        # Enforce dropdown options
        if self.type == "dropdown":
            options = self.data.get("dropdownOptions") or []
            if value not in options:
                self.logger.error(f"Setting {self.key} only accepts one of {options}, got '{value}', skipping...")
                return

        if not isinstance(value, base_type):
            self.logger.error(f"Setting {self.key} expects {base_type}, got {type(value)} ({value}), skipping...")
            return

        self.logger.info(f"Setting '{key}' on {self.key} to {value}")
        self.data[key] = value
        self.__setattr__(key, value)
        self.dataChanged.emit(key, value)
        if key == "value":
            self.valueChanged.emit()

        Settings.instance().save()
    
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