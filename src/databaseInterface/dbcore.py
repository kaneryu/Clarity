import sqlite3 as sq
import time
import os
from typing import Optional
import threading

from src.providerInterface.globalModels import (
    NamespacedIdentifier,
    NamespacedTypedIdentifier,
    SimpleIdentifier,
)

from src.paths import Paths
from src.misc import compiled
import src.misc.cleanup as cleanup_module


def initializeDatabase():
    os.makedirs(os.path.join(Paths.DATAPATH, "database"), exist_ok=True)
    os.makedirs(os.path.join(Paths.ASSETSPATH, "database"), exist_ok=True)
    pooledCursor = createDatabaseCursor()
    with pooledCursor as cursor:
        if not compiled.compiled:
            with open("src/databaseInterface/schema.sql", "r") as f:
                cursor.executescript(f.read())
        else:
            with open(
                os.path.join(Paths.ASSETSPATH, "database", "schema.sql"), "r"
            ) as f:
                cursor.executescript(f.read())


class PooledCursor:
    def __init__(self, cursor, connection):
        self.homeThread = threading.get_ident()
        self.cursor = cursor
        self.connection = connection

    def __enter__(self):
        if threading.get_ident() != self.homeThread:
            raise RuntimeError(
                "PooledCursor used from a different thread than it was created in."
            )
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        if threading.get_ident() != self.homeThread:
            raise RuntimeError(
                "PooledCursor used from a different thread than it was created in."
            )
        if exc_type is not None:
            self.connection.rollback()
        else:
            self.connection.commit()


def createDatabaseCursor():
    conn = sq.connect(os.path.join(Paths.DATAPATH, "database", "data"))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA cache_size = 10000;")
    return PooledCursor(conn.cursor(), conn)


class ConnectionPool:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionPool, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.main_thread_id = threading.main_thread().ident
        self.connections = []
        self.max_connections = 5

    def get_cursor(self):
        """Get a PooledCursor for the current thread.

        For main thread: returns from pool or creates new one
        For other threads: creates temporary connection
        """
        current_thread_id = threading.get_ident()

        if current_thread_id == self.main_thread_id:
            # Main thread: use pool
            if self.connections:
                return self.connections.pop(), True  # (cursor, should_return)
            else:
                return createDatabaseCursor(), True
        else:
            # Non-main thread: create temporary connection
            return createDatabaseCursor(), False  # Don't return to pool

    def return_cursor(self, pooled_cursor, should_return):
        """Return a PooledCursor to the pool or close it.

        Args:
            pooled_cursor: The PooledCursor to return
            should_return: Whether to return to pool (False for non-main threads)
        """
        if should_return:
            if len(self.connections) < self.max_connections:
                self.connections.append(pooled_cursor)
            else:
                pooled_cursor.connection.close()
        else:
            # Non-main thread: close the connection
            pooled_cursor.connection.close()

    def cleanup(self):
        """Close all connections in the pool. Should be called at application exit."""
        for pooled_cursor in self.connections:
            pooled_cursor.connection.close()
        self.connections.clear()


class DatabaseInterface:
    def __init__(self):
        self.pool = ConnectionPool()
        cleanup_module.addCleanup(self.pool.cleanup)

    def cleanup(self):
        """runs at application exit"""
        self.pool.cleanup()

    def _fixIdsInParams(self, params):
        return tuple(
            (
                str(i)
                if isinstance(
                    i,
                    (NamespacedIdentifier, NamespacedTypedIdentifier, SimpleIdentifier),
                )
                else i
            )
            for i in params
        )

    def query(self, sql, params=()) -> list:
        pooled_cursor, should_return = self.pool.get_cursor()
        try:
            with pooled_cursor as cursor:
                cursor.execute(sql, self._fixIdsInParams(params))
                return cursor.fetchall()
        finally:
            self.pool.return_cursor(pooled_cursor, should_return)

    def execute(self, sql, params=()) -> int:
        pooled_cursor, should_return = self.pool.get_cursor()
        try:
            with pooled_cursor as cursor:
                cursor.execute(sql, self._fixIdsInParams(params))
                return cursor.rowcount
        finally:
            self.pool.return_cursor(pooled_cursor, should_return)

    def execute_returning_id(self, sql, params=()) -> Optional[int]:
        pooled_cursor, should_return = self.pool.get_cursor()
        try:
            with pooled_cursor as cursor:
                cursor.execute(sql, self._fixIdsInParams(params))
                return cursor.lastrowid
        finally:
            self.pool.return_cursor(pooled_cursor, should_return)


if __name__ == "__main__":
    initializeDatabase()
