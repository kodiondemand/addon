from collections import defaultdict
from lib.sqlitedict import SqliteDict

from core import filetools
from platformcode import config

class nested_dict_sqlite(defaultdict):
    'like defaultdict but default_factory receives the key'

    def __missing__(self, key):
        self[key] = value = self.default_factory(key)
        return value

    def close(self):
        for key in self.keys():
            self[key].close()
        self.clear()

db_name = filetools.join(config.get_videolibrary_path(), "videolibrary.sqlite")
videolibrarydb = nested_dict_sqlite(lambda table: SqliteDict(db_name, table, 'c', True))