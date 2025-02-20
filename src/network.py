from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtCore import QUrl, QIODevice, QByteArray, Signal, Slot, QObject

class CustomAccessManager(QNetworkAccessManager):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.replyStorage = {}

    @Slot(QNetworkRequest, result=QNetworkReply)
    def get(self, request: QNetworkRequest, id: str) -> QNetworkReply:
        reply = super().get(request)
        self.replyStorage[id] = reply
        return reply
    
    @Slot(str, result=QNetworkReply)
    def getReply(self, id: str) -> QNetworkReply:
        rq = self.replyStorage.get(id)
        if rq is None:
            return None
        self.replyStorage.pop(id)
        return rq

    def clearStorage(self):
        self.replyStorage.clear()

accessManager = CustomAccessManager()
