import sqlite3
import logging
from pathlib import Path

from queries import Queries

log = logging.getLogger(__name__)

SCHEMA = "sql/schema.sql"
SQL_DIR = "sql/queries"

class Database:
    def __init__(self, path: str):
        self._conn = sqlite3.connect(path)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = NORMAL")
        self._q = Queries(SQL_DIR)

    def init_schema(self):
        self._conn.executescript(Path(SCHEMA).read_text())
        self._conn.commit()
        log.info("Database initialized")

    def __getattr__(self, name: str):
        fn = getattr(self._q, name)
        return lambda **params: fn(self._conn, **params)
