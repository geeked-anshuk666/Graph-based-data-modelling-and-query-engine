import sqlite3
import threading

from config import settings

_local = threading.local()


def get_db() -> sqlite3.Connection:
    """one connection per thread, reused across requests"""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(settings.db_path, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn
