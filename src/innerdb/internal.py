import sqlite3
import os
import json
import threading
import time

DB_PATH = os.path.join(os.path.abspath("data"), "innerdb.db")
DB = sqlite3.connect(DB_PATH)


class Schema:
    def __init__(self, name, columns):
        self.name = name
        self.columns = columns

    def create(self):
        DB.execute(
            f"CREATE TABLE IF NOT EXISTS {self.name} ({', '.join(self.columns)})"
        )
        DB.commit()

    def drop(self):
        DB.execute(f"DROP TABLE IF EXISTS {self.name}")
        DB.commit()

    def insert(self, **kwargs):
        DB.execute(
            f"INSERT INTO {self.name} ({', '.join(kwargs.keys())}) VALUES ({', '.join([f'"{i}"' for i in kwargs.values()])})"
        )
        DB.commit()

    def select(self, *columns, where=None):
        if where:
            DB.execute(f"SELECT {', '.join(columns)} FROM {self.name} WHERE {where}")
        else:
            DB.execute(f"SELECT {', '.join(columns)} FROM {self.name}")
        return DB.cursor().fetchall()

    def update(self, where, **kwargs):
        DB.execute(
            f"UPDATE {self.name} SET {', '.join([f'{k}="{v}"' for k, v in kwargs.items()])} WHERE {where}"
        )
        DB.commit()

    def delete(self, where):
        DB.execute(f"DELETE FROM {self.name} WHERE {where}")
        DB.commit()
