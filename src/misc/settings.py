import json
import logging

from src.paths import Paths

from PySide6.QtCore import QObject, Qt, Property, Signal, Slot, QAbstractTableModel

f = open(Paths.VERSIONPATH, "r")
version = f.read().strip()
f.close()

default_settings = {
    "for": "",
    "settings": {
        "discordPresenceEnabled": {"value": False, "type": bool, 
                                   "description": "Enable Discord Rich Presence", "group": "Discord",
                                   "name": "Enable Discord Presence"},
        "discordClientId": {"value": "", "type": str,
                            "description": "Discord Client ID", "group": "Discord", "hidden": True,
                            "name": "Discord Client ID"},
    }
}

type_map = {
    "bool": bool,
    "str": str,
    "int": int,
    "float": float
}

def get_type(type: str) -> type:
    return type_map.get(type, str)

class Settings:
    def __init__(self, settings_file: str = Paths.SETTINGSPATH):
        if not isinstance(settings_file, str):
            raise TypeError("Settings file must be a string")
        
        self.logger = logging.getLogger("Settings")
        self.settings_file = settings_file
        self.settings: dict[str, dict] = {}
        self.settingObjects: dict[str, Setting] = {}
        self.groupKeyMap: dict[str, list[str]] = {}
        
        self.load()
    
    def load(self) -> None:
        try:
            with open(self.settings_file, "r") as f:
                self.settings = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load settings file: {e}")
        
        if not self.settings.get("for") or self.settings.get("for") != version:
            self.logger.warning("Settings file outdated")
            
        value: dict
        for key, value in self.settings.get("settings", {}).items():
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
            
            description = value.get("description", "")
            group = value.get("group")
            hidden = value.get("hidden", False)
            
            
            new = Setting(key=key, value=value_, type=type_, description=description, group=group, hidden=hidden, name=name)
            self.settingObjects[key] = new
            
            if group:
                if group not in self.groupKeyMap:
                    self.groupKeyMap[group] = []
                self.groupKeyMap[group].append(key)
            
    
    def save(self):
        settings_to_save = {"for": version, "settings": {}}
        for key, setting in self.settingObjects.items():
            settings_to_save["settings"][key] = { # type: ignore
            "value": setting.value,
            "type": setting.type.__name__,
            "description": setting.description,
            "group": setting.group,
            "hidden": setting.hidden,
            "name": setting.name
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

class Setting:
    def __init__(self, key: str, value, type: type, description: str, group: str | None = None, hidden: bool = False, name: str | None = None):
        if not isinstance(key, str):
            raise TypeError("Key must be a string")
        if not isinstance(description, str):
            raise TypeError("Description must be a string")
        if not isinstance(type, type):
            raise TypeError("Type must be a type")
        
        self.logger = logging.getLogger("Settings")
        
        self.key = key
        self.value = value
        self.type = type
        self.description = description
        self.group = group
        self.hidden = hidden
        self.name = name