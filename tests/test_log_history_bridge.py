import logging
import threading
import time

import pytest
from PySide6.QtCore import QCoreApplication

from src.misc.logHistoryManager import LoggingBridge, MyHandler

ERROR_LINE = (
    '{"ts": "12:00:00", "level": "ERROR", "logger": "Clarity.test", "msg": "boom"}'
)


@pytest.fixture
def bridge():
    QCoreApplication.instance() or QCoreApplication([])
    previous = MyHandler.myBridge
    b = LoggingBridge()
    # The tests drive addLog() directly; detach from root logging so unrelated
    # log calls elsewhere in the suite cannot land rows in the model.
    logging.root.removeHandler(b.handler)
    yield b
    MyHandler.myBridge = previous


def _pump(predicate, timeout=5.0):
    deadline = time.time() + timeout
    while not predicate() and time.time() < deadline:
        QCoreApplication.processEvents()
    return predicate()


def test_log_from_a_worker_thread_is_applied_on_the_owning_thread(bridge):
    """A QAbstractListModel may only be mutated by the thread that owns it.

    Logging happens on whatever thread called logger.x(), so addLog() has to
    marshal rather than mutate inline.
    """
    # Record the thread that actually performs the insert, rather than the one a
    # signal is delivered on -- those are not the same thing.
    appliedOn: list[int] = []
    insert = bridge.historyModel.addLog

    def recordingInsert(log):
        appliedOn.append(threading.get_ident())
        return insert(log)

    bridge.historyModel.addLog = recordingInsert

    worker = threading.Thread(target=bridge.addLog, args=(ERROR_LINE,))
    worker.start()
    worker.join()

    # The worker has finished and the model is still untouched: the append was
    # queued for this thread, not run on the worker.
    assert appliedOn == []
    assert bridge.historyModel.rowCount() == 0

    assert _pump(lambda: bridge.historyModel.rowCount() == 1)
    assert appliedOn == [threading.get_ident()]


def test_log_from_the_owning_thread_is_applied_synchronously(bridge):
    bridge.addLog(ERROR_LINE)

    assert bridge.historyModel.rowCount() == 1


def test_notification_is_opt_in_not_level_based(bridge):
    """Pins current behaviour, which background-work.md section 5 plans to invert.

    A plain logger.error() does not reach the UI today -- only calls that pass
    {"notifying": True} do. When surfacing goes default-on this should fail.
    """
    assert bridge._shouldNotify(bridge._parseLog(ERROR_LINE)) is False
    assert (
        bridge._shouldNotify(bridge._parseLog(ERROR_LINE, {"notifying": True})) is True
    )


def test_notifying_false_suppresses_an_error(bridge):
    assert (
        bridge._shouldNotify(bridge._parseLog(ERROR_LINE, {"notifying": False}))
        is False
    )


def test_dismiss_removes_the_clicked_row(bridge):
    for msg in ("first", "second"):
        line = ERROR_LINE.replace('"boom"', f'"{msg}"')
        bridge._appendLog(bridge._parseLog(line, {"notifying": True}))

    assert bridge.notifyingModel.rowCount() == 2
    assert bridge.notifyingModel.dismiss(0) is True
    assert bridge.notifyingModel.rowCount() == 1
    assert bridge.notifyingModel.dismiss(5) is False
