import logging
import typing
import time
import queue
import random
from datetime import datetime, timezone
import json

from PySide6.QtCore import (
    Qt,
    QObject,
    Signal,
    Slot,
    QAbstractListModel,
    QModelIndex,
    QPersistentModelIndex,
    QTimer,
)
import threading

ModelIndex = typing.Union[QModelIndex, QPersistentModelIndex]

completeHistory: list = []


class LogHistoryModel(QAbstractListModel):

    roles = {
        "time": Qt.ItemDataRole.UserRole + 1,
        "name": Qt.ItemDataRole.UserRole + 2,
        "level": Qt.ItemDataRole.UserRole + 3,
        "message": Qt.ItemDataRole.DisplayRole,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        # example log dict:
        # log = {
        #     "time": "2023-10-01 12:00:00",
        #     "name": "my_logger",
        #     "level": "INFO",
        #     "message": "This is a log message"
        # }
        self._logs = []
        self.columns_ = ["time", "name", "level", "message"]

    def rowCount(self, parent: ModelIndex = QModelIndex()) -> int:
        return len(self._logs)

    def columnCount(self, parent: ModelIndex = QModelIndex()) -> int:
        return len(self.columns_)

    def index(
        self, row: int, column: int = 0, parent: ModelIndex = QModelIndex()
    ) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        return self.createIndex(row, column, self._logs[row])

    def roleNames(self):
        return {
            Qt.ItemDataRole.UserRole + 1: b"time",
            Qt.ItemDataRole.UserRole + 2: b"name",
            Qt.ItemDataRole.UserRole + 3: b"level",
            Qt.ItemDataRole.DisplayRole: b"message",
        }

    def flags(self, index: ModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return self.columns_[section]

    def data(self, index: ModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            log = self._logs[index.row()]
            return log["message"]
        elif role in self.roles.values():
            log = self._logs[index.row()]
            if role == Qt.ItemDataRole.UserRole + 1:
                return log["time"]
            elif role == Qt.ItemDataRole.UserRole + 2:
                return log["name"]
            elif role == Qt.ItemDataRole.UserRole + 3:
                return log["level"]
            else:
                return log["message"]
        return None

    def addLog(self, log: dict):
        if not isinstance(log, dict):
            raise ValueError("Log must be a dictionary")
        if (
            "time" not in log
            or "name" not in log
            or "level" not in log
            or "message" not in log
        ):
            raise ValueError(
                "Log must contain 'time', 'name', 'level', and 'message' keys"
            )
        self.beginInsertRows(QModelIndex(), len(self._logs), len(self._logs))
        self._logs.append(log)
        self.endInsertRows()
        return True

    def removeLog(self, log: dict):
        if not isinstance(log, dict):
            raise ValueError("Log must be a dictionary")
        if log not in self._logs:
            return False
        index = self._logs.index(log)
        self.beginRemoveRows(QModelIndex(), index, index)
        del self._logs[index]
        self.endRemoveRows()
        return True

    def removeAllLogs(self):
        self.beginResetModel()
        self._logs.clear()
        self.endResetModel()
        return True


class NotifyingLogModel(LogHistoryModel):
    """
    A model that stores logs that should be notified to the user.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def addLog(self, log: dict):
        if log["args"].get("customMessage", False):
            log["message"] = log["args"]["customMessage"]
            log["name"] = ""
        return super().addLog(log)


class JSONFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat(timespec="milliseconds") + "Z"

    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts": self.formatTime(record, datefmt="%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "thread": record.threadName,
        }
        skip = {
            "msg",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
        }
        for k, v in record.__dict__.items():
            if k not in base and k not in skip:
                try:
                    json.dumps(v)
                    base[k] = v
                except TypeError:
                    base[k] = repr(v)
        return json.dumps(base, ensure_ascii=False)


class MyHandler(logging.Handler):
    myBridge: typing.Union["LoggingBridge", None] = None

    def emit(self, record):
        formatted = self.format(record)
        completeHistory.append(formatted)
        if MyHandler.myBridge:
            MyHandler.myBridge.addLog(
                formatted, record.args if isinstance(record.args, dict) else None
            )


class LoggingBridge(QObject):
    logAdded = Signal(dict)
    notifyingLogAdded = Signal(dict)
    notifyingLogExpired = Signal(dict)
    logRemoved = Signal(dict)
    logHistoryChanged = Signal()
    # Signal to safely request log removal from the main thread
    _requestNotifyingLogRemoval = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.historyModel = LogHistoryModel()
        self.handler = MyHandler()
        MyHandler.myBridge = self
        self.handler.setLevel(logging.DEBUG)
        # inherit root JSON formatter
        if logging.getLogger().handlers:
            self.handler.setFormatter(JSONFormatter())
        logging.root.addHandler(self.handler)

        self.notifyingModel = (
            NotifyingLogModel()
        )  # A log model that will store pressing notifications. Each log will automatically delete itself after a certain time.
        self.notifyingLevel = (
            logging.ERROR
        )  # The level at which logs will be added to the notifying model.

        # --- Thread-based expiration handling ---
        self._expiration_queue: queue.Queue = queue.Queue()
        self._requestNotifyingLogRemoval.connect(self.notifyingLogExipry)

        self._expiration_thread = threading.Thread(
            target=self._process_expirations, daemon=True
        )
        self._expiration_thread.start()

    def addLog(self, log: str, args: typing.Optional[dict] = None):
        """Accepts a JSON formatted log string (preferred) or legacy plain string."""
        log_dict: dict
        if log.startswith("{"):
            try:
                parsed = json.loads(log)
                log_dict = {
                    "time": parsed.get("ts", ""),
                    "name": parsed.get("logger", ""),
                    "level": parsed.get("level", ""),
                    "message": parsed.get("msg", ""),
                    "args": args if isinstance(args, dict) else {},
                }
            except Exception:
                parts = log.split(" - ")
                log_dict = {
                    "time": parts[0] if len(parts) > 0 else "",
                    "name": parts[1] if len(parts) > 1 else "",
                    "level": parts[2] if len(parts) > 2 else "",
                    "message": (
                        " - ".join(parts[3:]).strip().replace("\n", " ")
                        if len(parts) > 3
                        else ""
                    ),
                    "args": args if isinstance(args, dict) else {},
                }
        else:
            parts = log.split(" - ")
            log_dict = {
                "time": parts[0] if len(parts) > 0 else "",
                "name": parts[1] if len(parts) > 1 else "",
                "level": parts[2] if len(parts) > 2 else "",
                "message": (
                    " - ".join(parts[3:]).strip().replace("\n", " ")
                    if len(parts) > 3
                    else ""
                ),
                "args": args if isinstance(args, dict) else {},
            }
        self.historyModel.addLog(log_dict)
        # Emit structured dict (keeping previous signal type but now dict already)
        self.logAdded.emit(log_dict)
        self.logHistoryChanged.emit()
        notifying = log_dict.get("args", {"notifying": False}).get("notifying", False)
        if (
            logging._nameToLevel.get(log_dict["level"], 0) >= self.notifyingLevel
            and notifying is not False
        ) or notifying is True:
            self.notifyingModel.addLog(log_dict)
            self.notifyingLogAdded.emit(log_dict)
            timeToRemoveInSeconds = 10
            # Add the log and its expiration time to the queue for the worker thread
            self._expiration_queue.put((time.time() + timeToRemoveInSeconds, log_dict))

    def _process_expirations(self):
        """
        Worker thread target. Runs forever, processing log expirations.
        This method runs in a background thread.
        """
        while True:
            # Block until a log is available in the queue
            expiry_time, log_dict = self._expiration_queue.get()

            # Sleep until it's time to remove the log
            sleep_duration = expiry_time - time.time()
            if sleep_duration > 0:
                time.sleep(sleep_duration)

            # Emit a signal to have the main thread perform the GUI update
            self._requestNotifyingLogRemoval.emit(log_dict)

    @Slot(dict)
    def notifyingLogExipry(self, log: dict):
        if self.notifyingModel.removeLog(log):
            self.notifyingLogExpired.emit(log)

    def removeLog(self, log: str):
        log_dict = {
            "time": log.split(" - ")[0],
            "name": log.split(" - ")[1],
            "level": log.split(" - ")[2],
            "message": " - ".join(log.split(" - ")[3:]).strip().replace("\n", " "),
        }
        if self.historyModel.removeLog(log_dict):
            self.logRemoved.emit(log)
            self.logHistoryChanged.emit()
        else:
            logging.warning(f"Log not found in history: {log}")

    def clearHistory(self):
        self.historyModel.removeAllLogs()
        self.logHistoryChanged.emit()


bridge = LoggingBridge()
