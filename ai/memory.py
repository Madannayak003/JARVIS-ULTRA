"""
JARVIS ULTRA
Memory Database Manager

Responsibilities
----------------
✓ Database connection
✓ Table creation
✓ Schema migration
✓ Connection helper

This file DOES NOT perform:
    remember()
    recall()
    search()
"""

import sqlite3
import threading
from pathlib import Path

DB = Path(__file__).parent / "memory.db"
MEMORY_DB_LOCK = threading.RLock()


# * ---------------------------------------
# * Connection
# * ---------------------------------------

def connect():

    conn = sqlite3.connect(DB, timeout=10, check_same_thread=False)

    conn.row_factory = sqlite3.Row

    return conn


# * ---------------------------------------
# * Initialize Database
# * ---------------------------------------

def init_memory():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY_DB_LOCK:
        conn = connect()
        cursor = conn.cursor()

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS memories(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            key TEXT UNIQUE,

            value TEXT,

            category TEXT,

            keywords TEXT,

            importance INTEGER DEFAULT 2,

            created_at TEXT,

            updated_at TEXT,

            last_used TEXT,

            use_count INTEGER DEFAULT 0

        )

        """)

        conn.commit()

        conn.close()


# * ---------------------------------------
# * Future Schema Migration
# * ---------------------------------------

def migrate():

    """
    Future database upgrades happen here.

    Example:

        Add new column

        Rename table

        Convert data

    """

    pass
