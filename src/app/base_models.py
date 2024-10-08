from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt

import dataclasses

@dataclasses.dataclass
class listModelItem:
    thing: str = ""
    things: str = ""
    objects: str = ""
    multi: str = ""
    
class ListModel(QAbstractListModel):
    def __init__(self, contains = listModelItem):
        super().__init__()
        self._contentsList = []

        self.contains = contains
        
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if 0 <= index.row() < self.rowCount():
            item = self._contentsList[index.row()]
            name = self.roleNames().get(role)
            if name:
                return getattr(item, name.decode())

    def roleNames(self) -> dict[int, QByteArray]:
        d = {}
        for i, field in enumerate(dataclasses.fields(self.contains)):
            d[Qt.ItemDataRole.DisplayRole + i] = field.name.encode()
        return d

    def rowCount(self, parent=None):
        return len(self._contentsList)

    def addItem(self, item: object):
        self.beginInsertRows(QModelIndex(), 0, 0)
        self._contentsList.insert(0, item)
        self.endInsertRows()
    
    def removeItem(self, index: int):
        self.beginRemoveRows(QModelIndex(), index, index)
        self._contentsList.pop(index)
        self.endRemoveRows()
    
    def moveItem(self, fromIndex: int, toIndex: int):
        self.beginMoveRows(QModelIndex(), fromIndex, fromIndex, QModelIndex(), toIndex)
        self._contentsList.insert(toIndex, self._contentsList.pop(fromIndex))
        self.endMoveRows()
    
    def clear(self):
        self.beginResetModel()
        self._contentsList.clear()
        self.endResetModel()

    def count(self):
        return len(self._contentsList)

    