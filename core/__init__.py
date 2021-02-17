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


class nested_dict_sqlite(defaultdict):
    'like defaultdict but default_factory receives the key'

    def __missing__(self, key):
        self[key] = value = self.default_factory(key)
        return value

    def close(self):
        for key in self.keys():
            self[key].close()
        self.clear()


db_name = filetools.join(config.get_data_path(), "db.sqlite")
db = nested_dict_sqlite(lambda table: SqliteDict(db_name, table, 'c', True))
