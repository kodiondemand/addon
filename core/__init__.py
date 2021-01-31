# -*- coding: utf-8 -*-

import os
import sys

# Appends the main plugin dir to the PYTHONPATH if an internal package cannot be imported.
# Examples: In Plex Media Server all modules are under "Code.*" package, and in Enigma2 under "Plugins.Extensions.*"
try:
    # from core import logger
    import core
except:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Connect to database
from . import filetools
from platformcode import config
import sqlite3, threading

db_name = filetools.join(config.get_data_path(), "kod_db.sqlite")
db_semaphore = threading.Semaphore()


class safeConn(sqlite3.Connection):
    """thread-safe sqlite3.Connection"""
    def commit(self):
        db_semaphore.acquire()
        try:
            super(safeConn, self).commit()
        finally:
            db_semaphore.release()


class safeCur(sqlite3.Cursor):
    """thread-safe sqlite3.Cursor"""
    def execute(self, *args, **kwargs):
        db_semaphore.acquire()
        try:
            super(safeCur, self).execute(*args, **kwargs)
        finally:
            db_semaphore.release()

    def executescript(self, *args, **kwargs):
        db_semaphore.acquire()
        try:
            super(safeCur, self).executescript(*args, **kwargs)
        finally:
            db_semaphore.release()

    def executemany(self, *args, **kwargs):
        db_semaphore.acquire()
        try:
            super(safeCur, self).executemany(*args, **kwargs)
        finally:
            db_semaphore.release()


db_conn = sqlite3.connect(db_name, factory=safeConn, timeout=15, check_same_thread=False)
db = db_conn.cursor(safeCur)

# Create tables if not already exists
db.execute('CREATE TABLE IF NOT EXISTS tmdb_cache (url TEXT PRIMARY KEY, response TEXT, added TEXT);')
db.execute('CREATE TABLE IF NOT EXISTS viewed (tmdb_id TEXT PRIMARY KEY, season INT, episode INT, played_time REAL);')
db.execute('CREATE TABLE IF NOT EXISTS dnscache(domain TEXT NOT NULL UNIQUE, ip	TEXT NOT NULL, PRIMARY KEY(domain));')
db_conn.commit()
