# -*- coding: utf-8 -*-

import os
import sys

# Appends the main plugin dir to the PYTHONPATH if an internal package cannot be imported.
# Examples: In Plex Media Server all modules are under "Code.*" package, and in Enigma2 under "Plugins.Extensions.*"
try:
    import core
except:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Connect to database
from . import filetools
from platformcode import config
from collections import defaultdict
from lib.sqlitedict import SqliteDict
import zlib, pickle, sqlite3


class nested_dict_sqlite(defaultdict):
    'like defaultdict but default_factory receives the key'

    def __missing__(self, key):
        self[key] = value = self.default_factory(key)
        return value

    def close(self):
        for key in self.keys():
            self[key].close()
        self.clear()

def encode(obj):
    return sqlite3.Binary(zlib.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)))

def decode(obj):
    return pickle.loads(zlib.decompress(bytes(obj)))

db_name = filetools.join(config.getDataPath(), "db.sqlite")
vdb_name = filetools.join(config.getVideolibraryPath(), "videolibrary.sqlite")

db = nested_dict_sqlite(lambda table: SqliteDict(db_name, table, 'c', True))
videolibrarydb = nested_dict_sqlite(lambda table: SqliteDict(vdb_name, table, 'c', True, encode=encode, decode=decode))


if 'played_time' not in SqliteDict.get_tablenames(vdb_name):
    for k, v in dict(db['viewed']).items():
        videolibrarydb['played_time'][k] = v
