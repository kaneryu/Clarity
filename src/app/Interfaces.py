"""This module contains the interfaces for the QML objects to interact with the Python objects.
These are read only interfaces, and may not implement all functions (thoguh they should implement all properties).

You should be able to use the objects direcly in python as it seems that python interacts with different-threaded QObjects just fine.

Depreciated in already in 2 commits, lol
"""

# stdlib imports
import json
import inspect
import enum

# library imports
from PySide6.QtCore import (
    QObject,
)

from PySide6.QtCore import Signal as Signal
from PySide6.QtCore import Slot as Slot
from PySide6.QtQml import (
    QmlElement,
)
from PySide6.QtCore import Property as QProperty, QMetaMethod, QMetaObject, Qt, QAbstractListModel

import src.universal as universal

class FwdVar:
    def __init__(self, getvar):
        self.var = getvar
        
    def __repr__(self):
        return self.var()
    
    def __str__(self):
        if isinstance(self.var(), str):
            return self.var()
        else:
            try:
                return str(self.var())
            except:
                return ""
            
